# Timer0 — 通用定时器 0

> ✅ 本知识卡已填充。最后更新：2026-03-25

## 模块概述

Timer0 是一个基本定时器，支持同步/异步两种计数方式。HC32F4A0 搭载 2 个独立单元（Timer0_1/2），每单元含 2 通道（CH-A/CH-B）。同步模式使用 PCLK1（可分频 ÷1~1024）或内部硬件触发事件作为计数时钟；异步模式使用 LRC 或 XTAL32（各可分频 ÷1~1024）。每通道支持比较输出和捕获输入功能，并可通过内部硬件触发实现启动/停止/清零/捕获控制。异步模式下 Timer0_1 CH-A 的比较匹配中断可唤醒低功耗模式。Timer0 与 USART 模块有硬件联动：当 USART TIMEOUT 功能使能时，硬件触发事件和 XTAL32 时钟源均由 USART 模块提供。

## 关键特性

- 2 个独立单元，每单元 2 通道（CH-A/CH-B），共 4 通道
- 16 位向上计数器（CNTAR/CNTBR），计数至 0xFFFF 时溢出
- 同步计数时钟源：PCLK1（÷1~1024）、内部硬件触发事件
- 异步计数时钟源：LRC（÷1~1024）、XTAL32（÷1~1024）
- 比较输出功能：CNT == CMP 时产生比较匹配事件
- 捕获输入功能：内部硬件触发事件将 CNT 值捕获到 CMP 寄存器
- 硬件触发：启动（HSTA）、停止（HSTP）、清零（HCLE）、捕获（HICP）四种条件独立可选
- 硬件触发源由 AOS 模块的 TMR0_TRGSEL 寄存器选择，两通道共用一个触发源
- 中断：比较匹配/捕获中断，每单元 2 个中断源
- 事件输出：比较匹配/捕获事件可触发其他外设
- 异步模式唤醒：Timer0_1 CH-A 的比较匹配中断可唤醒低功耗
- USART 联动：USART TIMEOUT 使能时，硬件触发和 XTAL32 时钟源由 USART 提供

## 功能导航大纲

> 小节编号对应原始手册 `25-Timer0-通用定时器.md` 中的标题。

| 区域 | 小节 | 关键内容 |
|------|------|----------|
| 概述 | 26.1-26.2 | 简介、基本框图 |
| **时钟源** | 26.3.1 | 同步（PCLK1/硬件事件）、异步（LRC/XTAL32）计数方式 |
| 基本计数 | 26.3.2 | CNT == CMP 时产生比较匹配事件 |
| **硬件触发** | 26.3.3 | 启动/停止/清零/捕获 4 种硬件触发、AOS 事件源选择 |
| **中断/事件** | 26.4 | 比较匹配/捕获中断、事件输出 |
| 寄存器 | 26.5 | CNTAR/CNTBR/CMPAR/CMPBR/BCONR/STFLR |
| **注意事项** | 26.6 | 异步写操作延迟、ASYNCLK 设定顺序、CST/SYNSA 不可同时改写 |

## 寄存器速查

> U1: 0x40024000, U2: 0x40024400

| 寄存器 | 偏移 | 宽度 | 用途 | 关键位字段 |
|--------|------|------|------|-----------|
| TMR0_CNTAR | 0x00 | 32 | 通道 A 计数值 | CNTA[15:0] |
| TMR0_CNTBR | 0x04 | 32 | 通道 B 计数值 | CNTB[15:0] |
| TMR0_CMPAR | 0x08 | 32 | 通道 A 基准值 | CMPA[15:0]（比较/捕获） |
| TMR0_CMPBR | 0x0C | 32 | 通道 B 基准值 | CMPB[15:0] |
| **TMR0_BCONR** | 0x10 | 32 | 基本控制 | CSTA[0]/CSTB[16] 启动, CAPMDA[1]/B[17] 功能模式, INTENA[2]/B[18] 中断使能, CKDIVA[7:4]/B[23:20] 分频, SYNSA[8]/B[24] 同步/异步, SYNCLKA[9]/B[25] 同步时钟, ASYNCLKA[10]/B[26] 异步时钟, HSTAA[12]/B[28] 硬件启动, HSTPA[13]/B[29] 硬件停止, HCLEA[14]/B[30] 硬件清零, HICPA[15]/B[31] 硬件捕获 |
| TMR0_STFLR | 0x14 | 32 | 状态标志 | CMAF[0] 匹配标志 A, CMBF[16] 匹配标志 B |

