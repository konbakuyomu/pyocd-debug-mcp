# GPIO — 通用 IO

> ✅ 本知识卡已填充。最后更新：2026-03-25

## 模块概述

HC32F4A0 提供 PA~PI 共 9 组 GPIO 端口，每组最多 16 个引脚。每个引脚可独立配置为通用输入/输出、最多 64 种周边复用功能、外部中断(EIRQ)输入、Event Port 事件端口、或模拟功能。支持推挽/开漏输出、高/中/低三档驱动能力、CMOS/Schmitt 输入切换、内部上拉，以及双功能同时有效（不可同时两个输出）。

## 关键特性

- 每组 16 pin，PA~PI 共 9 组（PI 不足 16 个）
- 每个 pin 最多 64 种可选复用功能（PFSRxy.FSEL[5:0]）
- 支持双周边功能同时有效（PCCR.BFSEL + PFSRxy.BFE）
- 推挽/NMOS 开漏输出（PCRxy.NOD）
- 高/中/低三档驱动能力（PCRxy.DRV[1:0]）
- CMOS/Schmitt 输入模式切换（PCRxy.CINSEL）
- 内部上拉电阻（PCRxy.PUU）；USB 引脚内藏 400KΩ 下拉
- 外部中断 EIRQ0~15 输入（PCRxy.INTE），与 INTC 配合
- 4 组 Event Port（每组 16 端口），可作为 AOS 触发源/目标
- 输出锁存功能（PCRxy.LTE）防止功能切换时产生毛刺
- 写保护寄存器（PWPR）防止误写

## 功能导航大纲

> 小节编号对应原始手册 `kuma_HC32F4A0手册_GPIO.md` 中的标题，可直接搜索定位。

| 区域 | 小节 | 关键内容 |
|------|------|----------|
| 概述 | 9.1-9.2 | 主要特性列表、端口基本结构示意图 |
| **GPIO 输入 (GPI)** | 9.3.1 | PIDRx 读取、PINAER 输入 MOS 常开、PCCR.RDWT 等待周期 |
| **GPIO 输出 (GPO)** | 9.3.1 | PODRx/POERx/POSRx/PORRx/POTRx、PCRxy.POUTE/POUT |
| 周边功能复用 | 9.3.2 | PFSRxy.FSEL[5:0] 选择 Func0~63；PSPCR 控制 JTAG/SWD |
| 双周边功能 | 9.3.3 | PCCR.BFSEL[5:0] + PFSRxy.BFE，禁止两个输出同时有效 |
| **Event Port** | 9.3.4 | 4 组×16 端口，触发源/被触发对象，需先使能 AOS (PWC_FCG0) |
| **外部中断 EIRQ** | 9.3.5 | PCRxy.INTE 使能，EIRQy 映射规则，需配合 INTC 章节 |
| 模拟功能 | 9.3.6 | PCRxy.DDIS=1 禁止数字功能 |
| 通用控制 | 9.3.7 | 上拉(PUU)、驱动力(DRV)、开漏(NOD)、输入模式(CINSEL) |
| 寄存器-GPIO 基础 | 9.4.1-9.4.6 | PIDRx/PODRx/POERx/POSRx/PORRx/POTRx |
| 寄存器-全局控制 | 9.4.7-9.4.10 | PSPCR/PCCR/PINAER/PWPR |
| **寄存器-引脚控制** | 9.4.11-9.4.12 | **PCRxy** (核心！含 INTE/DRV/NOD/PUU 等)、**PFSRxy** (功能选择) |
| 寄存器-Event Port | 9.4.13-9.4.20 | PEVNTDIRRm/PEVNTIDRm/PEVNTODRm/.../PEVNTNFCR |
| 注意事项 | 9.5 | 功能勿重复分配、模拟用 DDIS=1、切换时用 LTE |

## 寄存器速查

> BASE_ADDR: GPIO=0x40053800, Event Port=0x40010800

| 寄存器 | 偏移 | 用途 | 关键位字段 |
|--------|------|------|-----------|
| PIDRx | 0x00+0x10*n | 输入数据（只读） | PIN[15:0] |
| PODRx | 0x04+0x10*n | 输出数据 | POUT[15:0] |
| POERx | 0x06+0x10*n | 输出使能 | POUTE[15:0] |
| POSRx | 0x08+0x10*n | 输出置位（写1置位） | POS[15:0] |
| PORRx | 0x0A+0x10*n | 输出复位（写1清零） | POR[15:0] |
| POTRx | 0x0C+0x10*n | 输出翻转（写1翻转） | POT[15:0] |
| PSPCR | 0x3F8 | JTAG/SWD 特殊功能选择 | SPFE[4:0]（优先级高于 FSEL） |
| PCCR | 0x3F8 | 公共控制 | RDWT[2:0](读等待), BFSEL[5:0](副功能) |
| PINAER | 0x3FA | 输入 MOS 常开控制 | PINAE[8:0] (每 bit 控制一组) |
| PWPR | 0x3FC | 写保护 | WE=1 且 WP=0xA5 时解锁 |
| **PCRxy** | 0x400+0x40*n+0x4*y | **引脚控制（核心）** | DDIS[15] LTE[14] **INTE[12]** CINSEL[10] INVE[9] PIN[8] PUU[6] DRV[5:4] NOD[2] POUTE[1] POUT[0] |
| **PFSRxy** | 0x402+0x40*n+0x4*y | **功能选择** | BFE[8], **FSEL[5:0]** |

