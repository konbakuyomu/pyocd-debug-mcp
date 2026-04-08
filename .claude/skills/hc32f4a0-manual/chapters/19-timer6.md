# Timer6 — 高级控制定时器

> ✅ 本知识卡已填充。最后更新：2026-03-25

## 模块概述

HC32F4A0 内置 8 个独立 Timer6 单元（U1~U4 为 32 位计数器，U5~U8 为 16 位计数器）。Timer6 是面向电机控制和工业驱动的高级定时器，支持锯齿波/三角波两种计数模式，提供 6 路通用比较（GCMA~F）+ 2 路专用比较（SCMA~B）+ 3 路周期（PERA~C）寄存器，内建单/双缓冲传递链、硬件死区插入、正交编码器接口、EMB 紧急刹车联动、硬件事件触发（启动/停止/清零/捕获/计数）、软件同步控制（8 单元同步启停清零）及有效周期滤波等功能。每单元输出 PWMA/PWMB 两路互补或独立 PWM。

## 关键特性

- 8 个独立单元：U1~U4（32-bit）、U5~U8（16-bit）；共 16 路 PWM 输出
- 计数模式：锯齿波（单向递增/递减）、三角波（中心对齐，A/B 两种模式）
- 6 个通用比较寄存器（GCMA~F）：支持单/双缓冲链（C→A / E→C→A）
- 3 个周期寄存器（PERA~C）：支持单/双缓冲链（B→A / C→B→A）
- 2 个专用比较寄存器（SCMA~B）：独立缓冲链，可联动 ADC/DMA 触发
- 硬件死区：DTUAR/DTDAR 独立设置上升/下降沿死区，支持缓冲传递
- 正交编码器：支持 2 相（AB 相）和 3 相（AB+Z 相），Z 相屏蔽功能
- 硬件事件系统：启动/停止/清零/刷新/捕获/递加/递减共 7 类条件可独立绑定
- 软件同步控制：SSTAR/SSTPR/SCLRR/SUPDR 全局寄存器一次操作多个单元
- 有效周期：每 N 个计数周期产生一次特殊比较匹配事件
- 输入数字滤波：PWMA/PWMB/TRIGA/TRIGB 四路独立滤波
- EMB 联动：检测到故障时自动将 PWM 输出置为安全状态
- 中断：比较匹配×6 + 专用比较×4 + 上溢 + 下溢 + 死区错误 = 共 13 种
- 计数时钟：PCLK0 / 2 / 4 / 8 / ... / 1024（11 档分频）

## 功能导航大纲

> 小节编号对应原始手册 `19-Timer6-高级控制定时器.md` 中的 20.x 标题。

| 区域 | 小节 | 关键内容 |
|------|------|----------|
| 概述 | 20.1-20.2 | 简介、结构框图 |
| **波形模式** | 20.3.1-20.3.2 | 锯齿波（单向计数）、三角波（中心对齐） |
| 时钟与计数 | 20.3.3-20.3.4 | PCLK0 分频（CKDIV[3:0]）、内部/硬件计数源 |
| **比较输出** | 20.3.5-20.3.6 | 6 路 GCMA~F 在不同计数状态时的端口动作 |
| 捕获输入 | 20.3.7 | GCMA/GCMB 捕获 + 缓冲传送 |
| 刷新功能 | 20.3.8 | 将 UPDAR 值加载到计数器 |
| **同步控制** | 20.3.9-20.3.10 | 软件同步（SSTAR/SSTPR/SCLRR）、硬件同步启动 |
| 脉宽/周期测量 | 20.3.11 | 捕获两次匹配值之差 |
| **缓存传送** | 20.3.12 | 单/双缓冲链（周期、比较、死区三类均支持） |
| 数字滤波 | 20.3.13 | FCNGR/FCNTR 控制 PWMA/B/TRIGA/B 滤波时钟 |
| **PWM 输出** | 20.3.14 | 单路独立 / 互补软件死区 / 互补硬件死区 / 动态占空比 |
| 有效周期 | 20.3.15 | VPERR 控制每 N 周期触发一次特殊比较 |
| **正交编码** | 20.3.16 | 2 相位置计数 + 3 相公转计数 + Z 相屏蔽 |
| EMB 联动 | 20.3.17.15 | 端口保护状态设定 + 恢复时间点 |
| 中断与事件 | 20.4 | 比较/周期/死区错误中断 + AOS 事件输出 |
| 寄存器 | 20.5 | 约 40 个寄存器（含全局同步寄存器和共用滤波寄存器） |

## 寄存器速查

> U1: 0x40018000, U2: 0x40018400, U3: 0x40018800, U4: 0x40018C00, U5: 0x40019000, U6: 0x40019400, U7: 0x40019800, U8: 0x40019C00

