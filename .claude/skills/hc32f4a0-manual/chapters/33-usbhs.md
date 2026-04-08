# USBHS — USB2.0 高速模块

> ✅ 本知识卡已填充。最后更新：2026-03-25

## 模块概述

USBHS 是 USB 2.0 兼容的高速控制器，支持主机模式和设备模式。芯片内置全速 PHY（FS 12Mb/s + LS 1.5Mb/s），同时提供 ULPI 接口外接高速 PHY（HS 480Mb/s）。支持 USB 2.0 全部四种传输类型（控制/批量/中断/同步），内嵌 DMA 和 8KB 专用 FIFO RAM，支持 LPM（Link Power Management）。

## 关键特性

- **双 PHY 接口**：内置全速 PHY（需 USBHS_FSPHYE=1 使能）+ ULPI 外接高速 PHY
- **主机模式**：支持 HS/FS/LS，16 个主机通道，硬件调度器（8 周期 + 8 非周期请求队列）
- **设备模式**：支持 HS/FS，1 个双向 EP0 + 15 个 IN + 15 个 OUT 端点
- **传输类型**：控制、批量、中断、同步全部支持
- **FIFO**：8KB 专用 RAM，可配置分配为多个 FIFO（大小无需 2 的幂次）
- **内嵌 DMA**：可配置 AHB 突发类型（单次/INCR/INCR4/INCR8/INCR16）
- **时钟**需求：48MHz PLL 时钟 + PCLK1 ≥ 60MHz（外接 PHY 还需 60MHz ULPI 时钟）
- **模式识别**：ID 线自动检测或强制设定（FDMOD/FHMOD）
- **SOF 脉冲**可输出到引脚或作为 AOS 源触发 Timer/DMA
- **LPM**支持：USB 2.0 链路电源管理
- **VBUS**：设备模式 5V 耐压管脚，主机模式需外接电源芯片（DRVVBUS 控制使能）
- **片上全速 PHY 工作电压**：VCC 3.0~3.6V

## 功能导航大纲

> 小节编号对应原始手册标题

| 区域 | 小节 | 关键内容 |
|------|------|----------|
| 简介 | 34.1 | USBHS 总体功能描述 |
| 主要特性 | 34.2 | 通用/主机/设备特性分类 |
| 系统框图 | 34.3 | PHY→MAC→FIFO→AHB 架构 |
| 管脚说明 | 34.4 | 片上 PHY(DP/DM/VBUS/ID) + ULPI(CLK/DIR/NXT/STP/D0~D7) |
| 时钟与模式 | 34.5.1 | 三种时钟（48MHz/60MHz/PCLK1）、PHY 选择 |
| 模式决定 | 34.5.2 | ID 线自动识别 vs 强制模式（等待 ≥25ms） |
| 主机功能 | 34.5.3 | 端口供电/连接检测/枚举/挂起/16 通道/调度器 |
| 设备功能 | 34.5.4 | 供电检测/端点配置/FIFO 分配/传输流程 |
| 编程指南 | 34.6 | 初始化序列、主机/设备操作流程 |
| 寄存器 | 34.7 | 5 大类寄存器详述 |

## 寄存器速查

> 系统控制基址: 0x40055400 | 模块基址: 0x400C0000

| 寄存器组 | 偏移范围 | 说明 |
|---------|---------|------|
| USB_SYCTLREG | 系统基址+0x00 | 系统控制（PHY 使能/SOF 输出/滤波） |
| 全局寄存器 | 0x000~0x13C | GVBUSCFG, GAHBCFG, GUSBCFG, GRSTCTL, GINTSTS, GINTMSK, GRXFSIZ, HNPTXFSIZ 等 |
| FIFO 配置 | 0x100~0x13C | HPTXFSIZ, DIEPTXFx(x=1~15) |
| 主机寄存器 | 0x400~0x6FF | HCFG, HFIR, HFNUM, HPRT, HCCHARx/HCINTx/HCTSIZx(x=0~15) |
| 设备寄存器 | 0x800~0xDFF | DCFG, DCTL, DSTS, DIEPCTLx/DIEPINTx/DIEPTSIZx, DOEPCTLx/DOEPINTx |
| 电源控制 | 0xE00 | GCCTL（时钟门控） |
| DFIFO | 0x1000~0x41FF | 数据 FIFO 访问（端点 0~15 × 0x1000 间距） |

## 典型初始化流程

