# EMB — 紧急刹车模块

> ✅ 本知识卡已填充。最后更新：2026-03-25

## 模块概述

EMB（Emergency Brake）是硬件级 PWM 保护模块，在满足特定条件时向 Timer6 / Timer4 发送控制事件，强制停止 PWM 输出（置高/置低/高阻态），用于电机驱动等场景的故障保护。共 7 个组群：group0~3 控制 Timer6（由 Timer6 寄存器选择），group4~6 分别对应 Timer4_1/2/3。

## 关键特性

- **5 种触发源**：外部端口电平、PWM 同相检测、电压比较器（CMP1~4）、外部振荡器停振、软件寄存器控制
- **4 个外部端口**（PORT1~4），每端口支持多引脚复用，支持高/低电平极性选择
- **数字噪声滤波**：3 次采样一致滤波，4 档滤波时钟（PCLK/1, /8, /32, /128）
- **两种释放模式**：自动释放（状态位清零即释放）/ 手动释放（需软件清标志位）
- **EMB_CTL1 和 EMB_CTL2 为单次写入寄存器**（复位后只能写一次）
- 每个 group 可独立配置触发源组合、中断使能和释放策略

## 功能导航大纲

| 区域 | 小节 | 关键内容 |
|------|------|----------|
| 架构 | 23.1~23.2.1 | 结构框图、7 个 group 与 Timer 的映射关系 |
| 外部端口刹车 | 23.2.2 | PORT1~4 引脚分配、极性选择（INVSEL）、噪声滤波、释放控制 |
| PWM 同相刹车 | 23.2.3 | 监控互补 PWM 同高/同低，group0~3 对应 Timer6，group4~6 对应 Timer4 |
| 比较器刹车 | 23.2.4 | CMP1~4 比较结果触发，CMPEN 使能 |
| 振荡器停振刹车 | 23.2.5 | 外部振荡器停止时触发，OSCSTPEN 使能 |
| 软件刹车 | 23.2.6 | EMB_SOE.SOE 直接控制，不产生中断 |
| 寄存器说明 | 23.3 | 7 个寄存器的详细位字段定义 |

## 寄存器速查

> BASE_ADDR: 0x40017C00（group0），每组偏移 0x20（group1=0x40017C20, ..., group6=0x40017CC0）

| 寄存器 | 偏移 | 用途 | 关键位字段 |
|--------|------|------|------------|
| EMB_CTL1 | 0x00 | 触发源使能（**单次写入**） | PORTINEN[4:1], INVSEL[4:1], PWMSEN[7:0]/[2:0], OSCSTPEN, CMPEN[4:1] |
| EMB_CTL2 | 0x04 | 滤波配置 + PWM 电平选择（**单次写入**） | NFEN[4:1], NFSEL[4:1], PWMLV[7:0]/[2:0] |
| EMB_SOE | 0x08 | 软件输出控制 | SOE（b0: 1=停止PWM输出） |
| EMB_STAT | 0x0C | 状态寄存器（只读） | PORTINST[4:1], PORTINF[4:1], OSST, CMPST, PWMST, OSF, CMPF, PWMSF |
| EMB_STATCLR | 0x10 | 状态复位（只写） | PORTINFCLR[4:1], OSFCLR, CMPFCLR, PWMSCLR |
| EMB_INTEN | 0x14 | 中断许可 | PORTININTEN[4:1], OSINTEN, CMPINTEN, PWMSINTEN |
| EMB_RLSSEL | 0x18 | 释放方式选择 | PORTINRSEL[4:1], OSRSEL, CMPRSEL, PWMRSEL（0=标志位释放, 1=状态位自动释放） |

## 典型初始化流程