| 寄存器 | 偏移 | 用途 | 关键位字段 |
|--------|------|------|-----------|
| TMR6_CNTER | 0x000 | 计数值 | CNT[15:0]（U1~4 为 32bit） |
| TMR6_UPDAR | 0x004 | 刷新值 | UPDA[15:0] |
| TMR6_PERAR/BR/CR | 0x040/044/048 | 周期基准值 A/B/C | 双缓冲链 C→B→A |
| **TMR6_GCMmR** | 0x080~094 | 通用比较 A~F | 双缓冲链 E→C→A, F→D→B |
| TMR6_SCMmR | 0x0C0~0D4 | 专用比较 A~F | 独立缓冲链 |
| TMR6_DTU/DAR | 0x100/104 | 死区基准值（上升/下降） | 缓冲 UB→UA, DB→DA |
| **TMR6_GCONR** | 0x140 | **通用控制**（核心） | **START[0]** MODE[2] DIR[1] **CKDIV[7:4]** OVSTP[8] ZMSK*[19:16] |
| TMR6_ICONR | 0x144 | 中断控制 | INTENA~F INTENOVF INTENUDF INTENDTE |
| TMR6_BCONR | 0x148 | 缓存控制 | BENA/B BSEA/B BENP BSEP BENSPA/B 等 |
| TMR6_DCONR | 0x14C | 死区控制 | DTCEN[0] SEPA[1] DTBENU/D[4:5] |
| **TMR6_PCNAR** | 0x154 | 端口控制 A | OUTENA CAPMDA STACA OVFCA CMAx 极性 EMBCA |
| TMR6_PCNBR | 0x158 | 端口控制 B | OUTENB CAPMDB 同上 B 通道 |
| TMR6_FCNGR | 0x15C | 滤波控制（单元级） | PWMA/B 滤波时钟分频 |
| TMR6_VPERR | 0x160 | 有效周期 | PCNTE[31:29] PCNTS[27:26] |
| TMR6_STFLR | 0x164 | 状态标志 | CMAF~F OVFF UDFF DTEF 等 |
| TMR6_HSTAR | 0x180 | 硬件启动条件 | HSTAx (x=0~31) + STAS |
| TMR6_HSTPR | 0x184 | 硬件停止条件 | HSTOx + STPS |
| TMR6_HCLRR | 0x188 | 硬件清零条件 | HCLRx + CLES |
| TMR6_HCPAR/HCPBR | 0x190/194 | 硬件捕获条件 A/B | 边沿选择 |
| TMR6_HCUPR/HCDOR | 0x198/19C | 硬件递加/递减条件 | 正交编码输入选择 |
| TMR6_SSTAR | U1+0x3F0 | 同步启动（全局） | 8 单元一键同步启动 |
| TMR6_SSTPR | U1+0x3F4 | 同步停止（全局） | 8 单元一键同步停止 |
| TMR6_FCNTR | U1+0x3EC | 滤波控制（全局） | TRIGA/B 全局滤波时钟 |

## 典型初始化流程

```c
/* === Timer6 锯齿波 PWM 比较输出 === */
// 1. 使能时钟
FCG_Fcg2PeriphClockCmd(FCG2_PERIPH_TMR6_1, ENABLE);

// 2. 配置 GPIO 复用
GPIO_SetFunc(GPIO_PORT_B, GPIO_PIN_09, GPIO_FUNC_3); // TIM6_1_PWMA
GPIO_SetFunc(GPIO_PORT_B, GPIO_PIN_08, GPIO_FUNC_3); // TIM6_1_PWMB

// 3. 基本计数配置
stc_tmr6_init_t stcInit;
TMR6_StructInit(&stcInit);
stcInit.sw_count.u32ClockDiv = TMR6_CLK_DIV1024;
stcInit.u32PeriodValue = HCLK_VALUE / 1024U / 4U;  // 周期
TMR6_Init(CM_TMR6_1, &stcInit);

// 4. PWM 输出配置（每通道独立设置各状态极性）
stc_tmr6_pwm_init_t stcPwm;
TMR6_PWM_StructInit(&stcPwm);
stcPwm.u32CompareValue = 0x3000U;
stcPwm.u32CountUpMatchAPolarity   = TMR6_PWM_HIGH;
stcPwm.u32CountDownMatchAPolarity = TMR6_PWM_LOW;
stcPwm.u32OvfPolarity  = TMR6_PWM_LOW;
stcPwm.u32StartPolarity = TMR6_PWM_LOW;
stcPwm.u32StopPolarity  = TMR6_PWM_LOW;
TMR6_PWM_Init(CM_TMR6_1, TMR6_CH_A, &stcPwm);
TMR6_SetFunc(CM_TMR6_1, TMR6_CH_A, TMR6_PIN_CMP_OUTPUT);
TMR6_PWM_OutputCmd(CM_TMR6_1, TMR6_CH_A, ENABLE);

// 5. 中断（可选）
TMR6_IntCmd(CM_TMR6_1, TMR6_INT_OVF, ENABLE);
// ... INTC_IrqSignIn + NVIC 配置 ...

// 6. 启动
TMR6_Start(CM_TMR6_1);
```

