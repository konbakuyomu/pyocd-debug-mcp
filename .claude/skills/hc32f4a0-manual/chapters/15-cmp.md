# CMP — 电压比较器

> ✅ 本知识卡已填充。最后更新：2026-03-25

## 模块概述

HC32F4A0 内置 4 通道电压比较器（CMP1~4），可独立进行模拟电压比较（普通模式），或 CMP1+2 / CMP3+4 组合实现窗口比较。每通道正端和负端均有多路输入源可选（外部引脚、DAC 输出、PGA 输出等）。支持数字噪声滤波、定时器 PWM 窗口输出控制、外部管脚输出（VCOUT）、中断及外设触发事件，并可唤醒停止模式。

## 关键特性

- 4 个独立比较通道 CMP1~4
- 普通比较模式：单通道独立比较，CMON 位实时反映结果
- 窗口比较模式：CMP1+2 或 CMP3+4 组合，检测输入是否在上下限之间
- 正端输入可选：外部引脚（INP2/3/4）、PGA 输出、PGA 旁路
- 负端输入可选：DAC 输出（DA1O1/DA1O2/DA2O1/DA2O2）、外部引脚（INM3/INM4）
- 数字噪声滤波器：采样时钟可选 PCLK / PCLK÷8 / PCLK÷32，3 次采样一致后输出
- 定时器窗口输出：用 Timer6/TimerA/Timer4 的 PWM 信号控制 CMP 输出开关
- 比较结果可输出到外部引脚 VCOUT1~4 / VCOUT
- 中断：边沿检测（上升/下降/双沿），可唤醒停止低功耗模式
- 外设触发事件：与中断条件相同但独立，可触发其他外设

## 功能导航大纲

> 小节编号对应原始手册 `15-CMP-电压比较器.md` 中的标题。

| 区域 | 小节 | 关键内容 |
|------|------|----------|
| 概述 | 16.1 | 主要特性列表 |
| 框图 | 16.2 | 功能框图、引脚列表 |
| **普通比较模式** | 16.3.1 | 设定步骤（8 步）、CMON 结果监视 |
| **窗口比较模式** | 16.3.2 | CMP1+2 或 CMP3+4 组合、CMP2/4 控制输出 |
| 定时器窗口输出 | 16.3.3 | TWOE/TWOL 控制、定时器 PWM 窗口映射表 |
| 数字滤波器 | 16.3.4 | FCKS 采样时钟选择、3 次采样一致 |
| **中断** | 16.3.5 | CIEN + EDGS 边沿选择、唤醒停止模式 |
| 外设触发事件 | 16.3.6 | 与中断条件相同但独立于 CIEN |
| 外部管脚输出 | 16.3.7 | CPOE/COPS 控制 VCOUT |
| 注意事项 | 16.4 | 模块停止、低功耗行为 |
| 寄存器 | 16.5 | MDR/FIR/OCR/PMSR/TWSR/TWPR/VISR |

## 寄存器速查

> CMP1: 0x4004A000, CMP2: 0x4004A010, CMP3: 0x4004A400, CMP4: 0x4004A410

| 寄存器 | 偏移 | 宽度 | 用途 | 关键位字段 |
|--------|------|------|------|-----------|
| **CMPx_MDR** | 0x00 | 8 | 模式设定 | CENB[0] 使能, CWDE[1] 窗口模式(仅 CMP2/4), **CMON[7]** 结果监视 |
| **CMPx_FIR** | 0x01 | 8 | 滤波和中断 | FCKS[1:0] 滤波时钟, EDGS[5:4] 边沿检测, CIEN[6] 中断使能 |
| CMPx_OCR | 0x02 | 8 | 输出控制 | COEN[0] 输出使能, COPS[1] 极性, CPOE[2] VCOUT 使能, TWOE[3] 窗口输出, TWOL[4] 窗口禁止时电平 |
| **CMPx_PMSR** | 0x03 | 8 | 正负端选择 | RVSL[3:0] 负端, CVSL[7:4] 正端 |
| CMPx_TWSR | 0x04 | 16 | 定时器窗口选择 | CTWS[15:0] 每 bit 对应一路定时器 PWM |
| CMPx_TWPR | 0x06 | 16 | 定时器窗口极性 | CTWP[15:0] 0=低电平允许输出, 1=高电平允许输出 |
| CMPx_VISR | 0x08 | 16 | 电压输入源(仅 CMP1/3) | P2SL[2:0] INP2 源选择, P3SL[5:4] INP3 源选择 |

## 典型初始化流程

