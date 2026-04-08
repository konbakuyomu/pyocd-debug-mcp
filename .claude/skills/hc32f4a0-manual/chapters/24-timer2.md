# Timer2 — 通用定时器 2

> ✅ 本知识卡已填充。最后更新：2026-03-25

## 模块概述

Timer2 是一个基本定时器，支持同步/异步两种计数方式。HC32F4A0 搭载 4 个独立单元（Timer2_1~4），每单元含 2 通道（CH-A/CH-B）。同步模式使用 PCLK1 或其分频、TRIG 端口边沿、内部硬件事件、Timer6 溢出作为计数时钟；异步模式使用 LRC/XTAL32/外部 CLK 端口输入。每通道支持比较输出（方波）、捕获输入、脉宽/周期测量。TRIG 输入端口带数字滤波（3 次采样一致）和模拟滤波（40ns）。异步模式下 Timer2_1 的 CMPAR 比较匹配可唤醒低功耗模式。

## 关键特性

- 4 个独立单元，每单元 2 通道（CH-A/CH-B），共 8 通道
- 16 位向上计数器（CNTAR/CNTBR），计数至 0xFFFF 时溢出
- 同步计数时钟源：PCLK1（÷1~1024）、TRIG 端口边沿、内部硬件事件、Timer6 上/下溢
- 异步计数时钟源：LRC、XTAL32、TIM2_CLK 外部输入（均可 ÷1~1024）
- 比较输出功能：方波输出至 TIM2_PWM 端口，可配置启动/停止/匹配时电平
- 捕获输入功能：TRIG 端口/内部事件触发时，将 CNT 值捕获到 CMP 寄存器
- 硬件触发：启动、停止、清零、捕获四种硬件触发条件独立可选
- 脉宽测量：利用硬件启动+停止+清零+捕获组合实现
- 周期测量：利用硬件启动+清零+捕获组合实现
- 数字滤波：TRIG 端口输入滤波（采样时钟可选 ÷1/4/16/64）
- 中断：比较匹配/捕获中断 + 计数溢出中断，共 4 个中断源/单元
- 事件输出：比较匹配/捕获事件 + 溢出事件可触发其他外设
- 异步模式唤醒：Timer2_1 CH-A 的比较匹配中断可唤醒低功耗

## 功能导航大纲

> 小节编号对应原始手册 `24-Timer2-通用定时器.md` 中的标题。

| 区域 | 小节 | 关键内容 |
|------|------|----------|
| 概述 | 25.1-25.2 | 简介、基本框图、端口列表 |
| **时钟源** | 25.3.1 | 同步/异步计数方式、5 种同步时钟源、3 种异步时钟源 |
| 比较输出 | 25.3.2 | 方波输出、STACA/STPCA/CMPCA 端口电平控制 |
| **硬件触发** | 25.3.3 | 启动/停止/清零/捕获 4 种硬件触发、脉宽测量、周期测量 |
| 数字滤波 | 25.3.4 | TRIG 端口 3 次采样一致滤波 |
| **中断/事件** | 25.4 | 比较匹配/捕获中断、溢出中断、事件输出 |
| 寄存器 | 25.5 | CNTAR/CNTBR/CMPAR/CMPBR/BCONR/ICONR/PCONR/HCONR/STFLR |

## 寄存器速查

> U1: 0x40024800, U2: 0x40024C00, U3: 0x40025000, U4: 0x40025400

| 寄存器 | 偏移 | 宽度 | 用途 | 关键位字段 |
|--------|------|------|------|-----------|
| TMR2_CNTAR | 0x00 | 32 | 通道 A 计数值 | CNTA[15:0] |
| TMR2_CNTBR | 0x04 | 32 | 通道 B 计数值 | CNTB[15:0] |
| TMR2_CMPAR | 0x08 | 32 | 通道 A 基准值 | CMPA[15:0]（比较/捕获） |
| TMR2_CMPBR | 0x0C | 32 | 通道 B 基准值 | CMPB[15:0] |
| **TMR2_BCONR** | 0x10 | 32 | 基本控制 | CSTA[0]/CSTB[16] 启动, CAPMDA[1]/B[17] 功能模式, SYNSA[3]/B[19] 同步/异步, CKDIVA[7:4]/B[23:20] 分频, SYNCLKA[9:8]/B[25:24] 同步时钟, ASYNCLKA[11:10]/B[27:26] 异步时钟 |
| TMR2_ICONR | 0x14 | 32 | 中断控制 | CMENA[0]/B[16] 比较匹配中断, OVENA[1]/B[17] 溢出中断 |
| TMR2_PCONR | 0x18 | 32 | 端口控制 | STACA/STPCA/CMPCA 电平设定, OUTENA[8]/B[24] 输出使能, NOFIENA[12]/B[28] 滤波 |
| TMR2_HCONR | 0x1C | 32 | 硬件控制 | HSTAx0~2 启动条件, HSTPs 停止, HCLEx 清零, HICPx 捕获（各 3 个条件位） |
| TMR2_STFLR | 0x20 | 32 | 状态标志 | CMFA[0]/B[16] 匹配标志, OVFA[1]/B[17] 溢出标志 |