```c
/* 以 USB 设备 CDC 模式为例 */

/* 1. 使能时钟：USB 48MHz PLL + PCLK1 ≥ 60MHz */
CLK_SetUSBClockSrc(CLK_USBCLK_PLLHP);  /* 配置 USB 48MHz 时钟源 */
FCG_Fcg1PeriphClockCmd(FCG1_PERIPH_USBHS, ENABLE);

/* 2. GPIO 配置：DP/DM 设为模拟功能（关闭数字功能） */
GPIO_SetFunc(GPIO_PORT_B, GPIO_PIN_14 | GPIO_PIN_15, GPIO_FUNC_10);
/* VBUS 检测引脚 PB13 */
stc_gpio_init_t stcGpioInit = {.u16PinDir = PIN_DIR_IN};
GPIO_Init(GPIO_PORT_B, GPIO_PIN_13, &stcGpioInit);

/* 3. 系统控制寄存器：使能片上全速 PHY */
USB_SYCTLREG |= USB_SYCTLREG_USBHS_FSPHYE;

/* 4. 模块软复位 */
SET_REG32_BIT(CM_USBHS->GRSTCTL, USBHS_GRSTCTL_CSRST);
while (READ_REG32_BIT(CM_USBHS->GRSTCTL, USBHS_GRSTCTL_CSRST));

/* 5. 配置全局寄存器 */
/* AHB: DMA 使能 + 突发类型 + 全局中断使能 */
CM_USBHS->GAHBCFG = USBHS_GAHBCFG_DMAEN | USBHS_GAHBCFG_GINTMSK;
/* USB 配置: 强制设备模式 + PHY 选择 + 周转时间 */
CM_USBHS->GUSBCFG |= USBHS_GUSBCFG_FDMOD | USBHS_GUSBCFG_PHYSEL;

/* 6. 后续由 USB 中间件库完成端点配置和协议栈初始化 */
```

## 常见陷阱与注意事项

1. **PCLK1 频率要求**：PCLK1 必须 ≥ 60MHz，否则寄存器访问和 DMA 传输异常
2. **片上 PHY 仅全速**：内置 PHY 不支持高速 480Mb/s，需高速传输必须外接 ULPI PHY
3. **强制模式需等待 25ms**：写入 FDMOD/FHMOD 后必须等待至少 25ms 才能生效
4. **模块复位后等 AHB 空闲**：CSRST 自清零后还需检查 AHBIDL=1 且等 3 个 PHY 周期
5. **DP/DM 为模拟功能**：不使用 USB 时这两个引脚的数字翻转会产生额外电流消耗
6. **VCC 电压范围**：使用片上全速 PHY 时 VCC 必须在 3.0~3.6V
7. **主机需外部供电**：内部 PHY 无法提供 5V VBUS，必须外接电源芯片
8. **模式切换需重新编程**：从主机切到设备模式时，新模式寄存器必须重新初始化为复位值
9. **所有寄存器 32 位对齐**：只能以 32 位方式访问
10. **FIFO 分配**：TX/RX FIFO 大小可灵活配置但不能超过 8KB 总量，需根据端点数和包大小合理规划

## 官方例程索引

| 例程名 | 绝对路径 | 用途简述 |
|--------|---------|---------:|
| usb_dev_cdc | `$APPS\usb\usb_dev_cdc` | USB 设备 CDC 虚拟串口 |
| usb_dev_msc | `$APPS\usb\usb_dev_msc` | USB 设备 MSC 大容量存储 |
| usb_dev_hid_custom | `$APPS\usb\usb_dev_hid_custom` | USB 设备自定义 HID |
| usb_dev_mouse | `$APPS\usb\usb_dev_mouse` | USB 设备 HID 鼠标 |
| usb_dev_winusb | `$APPS\usb\usb_dev_winusb` | USB 设备 WinUSB |
| usb_dev_cdc_msc | `$APPS\usb\usb_dev_cdc_msc` | USB 复合设备 CDC+MSC |
| usb_dev_hid_cdc | `$APPS\usb\usb_dev_hid_cdc` | USB 复合设备 HID+CDC |
| usb_dev_hid_msc | `$APPS\usb\usb_dev_hid_msc` | USB 复合设备 HID+MSC |
| usb_host_cdc | `$APPS\usb\usb_host_cdc` | USB 主机 CDC |
| usb_host_mouse_kb | `$APPS\usb\usb_host_mouse_kb` | USB 主机 HID（鼠标/键盘） |
| usb_host_msc | `$APPS\usb\usb_host_msc` | USB 主机 MSC |

> `$APPS` = `D:\Dev\SDKs\HC32\HC32F4A0\HC32F4A0_DDL_Rev2.4.0\projects\ev_hc32f4a0_lqfp176\applications`
>
> USB 中间件库：`D:\Dev\SDKs\HC32\HC32F4A0\HC32F4A0_DDL_Rev2.4.0\midwares\hc32\usb\`（usb_device_lib + usb_host_lib）

## 相关应用笔记

| 笔记名 | 路径 | 关键内容 |
|--------|------|----------|
| USB 挂起和唤醒功能 | `$MANUAL\AN_HC32F4A0系列的USB挂起和唤醒功能_Rev1.0\AN_HC32F4A0系列的USB挂起和唤醒功能_Rev1.0.md` | USB Host/Device 挂起、远程唤醒与 CDC 主从样例流程 |
| USB HID 设备实现 | `$MANUAL\AN_HC32F4A0系列实现USB_HID设备_Rev1.00\AN_HC32F4A0系列实现USB_HID设备_Rev1.00.md` | USBHS/USBFS HID 设备描述符、时钟/端点配置和样例 |

> `$MANUAL` = `D:\Library\10_Datasheets\11_MCU\HC32系列\HC32F4A0`

## 源文件引用

- **手册 Markdown**: `D:\Library\10_Datasheets\11_MCU\HC32系列\HC32F4A0\33-USBHS-USB2.0高速模块\33-USBHS-USB2.0高速模块.md`
- **手册 PDF**: `D:\Library\10_Datasheets\11_MCU\HC32系列\HC32F4A0\RM_HC32F4A0系列参考手册_Rev1.40.pdf`
