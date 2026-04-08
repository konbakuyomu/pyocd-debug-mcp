# KEYSCAN — 键盘扫描控制模块

> ✅ 本知识卡已填充。最后更新：2026-03-25

## 模块概述

HC32F4A0 搭载 1 个 KEYSCAN 单元，用于驱动键盘矩阵的行列扫描。列由 KEYOUT0~KEYOUT7（最多 8 路）循环输出低电平驱动，行由 KEYIN0~KEYIN15（复用 EIRQ0~EIRQ15）检测下降沿中断。模块采用逐列扫描 + 中断定位方式识别按键，最大支持 16 行 × 8 列 = 128 键矩阵。

## 关键特性

- 最大支持 16 行（KEYIN0~15，复用 EIRQ0~15）× 8 列（KEYOUT0~7）
- 行输入通过 SCR.KEYINSEL[15:0] 逐位独立选择
- 列输出通过 SCR.KEYOUTSEL[2:0] 选择使用的 KEYOUT 管脚数量（2~8 列）
- 扫描时钟源可选：HCLK / LRC / XTAL32
- 列输出低电平时间可配置：2^T_LLEVEL 个扫描时钟周期（T_LLEVEL: 2~24）
- 列间 Hi-Z 时间可配置：4 / 8 / 16 / 32 / 64 / 256 / 512 / 1024 个时钟周期
- 按键按下时扫描自动停止，通过 SSR.INDEX[2:0] + INT_EIFR 定位行列坐标
- 支持 STOP 模式下使用（需选择 LRC 或 XTAL32 作为扫描时钟）

## 功能导航大纲

| 区域 | 小节 | 关键内容 |
|------|------|----------|
| 简介 | 13.1 | 模块概述，1 个 KEYSCAN 单元 |
| 系统框图 | 13.2 | KEYOUT 列驱动 + KEYIN/EIRQ 行检测拓扑 |
| 管脚说明 | 13.3 | KEYINn(n:0~15) 输入 / KEYOUTm(m:0~7) 输出 |
| 按键识别 | 13.4.1 | 行列短接产生 EIRQ 下降沿，INDEX + EIFR 定位 |
| 键盘扫描 | 13.4.2 | 逐列输出低电平，其余 Hi-Z，循环扫描时序 |
| 注意事项 | 13.4.3 | EIRQ 下降沿 + 数字滤波；STOP 模式时钟选择 |
| SCR 寄存器 | 13.5.1 | 时钟源、行选择、列选择、低电平/Hi-Z 时间 |
| SER 寄存器 | 13.5.2 | 扫描使能位 SEN |
| SSR 寄存器 | 13.5.3 | 当前扫描列索引 INDEX[2:0]（只读） |

## 寄存器速查

> BASE_ADDR: 0x40050C00

| 寄存器 | 偏移 | 用途 | 关键位字段 |
|--------|------|------|-----------|
| KEYSCAN_SCR | 0x00 | 扫描控制 | T_HIZ[2:0](b31~29), T_LLEVEL[4:0](b28~24), CKSEL[1:0](b21~20), KEYOUTSEL[2:0](b18~16), KEYINSEL[15:0](b15~0) |
| KEYSCAN_SER | 0x04 | 扫描使能 | SEN(b0) 0=禁止 1=使能 |
| KEYSCAN_SSR | 0x08 | 扫描状态 | INDEX[2:0](b2~0) 当前工作 KEYOUT 索引（只读） |

## 典型初始化流程