## 典型初始化流程

```c
/* === 基本定时器（比较匹配中断）=== */
// 1. 使能 Timer2 时钟
LL_PERIPH_WE(LL_PERIPH_GPIO | LL_PERIPH_FCG | LL_PERIPH_PWC_CLK_RMU);
FCG_Fcg2PeriphClockCmd(FCG2_PERIPH_TMR2_1, ENABLE);

// 2. 初始化 Timer2
stc_tmr2_init_t stcTmr2Init;
(void)TMR2_StructInit(&stcTmr2Init);
stcTmr2Init.u32ClockSrc     = TMR2_CLK_PCLK1;
stcTmr2Init.u32ClockDiv     = TMR2_CLK_DIV256;
stcTmr2Init.u32Func         = TMR2_FUNC_CMP;      // 比较输出模式
stcTmr2Init.u32CompareValue = cmpValue;
(void)TMR2_Init(CM_TMR2_1, TMR2_CH_A, &stcTmr2Init);

// 3. 使能中断
TMR2_IntCmd(CM_TMR2_1, TMR2_INT_CMP_A, ENABLE);
// NVIC: INT_SRC_TMR2_1_CMP_A

// 4. 启动
TMR2_Start(CM_TMR2_1, TMR2_CH_A);

/* === 捕获输入（脉宽测量）=== */
stcTmr2Init.u32Func = TMR2_FUNC_CAPT;
(void)TMR2_Init(CM_TMR2_1, TMR2_CH_A, &stcTmr2Init);
// 配置硬件触发条件
TMR2_HWTriggerCondCmd(CM_TMR2_1, TMR2_CH_A,
    TMR2_HW_TRIG_START_A_RISING | TMR2_HW_TRIG_STOP_A_FALLING |
    TMR2_HW_TRIG_CLR_A_FALLING | TMR2_HW_TRIG_CAPT_A_FALLING,
    ENABLE);
```

## 常见陷阱与注意事项

1. ⚠️ **异步模式下寄存器读不可靠**：异步计数方式时状态可能正在变化，寄存器读操作须在计数停止状态下进行
2. ⚠️ **异步模式唤醒限制**：仅 Timer2_1 CH-A 的 CMPAR 比较匹配可唤醒低功耗，且 ASYNCLKA≠10（外部 CLK 输入模式除外）
3. ⚠️ **STACA 启动电平仅不分频有效**：PCONR.STACA/STACB 的设定只在 CKDIV=0（不分频）时有效，其他分频须设为 10 或 11（保持）
4. ⚠️ **硬件停止自动清 CST**：硬件触发停止条件有效时，BCONR.CSTA/CSTB 位会自动变为 0
5. ⚠️ **Timer6 溢出作时钟源需 PCLK0=PCLK1**：选择 Timer6 上/下溢事件作为同步计数时钟源时，须设定 PCLK0 和 PCLK1 同频
6. ⚠️ **内部硬件触发需使能 AOS 时钟**：使用内部硬件触发功能前需通过 PWC_FCG0 使能外围电路触发功能

## 官方例程索引

| 例程名 | 绝对路径 | 用途简述 |
|--------|---------|---------|
| timer2_base_timer | `$EXAMPLES\timer2\timer2_base_timer` | 基本定时：PCLK1 计数 + 比较匹配中断，支持硬件触发启动 |
| timer2_capture | `$EXAMPLES\timer2\timer2_capture` | 捕获输入：TRIG 端口边沿触发捕获 |
| timer2_clock_source | `$EXAMPLES\timer2\timer2_clock_source` | 时钟源选择：演示同步/异步各种时钟源配置 |
| timer2_pwm | `$EXAMPLES\timer2\timer2_pwm` | 方波输出：PWM 端口输出方波 |

> `$EXAMPLES` = `D:\Dev\SDKs\HC32\HC32F4A0\HC32F4A0_DDL_Rev2.4.0\projects\ev_hc32f4a0_lqfp176\examples`

## 相关应用笔记

（未找到独立的 Timer2 应用笔记）

## 源文件引用

- **手册 Markdown**: `D:\Library\10_Datasheets\11_MCU\HC32系列\HC32F4A0\24-Timer2-通用定时器\24-Timer2-通用定时器.md`
- **手册 PDF**: `D:\Library\10_Datasheets\11_MCU\HC32系列\HC32F4A0\RM_HC32F4A0系列参考手册_Rev1.40.pdf`
