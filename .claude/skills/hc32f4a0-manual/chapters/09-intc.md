# INTC — 中断控制器

> ✅ 本知识卡已填充。最后更新：2026-03-25

## 模块概述

HC32F4A0 的中断控制器 (INTC) 负责将外设中断事件请求路由到 Cortex-M4 NVIC。芯片提供 144 个 NVIC 中断向量（IRQ0~143），约 512 个中断事件请求源。INTC 通过中断选择寄存器 (INTC_SELn) 实现"多对一"灵活映射：向量 0~31 可自由选择任意事件源（Global），向量 32~127 按分组选择（Group），向量 128~143 为共享中断（Share，多个事件源共用一个向量，需在 ISR 中判标志）。还支持 16 路外部引脚中断 (EIRQ0~15)、NMI 不可屏蔽中断、32 路软件中断、停止模式唤醒事件。

## 关键特性

- 144 个 NVIC 中断向量，16 级可编程优先级（4 位）
- ~512 个中断事件请求源，通过 INTC_SELn 映射到 NVIC
- 三种向量映射模式：Global（0~31 自由选）、Group（32~127 分组选）、Share（128~143 位使能共享）
- 16 路外部引脚中断 EIRQ0~15，支持上升/下降/双边沿/低电平触发
- EIRQ 双重数字滤波器：滤波器 A（基于 PCLK3 采样）+ 滤波器 B（固定宽度，停止模式可用）
- NMI 不可屏蔽中断源：SWDT、PVD1、PVD2、XTAL 停止、SRAM 校验错误、MPU 总线错误、WDT
- 32 路软件中断/事件（INTC_SWIER）
- 停止模式唤醒事件选择（INTC_WUPEN）：EIRQ、SWDT、PVD、RTC、Timer0/2、CMP、USART、USB、ETH 等

## 功能导航大纲

> 小节编号对应原始手册 `kuma_HC32F4A0手册_INTC.md` 中的标题。

| 区域 | 小节 | 关键内容 |
|------|------|----------|
| 概述 | 10.1 | 144 向量、16 优先级、16 EIRQ、32 软件中断 |
| 系统框图 | 10.2.1 | **中断系统框图**（事件源→INTC→NVIC/WFI/WFE 路由） |
| **中断向量表** | 10.3.1 | NVIC 向量 0~143 分配规则 |
| **中断事件请求序号** | 10.3.2 | ~512 个事件源编号 + 到 SEL/VSSEL 寄存器的映射表 |
| 中断选择 | 10.4.1 | INTC_SEL0~31（Global）、SEL32~127（Group）、VSSEL128~143（Share） |
| 事件选择 | 10.4.2 | WFE 唤醒用事件选择 |
| **外部管脚中断** | 10.4.3 | EIRQ0~15 配置、边沿/电平触发 |
| NMI 不可屏蔽中断 | 10.4.4 | NMI 源选择与使能 |
| 软件中断 | 10.4.5 | SWIER 写 1 触发、写 0 清除 |
| **EIRQ 数字滤波** | 10.4.6-10.4.7 | 滤波器 A（PCLK3 采样）、滤波器 B（固定宽度，停止模式可用） |
| **低功耗唤醒** | 10.4.8 | 休眠/停止/掉电模式返回条件 |
| 内部触发事件 | 10.4.9 | ADC/Timer/DMA 等外设触发源 |
| 寄存器-控制 | 10.5.1-10.5.7 | NOCCR/NMIENR/NMIFR/NMICFR/EIRQCRx/EIFR/EIFCR |
| **寄存器-中断选择** | 10.5.8-10.5.10 | SEL0~31(Global)/SEL32~127(Group)/VSSEL128~143(Share) |
| 寄存器-唤醒/SW | 10.5.11-10.5.14 | WUPEN/SWIER/EVTER/IER |

## 寄存器速查

> BASE_ADDR: INTC=0x40051000

| 寄存器 | 偏移 | 用途 | 关键位字段 |
|--------|------|------|-----------|
| INTC_NOCCR | 0x000 | EIRQ 滤波器 B 宽度 | NOCSEL[13:12] |
| INTC_NMIENR | 0x004 | NMI 源使能 | WDTENR[11], XTALSTPENR[5], PVD2ENR[3], PVD1ENR[2], SWDTENR[1] |
| INTC_NMIFR | 0x008 | NMI 标志（只读） | 各源标志位 |
| INTC_NMICFR | 0x00C | NMI 标志清除 | 写 1 清对应标志 |
| **INTC_EIRQCRx** | 0x010+0x4*x | **EIRQ 控制**（x=0~15） | NOCEN[15], EFEN[7], EISMPCLK[5:4], EIRQTRG[1:0] |
| INTC_WUPEN | 0x050 | 停止模式唤醒使能 | EIRQWUEN[15:0] + 各外设唤醒位 |
| INTC_EIFR | 0x054 | EIRQ 标志（只读） | EIFR[15:0] |
| INTC_EIFCR | 0x058 | EIRQ 标志清除 | 写 1 清对应位 |
| **INTC_SELn** | 0x05C+0x4*n | **中断选择**（n=0~127） | INTSEL[8:0]（中断事件请求序号） |
| **INTC_VSSELn** | 0x25C+0x4*(n-128) | **共享中断使能**（n=128~143） | VSEL[31:0]（每位使能一个事件源） |
| INTC_SWIER | 0x29C | 软件中断触发 | SWIE[31:0]（写 1 触发，写 0 清除） |
| INTC_EVTER | 0x2A0 | 事件使能 | EVTE[31:0] |
| INTC_IER | 0x2A4 | 中断使能 | IER[31:0]（复位值全 1） |