```c
/* === 键盘矩阵扫描（3行×3列示例） === */
/* 1. 开启 KEYSCAN 外设时钟 */
FCG_Fcg0PeriphClockCmd(FCG0_PERIPH_KEY, ENABLE);

/* 2. 配置 KEYIN 管脚为 EIRQ 功能 */
GPIO_SetFunc(GPIO_PORT_A, GPIO_PIN_00, GPIO_FUNC_14);  /* KEYIN0/EIRQ0 */
GPIO_SetFunc(GPIO_PORT_A, GPIO_PIN_01, GPIO_FUNC_14);  /* KEYIN1/EIRQ1 */

/* 3. 配置 KEYOUT 管脚 */
GPIO_SetFunc(GPIO_PORT_A, GPIO_PIN_04, GPIO_FUNC_8);   /* KEYOUT0 */
GPIO_SetFunc(GPIO_PORT_A, GPIO_PIN_05, GPIO_FUNC_8);   /* KEYOUT1 */
GPIO_SetFunc(GPIO_PORT_A, GPIO_PIN_06, GPIO_FUNC_8);   /* KEYOUT2 */

/* 4. 配置 KEYSCAN 参数（SEN=0 时才能写 SCR） */
stc_keyscan_init_t stcKeyscanInit;
(void)KEYSCAN_StructInit(&stcKeyscanInit);
stcKeyscanInit.u32HizCycle  = KEYSCAN_HIZ_CYCLE_512;
stcKeyscanInit.u32LowCycle  = KEYSCAN_LOW_CYCLE_512;
stcKeyscanInit.u32KeyClock  = KEYSCAN_CLK_HCLK;
stcKeyscanInit.u32KeyOut    = KEYSCAN_OUT_0T2;
stcKeyscanInit.u32KeyIn     = (KEYSCAN_IN_0 | KEYSCAN_IN_1 | KEYSCAN_IN_2);
(void)KEYSCAN_Init(&stcKeyscanInit);

/* 5. 配置 EIRQ 下降沿检测 + 数字滤波 */
stc_extint_init_t stcExtIntInit;
(void)EXTINT_StructInit(&stcExtIntInit);
stcExtIntInit.u32Edge       = EXTINT_TRIG_FALLING;
stcExtIntInit.u32Filter     = EXTINT_FILTER_ON;
stcExtIntInit.u32FilterClock = EXTINT_FCLK_DIV8;
(void)EXTINT_Init(EXTINT_CH00, &stcExtIntInit);

/* 6. 注册 EIRQ 中断 + NVIC */
/* 7. 启动扫描 */
KEYSCAN_Cmd(ENABLE);
```

## 常见陷阱与注意事项

1. ⚠️ **SCR 仅在 SEN=0 时可写**：修改扫描参数前必须先 `KEYSCAN_Cmd(DISABLE)`
2. ⚠️ **T_LLEVEL 禁止设为 0 或 1**：最大允许值为 24（2^24 个时钟周期）
3. ⚠️ **行检测依赖 INTC/EIRQ**：KEYSCAN 本身不产生中断，必须同步配置 EXTINT 下降沿 + 滤波
4. ⚠️ **STOP 模式必须用低速时钟**：须将 CKSEL 切换为 LRC 或 XTAL32
5. ⚠️ **内部上拉电阻影响时序**：使用芯片内部上拉需确保扫描低电平时间足够长
6. ⚠️ **按键释放后才恢复扫描**：检测到 EIRQ 后扫描自动停止，需清除 EIRQ 标志后才重启
7. ⚠️ **SSR.INDEX 仅 SEN=1 时有意义**

## 官方例程索引

| 例程名 | 绝对路径 | 用途简述 |
|--------|---------|---------|
| keyscan_base | `$EXAMPLES\keyscan\keyscan_base` | 基本键盘矩阵扫描，KEYSCAN + EIRQ 联合配置 |

> `$EXAMPLES` = `D:\Dev\SDKs\HC32\HC32F4A0\HC32F4A0_DDL_Rev2.4.0\projects\ev_hc32f4a0_lqfp176\examples`

## 相关应用笔记

暂无专属应用笔记。

## 源文件引用

- **手册 Markdown**: `D:\Library\10_Datasheets\11_MCU\HC32系列\HC32F4A0\12-KEYSCAN-键盘扫描控制模块\12-KEYSCAN-键盘扫描控制模块.md`
- **手册 PDF**: `D:\Library\10_Datasheets\11_MCU\HC32系列\HC32F4A0\RM_HC32F4A0系列参考手册_Rev1.40.pdf`
