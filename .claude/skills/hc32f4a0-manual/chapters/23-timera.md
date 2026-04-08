# TimerA — 通用定时器 A

> ✅ 本知识卡已填充。最后更新：2026-03-25

## 模块概述

HC32F4A0 内置 12 个独立 TimerA 单元（U1~U12），每单元为 16 位计数器，4 路 PWM 输出通道，共可实现最多 48 路 PWM。支持锯齿波/三角波两种计数模式，4 路独立比较输出或捕获输入，比较值支持成对缓冲传递（CMPAR2→1, CMPAR4→3），支持正交编码器接口（2 相位置计数、3 相公转计数）、对称单元间级联 32 位计数、软件/硬件同步启动、硬件触发启停清零等功能。U1~U4 时钟源为 PCLK0，U5~U12 时钟源为 PCLK1。

## 关键特性

- 12 个独立单元 × 4 通道 = 最多 48 路 PWM 输出
- 16 位计数器，锯齿波（递加/递减）+ 三角波（中心对齐）
- 4 个比较基准值寄存器（CMPAR1~4），成对缓冲（2→1, 4→3）
- 捕获输入：PWM 端口边沿 / TRIG 端口边沿 / TRGSEL 内部事件
- 正交编码：基本计数、相位差计数（1x/2x/4x）、方向计数、Z 相/位置溢出/混合公转计数
- 级联计数：对称单元溢出事件作为硬件计数源，两单元合并为 32 位
- 同步启动：偶数单元可与奇数单元同步（软件或硬件触发）
- 硬件触发：启动/停止/清零各 3 类条件（TRIG 端口 + 对称单元 + 内部事件）
- 数字滤波：CLKA/CLKB/TRIG/PWM(捕获) 端口独立滤波，采样基准 PCLK/1/4/16/64
- 中断：比较匹配×4（或逻辑汇总为 1 路）+ 上溢 + 下溢；事件输出同理
- 计数时钟：PCLK / 2 / 4 / 8 / ... / 1024（11 档分频）或硬件计数源
- U1~U4 时钟为 PCLK0；U5~U12 时钟为 PCLK1

## 功能导航大纲

> 小节编号对应原始手册 `23-TimerA-通用定时器.md` 中的 24.x 标题。

| 区域 | 小节 | 关键内容 |
|------|------|----------|
| 概述 | 24.1-24.2 | 简介、基本框图、端口列表 |
| **波形模式** | 24.3.1 | 锯齿波（递加/递减）、三角波 |
| 时钟源 | 24.3.2 | 软件计数（PCLK 分频）vs 硬件计数（TRIG/编码/级联/事件） |
| **比较输出** | 24.3.3 | 4 通道独立比较匹配 → 端口电平控制 |
| **捕获输入** | 24.3.4 | CAPMD=1，边沿捕获计数值存入 CMPARn |
| 同步启动 | 24.3.5 | 偶数单元 SYNST=1 → 与奇数单元同步 |
| 数字滤波 | 24.3.6 | FCONR/CCONRn 控制滤波时钟和使能 |
| **缓存功能** | 24.3.7 | CMPAR2→1, CMPAR4→3，峰/谷时刻传递 |
| 级联计数 | 24.3.8 | 对称单元溢出驱动本单元，合并 32 位 |
| **PWM 输出** | 24.3.9 | 单边对齐 / 双边对称 / 独立 / 互补 |
| **正交编码** | 24.3.10 | 位置计数（基本/相差/方向）+ 公转计数（Z 相/溢出/混合） |
| 中断与事件 | 24.4 | 比较匹配×4(或汇总) + OVF + UDF |
| 寄存器 | 24.5 | 25 个寄存器 + 4 个全局 TRGSEL |

## 寄存器速查

> U1: 0x4003A000, U2: 0x4003A400, U3: 0x4003A800, U4: 0x4003AC00; U5: 0x40026000, ..., U12: 0x40027C00