## 典型初始化流程

```c
/* === 外部中断 EIRQ（按键检测，Global 模式） === */
// 1. GPIO 配置为外部中断输入
stc_gpio_init_t stcGpioInit;
(void)GPIO_StructInit(&stcGpioInit);
stcGpioInit.u16ExtInt = PIN_EXTINT_ON;   // 使能 EIRQ 功能
stcGpioInit.u16PullUp = PIN_PU_ON;       // 内部上拉
(void)GPIO_Init(GPIO_PORT_A, GPIO_PIN_00, &stcGpioInit);

// 2. 配置外部中断（触发边沿 + 滤波）
stc_extint_init_t stcExtIntInit;
(void)EXTINT_StructInit(&stcExtIntInit);
stcExtIntInit.u32Filter      = EXTINT_FILTER_ON;
stcExtIntInit.u32FilterClock = EXTINT_FCLK_DIV8;
stcExtIntInit.u32Edge        = EXTINT_TRIG_FALLING;
(void)EXTINT_Init(EXTINT_CH00, &stcExtIntInit);

// 3. 注册中断回调（将事件源映射到 NVIC 向量）
stc_irq_signin_config_t stcIrqSignConfig;
stcIrqSignConfig.enIntSrc    = INT_SRC_PORT_EIRQ0;
stcIrqSignConfig.enIRQn      = INT001_IRQn;         // Global 向量 1
stcIrqSignConfig.pfnCallback = &MyEirq0Callback;
(void)INTC_IrqSignIn(&stcIrqSignConfig);

// 4. NVIC 配置
NVIC_ClearPendingIRQ(INT001_IRQn);
NVIC_SetPriority(INT001_IRQn, DDL_IRQ_PRIO_DEFAULT);
NVIC_EnableIRQ(INT001_IRQn);

/* === 回调函数中清标志 === */
void MyEirq0Callback(void)
{
    if (SET == EXTINT_GetExtIntStatus(EXTINT_CH00)) {
        // 处理...
        EXTINT_ClearExtIntStatus(EXTINT_CH00);
    }
}
```

## 常见陷阱与注意事项

1. ⚠️ **一个中断源不可同时映射到多个 NVIC 向量**：同一 INT_SRC 只能写入一个 INTC_SELn
2. ⚠️ **Group/Share 向量有分组限制**：SEL32~37 只能选 0x000~0x01F 范围事件，SEL38~43 选 0x020~0x03F，依此类推
3. ⚠️ **共享中断需在 ISR 中判标志**：VSSEL128~143 多个事件共用一个向量，必须逐个检查哪个事件触发
4. ⚠️ **EIRQ 回调中必须清 EIFR 标志**：否则中断会反复触发。用 `EXTINT_ClearExtIntStatus()`
5. ⚠️ **进停止模式前关闭滤波器 A**：滤波器 A 依赖 PCLK3，停止模式下 PCLK3 停止。用滤波器 B 替代
6. ⚠️ **NMI 进 WFI 前须确认标志清零**：执行 WFI 前确认 INTC_NMIFR 所有状态位为 0
7. ⚠️ **停止模式唤醒需同时设 WUPEN 和 NVIC**：仅设 WUPEN 不够，还需使能对应 NVIC 中断
8. ⚠️ **EIRQ 引脚映射规则**：EIRQn 对应各端口的第 n 个引脚（如 PA0/PB0/PC0 都可作 EIRQ0），需在 GPIO 设 PCRxy.INTE
9. ⚠️ **软件中断写 0 才能清除**：SWIER 写 1 触发中断，必须写 0 清除，否则持续触发

## 官方例程索引

| 例程名 | 绝对路径 | 用途简述 |
|--------|---------|---------|
| intc_extint_key | `$EXAMPLES\intc\intc_extint_key` | 外部中断按键：演示 Global/Group/Share 三种中断注册方式 |
| intc_nmi_xtalstop | `$EXAMPLES\intc\intc_nmi_xtalstop` | NMI 中断：XTAL 停止检测触发 NMI |
| intc_swint | `$EXAMPLES\intc\intc_swint` | 软件中断：SWIER 触发软件中断 |

> `$EXAMPLES` = `D:\Dev\SDKs\HC32\HC32F4A0\HC32F4A0_DDL_Rev2.4.0\projects\ev_hc32f4a0_lqfp176\examples`

## 相关应用笔记

（无直接相关 AN）

## 源文件引用

- **手册 Markdown**: `D:\Library\10_Datasheets\11_MCU\HC32系列\HC32F4A0\9-INTC-中断控制器\kuma_HC32F4A0手册_INTC.md`
- **手册 PDF**: `D:\Library\10_Datasheets\11_MCU\HC32系列\HC32F4A0\RM_HC32F4A0系列参考手册_Rev1.40.pdf`
