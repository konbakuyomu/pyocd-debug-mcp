# FMAC — 滤波数学加速器

> ✅ 本知识卡已填充。最后更新：2026-03-26

## 模块概述

FMAC（Filter Math Accelerator）是 FIR 数字滤波硬件加速模块。支持最大 16 阶、阶数可配置的 FIR 滤波，内置 16×16 位乘法器和 37 位加法器（32+5bit），用户可自定义输出精度。HC32F4A0 搭载 4 个独立 FMAC 模块（FMAC1~FMAC4）。在 150MHz 工作频率下，16 阶 FIR 可处理最大 8.8MHz 输入数据流。

## 关键特性

- **4 个独立模块**：FMAC1~FMAC4
- **最大 16 阶 FIR**：阶数通过 STAGE_NUM[4:0] 可配置
- **数据格式**：16 位有符号数输入/输出，16 位有符号数滤波系数
- **运算核心**：16×16 bit 乘法器 + 37 bit 加法器
- **输出精度**：SHIFT[4:0] 控制结果右移 0~21 位
- **处理速度**：16 阶需 17 个时钟周期/数据，阶数越小越快
- **中断/事件**：运算完成产生 FMAC_m_FIR 中断和事件（m=1~4）
- **软复位**：FIREN 清 0 清除内部状态，切换系数/阶数时需用

## 功能导航大纲

> 小节编号对应原始手册标题

| 区域 | 小节 | 关键内容 |
|------|------|----------|
| 简介 | 46.1 | FIR 滤波加速器功能总览 |
| 框图 | 46.2 | 16 阶 FIR 结构，17 时钟/数据 |
| 操作流程 | 46.3 | FIREN→配置阶数/移位→写系数→写数据→等完成→读结果 |
| 模块使能 | 46.4 | FIREN 兼做软复位 |
| 系数归一化 | 46.5 | 最大值归一化到 32767，保持精度 |
| 中断/事件 | 46.6 | FMAC_m_FIR 中断和事件输出 |
| 寄存器 | 46.7 | 寄存器详述 |

## 寄存器速查

> FMAC1: 0x40058000 | FMAC2: 0x40058400 | FMAC3: 0x40058800 | FMAC4: 0x40058C00

| 寄存器 | 偏移 | 用途 | 关键位字段 |
|--------|------|------|-----------:|
| FMAC_ENR | 0x00 | 模块使能 | FMACEN（使能/软复位） |
| FMAC_CTR | 0x04 | 控制 | STAGE_NUM[4:0]（阶数）, SHIFT[4:0]（结果右移） |
| FMAC_IER | 0x08 | 中断使能 | INTEN |
| FMAC_DTR | 0x0C | 数据输入 | FMAC_DIN[15:0] |
| FMAC_RTR0 | 0x10 | 结果输出 0 | 32 位完整结果 |
| FMAC_RTR1 | 0x14 | 结果输出 1 | SHIFT 后的结果 |
| FMAC_STR | 0x18 | 运算状态 | READY（运算完成标志） |
| FMAC_COR0~16 | 0x20~0x60 | 滤波系数 | FMAC_CIN[15:0]（N阶写 COR0~CORN） |

## 典型初始化流程

```c
/* 以 FMAC1 4 阶 FIR 滤波为例 */

/* 1. 使能时钟 */
FCG_Fcg0PeriphClockCmd(FCG0_PERIPH_FMAC1, ENABLE);

/* 2. 使能模块 */
FMAC_Cmd(CM_FMAC1, ENABLE);

/* 3. 配置阶数和移位 */
stc_fmac_init_t stcFmacInit;
stcFmacInit.u32Stage = 4U;     /* 4 阶 */
stcFmacInit.u32Shift = 0U;     /* 不移位 */
FMAC_Init(CM_FMAC1, &stcFmacInit);

/* 4. 写入滤波系数 COR0~COR4 */
int16_t as16Coeff[] = {3410, 4433, 11935, 32736, 14322};
FMAC_SetCoefficient(CM_FMAC1, as16Coeff, 5U);

/* 5. 写入数据并读取结果 */
FMAC_SetInputData(CM_FMAC1, i16Data);
while (FMAC_GetStatus(CM_FMAC1) != SET) {}  /* 等待 READY */
int32_t i32Result = FMAC_ReadResult(CM_FMAC1);
```

## 常见陷阱与注意事项

1. **切换阶数/系数须软复位**：修改阶数或系数前必须先将 FIREN 清 0 再置 1
2. **FIREN 清 0 不清配置**：只清除内部寄存器和中间结果，配置参数保留
3. **系数归一化**：建议将最大系数归一化到 32767（负数 -32768），避免精度损失
4. **输入数据太小结果为 0**：不归一化时，16 位截断可能丢失全部有效位
5. **16 阶 17 个时钟**：每个数据需 N+1 个时钟处理（N 为阶数）
6. **N 阶只需配 COR0~CORN**：不用配置多余的系数寄存器

## 官方例程索引

| 例程名 | 绝对路径 | 用途简述 |
|--------|---------|--------:|
| fmac_base | `$EXAMPLES\fmac\fmac_base` | FIR 滤波基础演示 |

> `$EXAMPLES` = `D:\Dev\SDKs\HC32\HC32F4A0\HC32F4A0_DDL_Rev2.4.0\projects\ev_hc32f4a0_lqfp176\examples`

## 相关应用笔记

暂无专属 FMAC 应用笔记。

## 源文件引用

- **手册 Markdown**: `D:\Library\10_Datasheets\11_MCU\HC32系列\HC32F4A0\45-FMAC-滤波数学加速器\45-FMAC-滤波数学加速器.md`
- **手册 PDF**: `D:\Library\10_Datasheets\11_MCU\HC32系列\HC32F4A0\RM_HC32F4A0系列参考手册_Rev1.40.pdf`