```c
/* === 以 group0 + Timer6 外部端口刹车为例 === */
/* 1. 使能 EMB 外设时钟 */
FCG_Fcg2PeriphClockCmd(FCG2_PERIPH_EMB_GRP0, ENABLE);

/* 2. 配置 EMB 端口引脚为输入功能 */
GPIO_SetFunc(GPIO_PORT_A, GPIO_PIN_11, GPIO_FUNC_6);  /* EMB_IN0 */

/* 3. 配置 EMB（注意: CTL1/CTL2 只能写一次！） */
stc_emb_tmr6_init_t stcEmbInit;
(void)EMB_TMR6_StructInit(&stcEmbInit);
stcEmbInit.stcPort.stcPort1.u32PortState  = EMB_PORT1_ENABLE;
stcEmbInit.stcPort.stcPort1.u32PortLevel  = EMB_PORT1_DETECT_LVL_LOW;
stcEmbInit.stcPort.stcPort1.u32PortFilterDiv = EMB_PORT1_FILTER_CLK_DIV8;
stcEmbInit.stcPort.stcPort1.u32PortFilterState = EMB_PORT1_FILTER_ENABLE;
(void)EMB_TMR6_Init(CM_EMB0, &stcEmbInit);

/* 4. 设置释放方式：手动释放 */
EMB_SetReleasePwmMode(CM_EMB0, EMB_EVENT_PORT1, EMB_RELEASE_PWM_SEL_FLAG_ZERO);

/* 5. 使能中断 */
EMB_IntCmd(CM_EMB0, EMB_INT_SRC_PORT1, ENABLE);
NVIC_EnableIRQ(EMB_GRP0_IRQn);
```

## 常见陷阱与注意事项

1. ⚠️ **CTL1/CTL2 单次写入**：复位后只能写入一次。配置必须在首次写入时一步到位，之后修改无效
2. ⚠️ **释放模式选择**：RLSSEL=1（状态位自动释放）适合瞬态故障；RLSSEL=0（标志位手动释放）适合安全场景。手动释放时须等状态位先清零再写 STATCLR
3. ⚠️ **端口引脚复用**：PORT1~4 各有 3~4 个可选引脚（见表 23-1），需在 GPIO 中配置正确 AF 功能
4. ⚠️ **噪声滤波**：滤波器采用 3 次一致判定，电机应用建议至少使能 DIV8 滤波
5. ⚠️ **PWM 同相检测**：group0~3 的 PWMSEN 有 8 位（Timer6_1~8），group4~6 仅 3 位（Timer4 U/V/W）
6. ⚠️ **软件刹车不触发中断**：EMB_SOE 仅直接控制 PWM 输出状态

## 官方例程索引

| 例程名 | 绝对路径 | 用途简述 |
|--------|----------|----------|
| emb_cmp_brake_timer6 | `$EXAMPLES\emb\emb_cmp_brake_timer6` | 电压比较器触发 Timer6 刹车 |
| emb_osc_brake_timer6 | `$EXAMPLES\emb\emb_osc_brake_timer6` | 外部振荡器停振触发 Timer6 刹车 |
| emb_port_brake_timer6 | `$EXAMPLES\emb\emb_port_brake_timer6` | 外部端口电平触发 Timer6 刹车 |
| emb_pwm_brake_timer6 | `$EXAMPLES\emb\emb_pwm_brake_timer6` | PWM 同相触发 Timer6 刹车 |
| emb_sw_brake_timer6 | `$EXAMPLES\emb\emb_sw_brake_timer6` | 软件控制 Timer6 刹车 |
| emb_port_brake_timer4 | `$EXAMPLES\emb\emb_port_brake_timer4` | 外部端口触发 Timer4 刹车 |

> `$EXAMPLES` = `D:\Dev\SDKs\HC32\HC32F4A0\HC32F4A0_DDL_Rev2.4.0\projects\ev_hc32f4a0_lqfp176\examples`

## 相关应用笔记

暂无直接针对 EMB 的独立应用笔记。间接相关：`AN_TIMER4与ADC模块在电机FOC控制中单电阻采样联动操作说明_Rev1.02`（Timer4 电机控制场景配合 EMB）。

## 源文件引用

- **手册 Markdown**: `D:\Library\10_Datasheets\11_MCU\HC32系列\HC32F4A0\22-EMB-紧急刹车模块\22-EMB-紧急刹车模块.md`
- **手册 PDF**: `D:\Library\10_Datasheets\11_MCU\HC32系列\HC32F4A0\RM_HC32F4A0系列参考手册_Rev1.40.pdf`