| 寄存器 | 偏移 | 用途 | 关键位字段 |
|--------|------|------|-----------|
| TMRA_CNTER | 0x000 | 计数值 | CNT[15:0] |
| TMRA_PERAR | 0x004 | 周期基准值 | PER[15:0] |
| **TMRA_CMPARn** | 0x040+4*(n-1) | 比较基准值 1~4 | CMP[15:0] |
| **TMRA_BCSTRL** | 0x080 | 控制状态 L | **START[0]** DIR[1] MODE[2] SYNST[3] **CKDIV[7:4]** |
| TMRA_BCSTRH | 0x081 | 控制状态 H | OVSTP[0] ITENOVF[4] ITENUDF[5] OVFF[6] UDFF[7] |
| TMRA_HCONR | 0x088 | 硬件触发事件 | HSTA[2:0] HSTP[6:4] HCLE[15:8] |
| TMRA_HCUPR | 0x088 | 硬件递加条件 | HCUP[12:0] — 编码/TRIG/事件/级联 |
| TMRA_HCDOR | 0x08C | 硬件递减条件 | HCDO[12:0] — 同上 |
| TMRA_ICONR | 0x090 | 中断控制 | ITEN1~4 |
| TMRA_ECONR | 0x094 | 事件控制 | ETEN1~4 |
| TMRA_FCONR | 0x098 | 滤波控制 | NOFIENTG/CA/CB + 时钟选择 |
| TMRA_STFLR | 0x09C | 状态标志 | CMPF1~4 |
| TMRA_BCONRm | 0x0C0/0C8 | 缓存控制 1/2 | BEN BSE0 BSE1 |
| **TMRA_CCONRn** | 0x100+4*(n-1) | 捕获控制 1~4 | CAPMD[0] HICP[9:4] NOFIENCP[12] |
| **TMRA_PCONRn** | 0x140+4*(n-1) | 端口控制 1~4 | STAC STPC CMPC PERC FORC **OUTEN[12]** |

## 典型初始化流程

```c
/* === TimerA PWM 输出（锯齿波单边对齐） === */
// 1. 使能时钟
FCG_Fcg2PeriphClockCmd(FCG2_PERIPH_TMRA_1, ENABLE);

// 2. 配置 GPIO 复用
GPIO_SetFunc(GPIO_PORT_E, GPIO_PIN_09, GPIO_FUNC_4); // TIMA_1_PWM1

// 3. 基本计数配置
stc_tmra_init_t stcInit;
TMRA_StructInit(&stcInit);
stcInit.sw_count.u8ClockDiv = TMRA_CLK_DIV8;
stcInit.sw_count.u8CountMode = TMRA_MD_SAWTOOTH;
stcInit.sw_count.u8CountDir  = TMRA_DIR_UP;
stcInit.u32PeriodValue = 50000UL - 1UL;  // 周期值
TMRA_Init(CM_TMRA_1, &stcInit);

// 4. PWM 通道配置
stc_tmra_pwm_init_t stcPwm;
TMRA_PWM_StructInit(&stcPwm);
stcPwm.u32CompareValue = 25000UL;  // 50% 占空比
TMRA_PWM_Init(CM_TMRA_1, TMRA_CH1, &stcPwm);
TMRA_PWM_OutputCmd(CM_TMRA_1, TMRA_CH1, ENABLE);

// 5. 中断（可选）
TMRA_IntCmd(CM_TMRA_1, TMRA_INT_OVF, ENABLE);
// ... INTC_IrqSignIn + NVIC 配置 ...

// 6. 启动
TMRA_Start(CM_TMRA_1);
```

## 常见陷阱与注意事项

