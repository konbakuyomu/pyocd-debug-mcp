# Timer4 — 通用控制定时器

> ✅ 本知识卡已填充。最后更新：2026-03-25

## 模块概述

Timer4 是专为三相电机控制设计的定时器模块，HC32F4A0 搭载 3 个独立单元（Timer4_1/2/3）。支持锯齿波和三角波两种计数模式，通过 3 组互补 PWM 输出端口（U/V/W 各含 OXH/OXL 两路）实现三相电机驱动。提供通用比较输出（OC）和专用比较事件输出（可触发 ADC 等外设），支持硬件死区定时器（含脉宽滤波模式）、周期间隔响应（中断屏蔽/缓存传输联动）、EMB 紧急刹车接口。所有比较寄存器和模式寄存器均带缓存功能，可在计数过程中同步更新。

## 关键特性

- 3 个独立单元，每单元 6 路 PWM 输出（3 相 × 上下桥臂）
- 锯齿波（向上计数）和三角波（向上+向下计数）两种波形模式
- 计数时钟：PCLK0 或外部 TIM4_CLK 输入，分频 1~1024
- 通用比较输出（OC）：6 路 OCCR 比较寄存器，灵活的端口状态控制（OCMR 16/32 位模式）
- 专用比较事件：6 路 SCCR，支持比较启动/延时启动模式，可触发 ADC
- PWM 输出模式：直通模式（独立/扩展/软件互补）、死区定时器模式、死区滤波模式
- 硬件死区：PDAR/PDBR 分别控制上升沿和下降沿死区时间
- 缓存功能：CPSR/OCCR/OCMR/SCCR/SCMR 均带缓存，可与周期间隔响应联动传输
- 周期间隔响应：上下溢中断屏蔽计数器（ZIM/PIM），降低中断频率
- EMB 控制：异步清零 MOE，PWM 端口输出预设安全状态
- 监测输出：TIM4_PCT（周期监测）、TIM4_ADSM（专用事件监测）

## 功能导航大纲

> 小节编号对应原始手册 `21-Timer4-通用控制定时器.md` 中的标题。

| 区域 | 小节 | 关键内容 |
|------|------|----------|
| 概述 | 22.1-22.2 | 简介、基本框图、端口列表 |
| **波形模式** | 22.3.1-22.3.2 | 锯齿波/三角波计数动作、周期计算公式 |
| 比较输出 | 22.3.3 | 锯齿波/三角波下输出波形示例 |
| **缓存功能** | 22.3.4 | CPSR/OCCR/OCMR/SCCR/SCMR 缓存传输时机与周期间隔联动 |
| **PWM 输出** | 22.3.5 | 独立/扩展/互补 PWM、死区定时器模式、死区滤波模式 |
| 周期间隔响应 | 22.3.6 | ZIM/PIM 中断屏蔽、CVPR 设定、专用事件周期间隔 |
| **EMB 控制** | 22.3.7 | EMB 事件 → MOE 清零 → 端口输出预设状态、AOE 自动恢复 |
| 监测输出 | 22.3.8 | TIM4_PCT（周期）、TIM4_ADSM（专用事件）监测端口 |
| **中断/事件** | 22.4 | 计数比较匹配、计数周期匹配、重载计数匹配、专用比较事件 |
| 寄存器 | 22.5 | 50+ 个寄存器（CNTR/CPSR/CCSR/CVPR/OCCRm/OCMRm/SCCRm/POCRn/PSCR/PDAR/PDBR 等） |

## 寄存器速查

> Unit1: 0x40038000, Unit2: 0x40038400, Unit3: 0x40038800