> n: PA~PI 对应 0~8；y: Pin0~15 对应 0~15

## 典型初始化流程

```c
/* === GPIO 输出示例 (LED) === */
// 1. 解除写保护
LL_PERIPH_WE(LL_PERIPH_GPIO);

// 2. 初始化结构体 + 配置
stc_gpio_init_t stcGpioInit;
(void)GPIO_StructInit(&stcGpioInit);    // 先填默认值
stcGpioInit.u16PinState = PIN_STAT_RST; // 初始低电平
stcGpioInit.u16PinDir   = PIN_DIR_OUT;  // 输出模式
(void)GPIO_Init(GPIO_PORT_C, GPIO_PIN_09, &stcGpioInit);

// 3. 恢复写保护
LL_PERIPH_WP(LL_PERIPH_GPIO);

// 4. 使用
GPIO_TogglePins(GPIO_PORT_C, GPIO_PIN_09);  // 翻转
GPIO_SetPins(GPIO_PORT_C, GPIO_PIN_09);     // 置高
GPIO_ResetPins(GPIO_PORT_C, GPIO_PIN_09);   // 置低

/* === GPIO 输入示例 (按键) === */
stcGpioInit.u16PullUp = PIN_PU_ON;     // 使能内部上拉
stcGpioInit.u16PinDir = PIN_DIR_IN;    // 输入模式
(void)GPIO_Init(GPIO_PORT_A, GPIO_PIN_00, &stcGpioInit);
// 读取: PIN_RESET == GPIO_ReadInputPins(GPIO_PORT_A, GPIO_PIN_00)

/* === 周边功能复用示例 (USART TX) === */
// 将 PE6 配置为 USART1_TX (Func32 = 0x20)
GPIO_SetFunc(GPIO_PORT_E, GPIO_PIN_06, GPIO_FUNC_32);
```

## 常见陷阱与注意事项

1. ⚠️ **JTAG/SWD 引脚释放**：PA13/PA14/PA15/PB3/PB4 复位后为 JTAG/SWD 功能（PSPCR=0x1F）。要用作普通 IO 必须先将 PSPCR.SPFE 对应位清零
2. ⚠️ **写保护**：GPIO 寄存器受写保护，操作前必须 `LL_PERIPH_WE(LL_PERIPH_GPIO)`，完成后恢复 `LL_PERIPH_WP`
3. ⚠️ **模拟功能须禁数字**：用作 ADC/DAC/CMP 等模拟输入时，必须设 PCRxy.DDIS=1 禁止数字功能
4. ⚠️ **功能切换防毛刺**：切换引脚功能时先设 LTE=1 锁存输出，改完 FSEL 后再 LTE=0
5. ⚠️ **同一功能勿分配到多个引脚**
6. ⚠️ **高速时钟下读输入需等待**：系统时钟 >50MHz 时需设置 PCCR.RDWT 插入等待周期（见 PCCR 寄存器说明表）
7. ⚠️ **PI13/MD 引脚特殊**：复位时须低电平（用户模式），模式确立后可做普通 IO。不可用作 EIRQ
8. ⚠️ **PC14/PC15 (32K 副振荡器)**：复位后 DDIS=1，用作数字功能前须先清零 DDIS
9. ⚠️ **Event Port 需先使能 AOS**：使用前必须在 PWC_FCG0 中使能 AOS 功能时钟
10. ⚠️ **USB 引脚下拉**：PA11/PA12(USBFS)、PB14/PB15(USBHS) 内藏 ~400KΩ 下拉，始终有效

## 官方例程索引

| 例程名 | 绝对路径 | 用途简述 |
|--------|---------|---------|
| gpio_output | `$EXAMPLES\gpio\gpio_output` | GPIO 输出：LED 翻转，演示 GPIO_Init + GPIO_TogglePins |
| gpio_input | `$EXAMPLES\gpio\gpio_input` | GPIO 输入：按键读取，演示 PIN_PU_ON + GPIO_ReadInputPins |

> `$EXAMPLES` = `D:\Dev\SDKs\HC32\HC32F4A0\HC32F4A0_DDL_Rev2.4.0\projects\ev_hc32f4a0_lqfp176\examples`

## 相关应用笔记

| 笔记名 | 路径 | 关键内容 |
|--------|------|----------|
| 掉电模式 IO 保持功能 | `$MANUAL\AN_HC32系列掉电模式IO保持功能的使用_Rev1.00` | Power Down 模式下 IO 输出状态保持方法 |

> `$MANUAL` = `D:\Library\10_Datasheets\11_MCU\HC32系列\HC32F4A0`

## 源文件引用

- **手册 Markdown**: `D:\Library\10_Datasheets\11_MCU\HC32系列\HC32F4A0\8-GPIO-通用IO\kuma_HC32F4A0手册_GPIO.md`
- **手册 PDF**: `D:\Library\10_Datasheets\11_MCU\HC32系列\HC32F4A0\RM_HC32F4A0系列参考手册_Rev1.40.pdf`