1. ⚠️ **U1~U4 vs U5~U12 时钟不同**：U1~U4 使用 PCLK0，U5~U12 使用 PCLK1，系统时钟配置变更会影响两组产生不同频率
2. ⚠️ **同步启动仅偶数→奇数**：只有偶数单元（2/4/6/...）可同步到其对称奇数单元（1/3/5/...），反之无效
3. ⚠️ **STAC 位仅 CKDIV=0 时有效**：PCONR.STAC（计数开始时端口状态）只在不分频时生效，有分频时应设为保持（10 或 11）
4. ⚠️ **三角波模式运行中不可写 BCSTRL**：会导致不可预期行为
5. ⚠️ **4 路比较匹配中断汇总为 1 路**：每单元的 CMPF1~4 通过或逻辑输出单一中断，回调中需手动判 STFLR 区分通道
6. ⚠️ **缓冲是成对的**：CMPAR2→CMPAR1，CMPAR4→CMPAR3，不能任意通道间缓冲
7. ⚠️ **TRGSEL 寄存器全局共享**：4 个 TMRA_TRGSEL0~3 被 12 个单元共享，不同单元的计数触发和捕获触发使用不同 TRGSEL（参照手册表 24-4 映射）
8. ⚠️ **三角波模式需初始化计数值为 1**：`TMRA_SetCountValue(UNIT, 1UL)`，否则第一个周期的波形不正确
9. ⚠️ **硬件计数模式下 CKDIV 无效**：选择 CLKA/CLKB/TRIG/级联作为计数源时，软件分频自动无效
10. ⚠️ **正交编码 4 倍计数**：需同时使能 HCUPR[7:4] 和 HCDOR[7:4] 的所有 4 位边沿条件

## 官方例程索引

| 例程名 | 绝对路径 | 用途简述 |
|--------|---------|---------:|
| timera_base_timer | `$EXAMPLES\timera\timera_base_timer` | 基本定时器：锯齿波/三角波 + OVF/UDF 中断 |
| timera_pwm | `$EXAMPLES\timera\timera_pwm` | PWM 输出：单通道/单边对齐/双边对称 |
| timera_capture | `$EXAMPLES\timera\timera_capture` | 输入捕获：PWM/TRIG/EVT 边沿捕获 |
| timera_cascade_count | `$EXAMPLES\timera\timera_cascade_count` | 级联计数：对称单元合并 32 位 |
| timera_compare_value_buffer | `$EXAMPLES\timera\timera_compare_value_buffer` | 比较值缓冲传递：峰/谷时刻自动更新 |
| timera_phase_difference_count | `$EXAMPLES\timera\timera_phase_difference_count` | 正交编码相差计数（X1/X2/X4） |
| timera_position_overflow_count | `$EXAMPLES\timera\timera_position_overflow_count` | 位置溢出计数：POS 溢出驱动 Z 单元 |
| timera_pulse_encoder_z_count | `$EXAMPLES\timera\timera_pulse_encoder_z_count` | Z 相脉冲编码器：TRIG 计圈 + POS 清零 |

> `$EXAMPLES` = `D:\Dev\SDKs\HC32\HC32F4A0\HC32F4A0_DDL_Rev2.4.0\projects\ev_hc32f4a0_lqfp176\examples`

## 相关应用笔记

| AN 名称 | 路径 |
|---------|------|
| 通用定时器 TIMERA 操作说明 | `$MANUAL\AN_HC32F4A0系列的通用定时器TIMERA__Rev1.1\` |
| 三相正交编码器操作说明及注意事项 | `$MANUAL\AN_HC32F4A0_F448系列的三相正交编码器操作说明及注意事项_Rev1.0\` |

## 源文件引用

- **手册 Markdown**: `D:\Library\10_Datasheets\11_MCU\HC32系列\HC32F4A0\23-TimerA-通用定时器\23-TimerA-通用定时器.md`
- **手册 PDF**: `D:\Library\10_Datasheets\11_MCU\HC32系列\HC32F4A0\RM_HC32F4A0系列参考手册_Rev1.40.pdf`