## 典型初始化流程

```c
/* === 异步计数 + 比较匹配中断（XTAL32 时钟源）=== */
// 1. 使能 Timer0 和 AOS 时钟
LL_PERIPH_WE(LL_PERIPH_GPIO | LL_PERIPH_FCG | LL_PERIPH_PWC_CLK_RMU);
FCG_Fcg2PeriphClockCmd(FCG2_PERIPH_TMR0_1, ENABLE);
FCG_Fcg0PeriphClockCmd(FCG0_PERIPH_AOS, ENABLE);

// 2. 初始化 Timer0（异步 XTAL32 时钟）
stc_tmr0_init_t stcTmr0Init;
(void)TMR0_StructInit(&stcTmr0Init);
stcTmr0Init.u32ClockSrc     = TMR0_CLK_SRC_XTAL32;
stcTmr0Init.u32ClockDiv     = TMR0_CLK_DIV4;
stcTmr0Init.u32Func         = TMR0_FUNC_CMP;
stcTmr0Init.u16CompareValue = cmpValue;
(void)TMR0_Init(CM_TMR0_1, TMR0_CH_B, &stcTmr0Init);

// ⚠️ 异步时钟：每次写 TMR0 寄存器后须等待 ≥6 个异步时钟周期
DDL_DelayMS(1U);

// 3. 配置硬件触发（可选）
TMR0_HWStopCondCmd(CM_TMR0_1, TMR0_CH_B, ENABLE);
DDL_DelayMS(1U);

// 4. 使能中断
TMR0_IntCmd(CM_TMR0_1, TMR0_INT_CMP_B, ENABLE);
DDL_DelayMS(1U);
// NVIC: INT_SRC_TMR0_1_CMP_B

// 5. 配置触发事件源
AOS_SetTriggerEventSrc(AOS_TMR0, EVT_SRC_xxx);

// 6. 启动
TMR0_Start(CM_TMR0_1, TMR0_CH_B);
DDL_DelayMS(1U);
```

## 常见陷阱与注意事项

1. ⚠️ **异步写操作须延迟 6 个异步时钟**：异步计数模式下，连续写 CNTR/CMPR/CSTA/STFLR 之间须间隔至少 6 个异步时钟周期，否则写入无效
2. ⚠️ **异步模式设定顺序**：必须先设 ASYNCLKA/B 选择异步时钟源，再设 SYNSA/B=1 选择异步模式，最后启动定时器
3. ⚠️ **CSTA 与 SYNSA 不可同时改写**：对 BCONR.CSTA 写入时，不能同时改写 BCONR.SYNSA
4. ⚠️ **异步模式下 SYNCLK 须为 0**：选择异步计数时，须将 SYNCLKA/B 设定为 0
5. ⚠️ **异步模式寄存器读不可靠**：异步计数方式下计数器状态可能正在变化，须在停止状态下读寄存器
6. ⚠️ **硬件停止自动清 CST**：硬件触发停止条件有效时，BCONR.CSTA/B 会自动变为 0
7. ⚠️ **USART TIMEOUT 联动**：当 USART TIMEOUT 功能使能时，硬件触发事件和 XTAL32 时钟源均由 USART 模块接管，可不需要实际 XTAL32 晶振
8. ⚠️ **使用硬件触发须使能 AOS 时钟**：FCG0_PERIPH_AOS 必须在使用硬件触发前使能

## 官方例程索引

| 例程名 | 绝对路径 | 用途简述 |
|--------|---------|---------|
| timer0_basetimer | `$EXAMPLES\timer0\timer0_basetimer` | 基本定时：异步 XTAL32 计数 + 比较匹配中断，硬件触发停止 |
| timer0_capture | `$EXAMPLES\timer0\timer0_capture` | 捕获输入：内部硬件事件触发捕获 |

> `$EXAMPLES` = `D:\Dev\SDKs\HC32\HC32F4A0\HC32F4A0_DDL_Rev2.4.0\projects\ev_hc32f4a0_lqfp176\examples`

## 相关应用笔记

（未找到独立的 Timer0 应用笔记）

## 源文件引用

- **手册 Markdown**: `D:\Library\10_Datasheets\11_MCU\HC32系列\HC32F4A0\25-Timer0-通用定时器\25-Timer0-通用定时器.md`
- **手册 PDF**: `D:\Library\10_Datasheets\11_MCU\HC32系列\HC32F4A0\RM_HC32F4A0系列参考手册_Rev1.40.pdf`