## 常见陷阱与注意事项

1. ⚠️ **U1~U4 vs U5~U8 位宽不同**：U1~U4 的计数器和基准值寄存器为 32 位有效，U5~U8 仅 16 位。复位值也不同（U1~U4 基准值复位为 0xFFFFFFFF，U5~U8 为 0x0000FFFF）
2. ⚠️ **时钟源为 PCLK0**：不是 PCLK2，注意 CMU 时钟树配置对 Timer6 频率的影响
3. ⚠️ **硬件死区仅在三角波模式下生效**：锯齿波模式需用软件死区（GCMA≠GCMB）
4. ⚠️ **同步寄存器是全局的**：SSTAR/SSTPR/SCLRR/SUPDR 偏移在 U1 基址 + 0x3F0 处，被 8 个单元共享
5. ⚠️ **FCNTR 全局滤波寄存器**：偏移在 U1 基址 + 0x3EC，TRIGA/TRIGB 滤波配置全局共享
6. ⚠️ **比较输出 vs 捕获输入缓冲方向相反**：比较模式 C→A，捕获模式 A→C
7. ⚠️ **OVSTP=1 时溢出即停止**：计数器上溢/下溢后 START 自动清零，适用于单发脉冲
8. ⚠️ **正交编码 Z 相屏蔽需正确配置**：ZMSKVAL/ZMSKPOS/ZMSKREV 三个字段控制屏蔽周期、位置计数器和公转计数器行为
9. ⚠️ **有效周期仅对特殊比较有效**：VPERR 控制的是 SCMA/SCMB 的匹配事件生成频率，不影响 GCMA~F
10. ⚠️ **死区错误中断**：当 DTUAR + GCMAR > PERAR 时自动触发死区错误（DTEF），应在初始化时校验参数

## 官方例程索引

| 例程名 | 绝对路径 | 用途简述 |
|--------|---------|---------:|
| timer6_cmp_sawtooth | `$EXAMPLES\timer6\timer6_cmp_sawtooth` | 锯齿波 PWM 比较输出（CH_A + CH_B 独立占空比） |
| timer6_cmp_sawtooth_dual_buf | `$EXAMPLES\timer6\timer6_cmp_sawtooth_dual_buf` | 锯齿波 + 双缓冲（E→C→A 三级链）动态更新 |
| timer6_cmp_triangular_buf | `$EXAMPLES\timer6\timer6_cmp_triangular_buf` | 三角波 + 单缓冲比较输出 |
| timer6_cmp_deadtime | `$EXAMPLES\timer6\timer6_cmp_deadtime` | 互补 PWM + 硬件死区插入（三角波） |
| timer6_capture | `$EXAMPLES\timer6\timer6_capture` | 捕获输入 + 单/双缓冲比较寄存器 |
| timer6_capture_dual_buf | `$EXAMPLES\timer6\timer6_capture_dual_buf` | 捕获模式 + 双缓冲（A→C→E 三级历史） |
| timer6_sw_sync | `$EXAMPLES\timer6\timer6_sw_sync` | 软件同步启停清零所有 8 个单元 |
| timer6_hw_sta_stp_clr | `$EXAMPLES\timer6\timer6_hw_sta_stp_clr` | 硬件事件触发启动/停止/清零 |
| timer6_hw_code_cnt | `$EXAMPLES\timer6\timer6_hw_code_cnt` | AB 相正交编码器硬件计数 |
| timer6_pulse_encoder_z_count | `$EXAMPLES\timer6\timer6_pulse_encoder_z_count` | 脉冲编码器 Z 相计数（位置 + 公转） |
| timer6_define_pwm_number | `$EXAMPLES\timer6\timer6_define_pwm_number` | 指定 N 个 PWM 脉冲后硬件停止 |
| timer6_valid_period | `$EXAMPLES\timer6\timer6_valid_period` | 有效周期功能（每 N 周期触发 ADC） |
| timer6_pwm_dynamic_dutycycle | `$EXAMPLES\timer6\timer6_pwm_dynamic_dutycycle` | 动态修改占空比 + 0%/100% 边界处理 |

> `$EXAMPLES` = `D:\Dev\SDKs\HC32\HC32F4A0\HC32F4A0_DDL_Rev2.4.0\projects\ev_hc32f4a0_lqfp176\examples`

## 相关应用笔记

| AN 名称 | 路径 |
|---------|------|
| 三相正交编码器操作说明及注意事项 | `$MANUAL\AN_HC32F4A0_F448系列的三相正交编码器操作说明及注意事项_Rev1.0\` |

## 源文件引用

- **手册 Markdown**: `D:\Library\10_Datasheets\11_MCU\HC32系列\HC32F4A0\19-Timer6-高级控制定时器\19-Timer6-高级控制定时器.md`
- **手册 PDF**: `D:\Library\10_Datasheets\11_MCU\HC32系列\HC32F4A0\RM_HC32F4A0系列参考手册_Rev1.40.pdf`