| 寄存器 | 偏移 | 宽度 | 用途 | 关键位字段 |
|--------|------|------|------|-----------|
| TMR4_CNTR | 0x46 | 16 | 计数值 | 当前计数值 |
| TMR4_CPSR | 0x42 | 16 | 周期基准 | 计数峰值（带缓存） |
| **TMR4_CCSR** | 0x48 | 16 | 控制状态 | ECKEN[15] 时钟源, MODE[5] 波形, STOP[6], CLEAR[4], CKDIV[3:0] 分频, BUFEN[7], IRQZF[14]/IRQPF[9] |
| TMR4_CVPR | 0x4A | 16 | 有效周期 | ZIM[3:0]/PIM[7:4] 屏蔽设定, ZIC[11:8]/PIC[15:12] 屏蔽计数器 |
| TMR4_OCCRm | 各异 | 16 | 通用比较基准 | UH/UL/VH/VL/WH/WL 各一个（带缓存） |
| TMR4_OCSRn | 各异 | 16 | 通用控制状态 | OCEH/OCEL 输出使能, OCIEH/OCIEL 中断使能, OCFH/OCFL 匹配标志 |
| TMR4_OCERn | 各异 | 16 | 通用扩展控制 | CHBUFEN/CLBUFEN 缓存传输, LMCH/LMCL 周期间隔联动 |
| TMR4_OCMRm | 各异 | 16/32 | 通用模式控制 | H 通道 16 位, L 通道 32 位（含扩展位），定义各条件下端口状态 |
| TMR4_SCCRm | 各异 | 16 | 专用比较基准 | 比较值或延迟值（带缓存） |
| TMR4_SCSRm | 各异 | 16 | 专用控制状态 | EVTMS[8] 模式, EVTOS[4:2] 输出选择, ZEN/UEN/PEN/DEN 方向使能 |
| TMR4_POCRn | 各异 | 16 | PWM 基本控制 | PWMMD[1:0] PWM 模式选择 |
| **TMR4_PSCR** | 0xE0 | 32 | PWM 状态控制 | MOE[0] 主输出使能, AOE[1] 自动恢复, OExy 端口输出使能, OSxy EMB 预设状态 |
| TMR4_PDARn | 各异 | 16 | 死区控制 A | 下降沿死区时间 |
| TMR4_PDBRn | 各异 | 16 | 死区控制 B | 上升沿死区时间 |
| TMR4_PFSRn | 各异 | 16 | PWM 滤波控制 | 滤波宽度（死区滤波模式） |
| TMR4_RCSR | 0xA4 | 16 | 重载控制 | RTIDU/RTIDV/RTIDW 重载中断使能 |

## 典型初始化流程

```c
/* === 三角波互补 PWM + 硬件死区 === */
// 1. 使能时钟 + 配置 PWM 输出引脚
LL_PERIPH_WE(LL_PERIPH_SEL);
GPIO_SetFunc(TIM4_OXH_PORT, TIM4_OXH_PIN, GPIO_FUNC_2);
GPIO_SetFunc(TIM4_OXL_PORT, TIM4_OXL_PIN, GPIO_FUNC_2);
FCG_Fcg2PeriphClockCmd(FCG2_PERIPH_TMR4_1, ENABLE);

// 2. 初始化计数器（三角波）
stc_tmr4_init_t stcTmr4Init;
(void)TMR4_StructInit(&stcTmr4Init);
stcTmr4Init.u16ClockDiv    = TMR4_CLK_DIV128;
stcTmr4Init.u16PeriodValue = periodValue;
(void)TMR4_Init(CM_TMR4_1, &stcTmr4Init);

// 3. 初始化通用比较输出（OC）
stc_tmr4_oc_init_t stcOcInit;
(void)TMR4_OC_StructInit(&stcOcInit);
stcOcInit.u16CompareValue = periodValue / 2U;
(void)TMR4_OC_Init(CM_TMR4_1, TMR4_OC_CH_UL, &stcOcInit);
// 设置 OCMR 模式（低通道 32 位，定义各条件下翻转行为）
un_tmr4_oc_ocmrl_t unOcmrl;
unOcmrl.OCMRx_f.OPDCL = TMR4_OC_INVT;   // 向下匹配翻转
unOcmrl.OCMRx_f.OPUCL = TMR4_OC_INVT;   // 向上匹配翻转
// ... 其余条件配置
TMR4_OC_SetLowChCompareMode(CM_TMR4_1, TMR4_OC_CH_UL, unOcmrl);
TMR4_OC_Cmd(CM_TMR4_1, TMR4_OC_CH_UL, ENABLE);

// 4. 初始化 PWM（死区定时器模式）
stc_tmr4_pwm_init_t stcPwmInit;
(void)TMR4_PWM_StructInit(&stcPwmInit);
stcPwmInit.u16Mode     = TMR4_PWM_MD_DEAD_TMR;
stcPwmInit.u16ClockDiv = TMR4_PWM_CLK_DIV128;
(void)TMR4_PWM_Init(CM_TMR4_1, TMR4_PWM_CH_U, &stcPwmInit);
TMR4_PWM_SetDeadTimeValue(CM_TMR4_1, TMR4_PWM_CH_U,
    TMR4_PWM_PDAR_IDX, deadTimeA);
TMR4_PWM_SetDeadTimeValue(CM_TMR4_1, TMR4_PWM_CH_U,
    TMR4_PWM_PDBR_IDX, deadTimeB);
TMR4_PWM_SetPortOutputMode(CM_TMR4_1, TMR4_PWM_PIN_OUH,
    TMR4_PWM_PIN_OUTPUT_NORMAL);
TMR4_PWM_SetPortOutputMode(CM_TMR4_1, TMR4_PWM_PIN_OUL,
    TMR4_PWM_PIN_OUTPUT_NORMAL);

// 5. 使能主输出 + 启动计数器
TMR4_PWM_MainOutputCmd(CM_TMR4_1, ENABLE);
TMR4_Start(CM_TMR4_1);
```