```c
/* === 普通比较模式 + 中断 === */
// 1. 使能 CMP 偏置时钟 + CMP 模块时钟
FCG_Fcg3PeriphClockCmd(FCG3_PERIPH_CMBIAS, ENABLE);
FCG_Fcg3PeriphClockCmd(FCG3_PERIPH_CMP12, ENABLE);  // 或 FCG3_PERIPH_CMP34

// 2. 配置模拟输入引脚
stc_gpio_init_t stcGpioInit;
(void)GPIO_StructInit(&stcGpioInit);
stcGpioInit.u16PinAttr = PIN_ATTR_ANALOG;
(void)GPIO_Init(CMP1_INP4_PORT, CMP1_INP4_PIN, &stcGpioInit);
(void)GPIO_Init(CMP1_INM4_PORT, CMP1_INM4_PIN, &stcGpioInit);
GPIO_SetFunc(VCOUT1_PORT, VCOUT1_PIN, GPIO_FUNC_1);  // VCOUT 输出引脚

// 3. 初始化 CMP
stc_cmp_init_t stcCmpInit;
(void)CMP_StructInit(&stcCmpInit);
stcCmpInit.u16PositiveInput = CMP1_POSITIVE_CMP1_INP4;
stcCmpInit.u16NegativeInput = CMP_NEGATIVE_INM4;
stcCmpInit.u16OutPolarity   = CMP_OUT_INVT_OFF;
stcCmpInit.u16OutDetectEdge = CMP_DETECT_EDGS_BOTH;
stcCmpInit.u16OutFilter     = CMP_OUT_FILTER_CLK_DIV32;
(void)CMP_NormalModeInit(CM_CMP1, &stcCmpInit);

// 4. 使能中断 + 输出
CMP_IntCmd(CM_CMP1, ENABLE);
CMP_CompareOutCmd(CM_CMP1, ENABLE);
CMP_PinVcoutCmd(CM_CMP1, ENABLE);

// 5. NVIC 配置
// INT_SRC: INT_SRC_CMP1
```

## 常见陷阱与注意事项

1. ⚠️ **CMBIAS 时钟必须先使能**：FCG3_PERIPH_CMBIAS 写 0 后需等待至少 2μs，再使能 CMP 模块
2. ⚠️ **CENB 置 1 后等 300ns**：每次启动比较器后需等待工作稳定时间 ~300ns 才能使用结果
3. ⚠️ **修改 CVSL/RVSL/COPS/FCKS 前须关输出**：先设 COEN=0，改完后等 300ns 再 COEN=1
4. ⚠️ **修改寄存器可能产生伪中断**：改 EDGS/COPS/CVSL/RVSL/FCKS 时先禁中断(CIEN=0)，改完后清中断标志
5. ⚠️ **窗口模式由 CMP2/4 控制输出**：窗口模式下滤波、边沿检测、中断和输出均由 CMP2 或 CMP4 完成
6. ⚠️ **CMP1/3 的 INP2/INP3 需额外配 VISR**：通过 CMPx_VISR 的 P2SL/P3SL 选择具体电压源
7. ⚠️ **模块停止≠省电**：CMP 进入模块停止后比较器仍工作，需 CENB=0 才能真正降低功耗
8. ⚠️ **唤醒停止模式须关滤波**：CIEN=1 + FCKS=00 + EDGS=00 时，输出低→高产生中断可唤醒 Stop 模式

## 官方例程索引

| 例程名 | 绝对路径 | 用途简述 |
|--------|---------|---------|
| cmp_normal_int | `$EXAMPLES\cmp\cmp_normal_int` | 普通比较模式 + 中断：CMP1 外部引脚比较，双沿中断 |
| cmp_normal_blankwindow | `$EXAMPLES\cmp\cmp_normal_blankwindow` | 普通比较 + 定时器窗口输出：Timer6 PWM 控制 CMP 输出开关 |
| cmp_window | `$EXAMPLES\cmp\cmp_window` | 窗口比较模式：CMP3+4 组合，DAC 提供上下限电压 |

> `$EXAMPLES` = `D:\Dev\SDKs\HC32\HC32F4A0\HC32F4A0_DDL_Rev2.4.0\projects\ev_hc32f4a0_lqfp176\examples`

## 相关应用笔记

| 笔记名 | 路径 | 关键内容 |
|--------|------|----------|
| 电压比较器 CMP 应用笔记 | `$MANUAL\AN_HC32F4A0系列的电压比较器CMP__Rev1.1` | CMP 使用详解、窗口比较配置、定时器窗口联动 |

> `$MANUAL` = `D:\Library\10_Datasheets\11_MCU\HC32系列\HC32F4A0`

## 源文件引用

- **手册 Markdown**: `D:\Library\10_Datasheets\11_MCU\HC32系列\HC32F4A0\15-CMP-电压比较器\15-CMP-电压比较器.md`
- **手册 PDF**: `D:\Library\10_Datasheets\11_MCU\HC32系列\HC32F4A0\RM_HC32F4A0系列参考手册_Rev1.40.pdf`