## 常见陷阱与注意事项

1. ⚠️ **CPSR 缓存禁止时修改风险**：缓存禁止（BUFEN=0）时写入 CPSR 立即生效，若新值 < 当前 CNTR，计数器将一直递增到 0xFFFF 才归零
2. ⚠️ **OCMR 独立/链接模式区分**：OCMRxl 的 bit[31:20] 和 bit[15:4] 写相同值且 bit[19:16]=0 时为独立模式（*L 只看 OCCRxl），否则为链接模式（*L 同时受 OCCRxh 和 OCCRxl 影响）
3. ⚠️ **PWM 输出前必须使能 MOE + OExy**：PSCR.MOE=1 且 OExy=1 后 PWM 才能输出到引脚，EMB 事件会异步清零 MOE
4. ⚠️ **MOE 硬件延迟**：EMB 清零 MOE 后需等 4 个 Timer4 总线时钟，EMB 解除后需等 6 个时钟才能在总线上读到实际 MOE 值
5. ⚠️ **外部时钟首个边沿无效**：使用 TIM4_CLK 外部输入时，写入 STOP=1 后第一个边沿视为无效，计数从第二个边沿开始
6. ⚠️ **周期间隔运行中修改 ZIM/PIM 不立即生效**：需写入 CLEAR=1 或等下一次中断屏蔽计数器归零后才加载新值
7. ⚠️ **延时启动模式重触发**：延迟计数运行中若再次发生 OCCR 匹配，延迟计数器重载重新计数，此时专用事件可能一直不产生
8. ⚠️ **计数时钟不分频时才能用 PCT 监测**：TIM4_PCT 周期监测仅在 CKDIV=0（不分频）时有效

## 官方例程索引

| 例程名 | 绝对路径 | 用途简述 |
|--------|---------|---------|
| timer4_counter_sawtooth | `$EXAMPLES\timer4\timer4_counter_sawtooth` | 锯齿波计数模式：基本计数 + 溢出中断 |
| timer4_counter_triangular | `$EXAMPLES\timer4\timer4_counter_triangular` | 三角波计数模式：基本计数 + 峰谷中断 |
| timer4_event_compare | `$EXAMPLES\timer4\timer4_event_compare` | 专用比较事件：SCCR 比较匹配触发事件输出 |
| timer4_event_delay | `$EXAMPLES\timer4\timer4_event_delay` | 专用事件延时启动：OCCR 匹配后延时触发 |
| timer4_oc_double_ch | `$EXAMPLES\timer4\timer4_oc_double_ch` | 通用比较双通道：OCCRxh+OCCRxl 链接模式 |
| timer4_oc_high_ch | `$EXAMPLES\timer4\timer4_oc_high_ch` | 通用比较高通道（H）：OCCRxh 独立比较输出 |
| timer4_oc_low_ch | `$EXAMPLES\timer4\timer4_oc_low_ch` | 通用比较低通道（L）：OCCRxl 独立比较输出 |
| timer4_pwm_dead_timer | `$EXAMPLES\timer4\timer4_pwm_dead_timer` | PWM 死区定时器：硬件互补 PWM + 死区控制 |
| timer4_pwm_dead_timer_filter | `$EXAMPLES\timer4\timer4_pwm_dead_timer_filter` | PWM 死区滤波：脉宽滤波 + 死区控制 |
| timer4_pwm_reload_int | `$EXAMPLES\timer4\timer4_pwm_reload_int` | PWM 重载中断：PFSR 重载定时器计数匹配中断 |
| timer4_pwm_through | `$EXAMPLES\timer4\timer4_pwm_through` | PWM 直通模式：OC 比较输出直接驱动端口 |

> `$EXAMPLES` = `D:\Dev\SDKs\HC32\HC32F4A0\HC32F4A0_DDL_Rev2.4.0\projects\ev_hc32f4a0_lqfp176\examples`

## 相关应用笔记

（未找到独立的 Timer4 应用笔记）

## 源文件引用

- **手册 Markdown**: `D:\Library\10_Datasheets\11_MCU\HC32系列\HC32F4A0\21-Timer4-通用控制定时器\21-Timer4-通用控制定时器.md`
- **手册 PDF**: `D:\Library\10_Datasheets\11_MCU\HC32系列\HC32F4A0\RM_HC32F4A0系列参考手册_Rev1.40.pdf`
