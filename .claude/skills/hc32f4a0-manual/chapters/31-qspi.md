# QSPI — 四线式串行外设接口

> ✅ 本知识卡已填充。最后更新：2026-03-25

## 模块概述

QSPI（Quad SPI）是一个存储器控制模块，主要用于与带 SPI 兼容接口的串行 ROM（串行 Flash、EEPROM、FeRAM）进行通信。支持扩展 SPI、二线式 SPI、四线式 SPI 三种协议，提供 ROM 映射模式（自动读取）和直接通信模式（软件手动收发指令）两种工作方式。

## 关键特性

- 1 通道，6 根信号线：QSCK（时钟）、QSSN（片选）、QSIO0~QSIO3（数据）
- 支持扩展 SPI / 二线式 SPI / 四线式 SPI 协议（指令/地址/数据阶段可分别配置）
- 支持 SPI 模式 0（CPOL=0）和模式 3（CPOL=1）
- 地址宽度可选 8/16/24/32 位，配合 4-Byte 模式指令切换
- 8 种读取模式：标准读、快速读、二线/四线输出快速读、二线/四线 I/O 快速读、自定义标准/快速读
- 16 字节预读取缓冲区 + 2 字节接收缓冲区，支持边沿/即时停止
- XIP（Execute In Place）模式：省略指令阶段，降低连续读取延迟
- QSPI 总线周期延长功能（SSNW）：避免连续地址读取重复发送指令和地址
- 直接通信模式：通过 DCOM 寄存器逐字节手动收发，支持擦除/写入/ID 读取等任意指令
- 基准时钟 = HCLK / (DIV+1)，分频范围 2~64，支持奇数分频占空比补正（DUTY 位）
- ROM 映射空间 0x98000000，最大 64MB，通过 EXAR 寄存器可扩展至 64MB×63 块
- 中断源：直接通信模式下 ROM 访问错误（RAER）

## 功能导航大纲

> 小节编号对应原始手册标题

| 区域 | 小节 | 关键内容 |
|------|------|----------|
| 简介 | 32.1 | 主要规格表（协议/读模式/直接通信等） |
| 内存映射 | 32.2 | AHB 地址空间映射、ROM 空间镜像、地址宽度影响 |
| SPI 协议 | 32.3.1 | 扩展/二线/四线协议的指令/地址/数据传输方式 |
| SPI 模式 | 32.3.2 | 模式 0/3 时序差异、QSCK 待机电平 |
| 时序调整 | 32.4 | 基准时钟分频(DIV)、占空比补正(DUTY)、QSSN 建立/保持时间、数据接收延迟 |
| ROM 读取指令 | 32.5 | 8 种读模式指令代码、虚拟周期、XIP 选择机制 |
| 总线周期安排 | 32.6 | 独立传输 vs 预读取 vs 总线延长(SSNW) |
| XIP 控制 | 32.7 | 模式代码(XIPMC)、进入/退出 XIP |
| IO2/IO3 状态 | 32.8 | 各读模式下 QSIO2/3 管脚输出状态表 |
| 直接通信 | 32.9 | 进入/退出、DCOM 寄存器读写 → 总线周期 |
| 中断 | 32.10 | RAER 标志（直接通信模式下 ROM 访问错误） |
| 注意事项 | 32.11 | 寄存器配置顺序、模块停止信号 |
| 寄存器 | 32.12 | 9 个寄存器详述 |

## 寄存器速查

> 控制寄存器 BASE_ADDR: 0x9C000000 | ROM 映射空间: 0x98000000

| 寄存器 | 偏移 | 用途 | 关键位字段 |
|--------|------|------|-----------|
| QSPI_CR | 0x0000 | 控制寄存器 | DIV[5:0], DPRSL/APRSL/IPRSL[1:0], SPIMD3, XIPE, DCOME, PFE, PFSAE, MDSEL[2:0] |
| QSPI_CSCR | 0x0004 | 片选控制 | SSNW[1:0](延长时间), SSHW[3:0](最小高电平) |
| QSPI_FCR | 0x0008 | 格式控制 | DUTY, DMCYCN[3:0](虚拟周期), WPOL, SSNLD, SSNHD, 4BIC, AWSL[1:0] |
| QSPI_SR | 0x000C | 状态寄存器 | PFAN, PFFUL, PFNUM[4:0], RAER, XIPF, BUSY |
| QSPI_DCOM | 0x0010 | 直接通信指令 | DCOM[7:0] |
| QSPI_CCMD | 0x0014 | 指令代码 | RIC[7:0] |
| QSPI_XCMD | 0x0018 | XIP 模式代码 | XIPMC[7:0] |
| QSPI_CLR | 0x0024 | 标志清除 | RAERCLR |
| QSPI_EXAR | 0x0804 | 外部扩展地址 | EXADR[5:0] |

## 典型初始化流程

```c
/* 以 W25Q64 四线 I/O 快速读 为例 */

/* 1. GPIO 配置：所有 QSPI 引脚设为高驱动 + 复用功能 18 */
stc_gpio_init_t stcGpioInit = {.u16PinDrv = PIN_HIGH_DRV};
GPIO_Init(GPIO_PORT_C, GPIO_PIN_06, &stcGpioInit);  /* QSCK */
GPIO_SetFunc(GPIO_PORT_C, GPIO_PIN_06, GPIO_FUNC_18);
/* ... QSSN(PC07), QSIO0(PB13), QSIO1(PB12), QSIO2(PB10), QSIO3(PB02) 类似 */

/* 2. 使能 QSPI 外设时钟 */
FCG_Fcg1PeriphClockCmd(FCG1_PERIPH_QSPI, ENABLE);

/* 3. QSPI 初始化 */
stc_qspi_init_t stcQspiInit;
stcQspiInit.u32ClockDiv     = QSPI_CLK_DIV3;
stcQspiInit.u32ReadMode     = QSPI_RD_MD_QUAD_IO_FAST_RD;  /* 四线 I/O 快速读 (0xEB) */
stcQspiInit.u32PrefetchMode = QSPI_PREFETCH_MD_EDGE_STOP;
stcQspiInit.u32DummyCycle   = QSPI_DUMMY_CYCLE6;            /* W25Q64 对应 6 个 */
stcQspiInit.u32AddrWidth    = QSPI_ADDR_WIDTH_24BIT;
stcQspiInit.u32SetupTime    = QSPI_QSSN_SETUP_ADVANCE_QSCK1P5;
stcQspiInit.u32ReleaseTime  = QSPI_QSSN_RELEASE_DELAY_QSCK1P5;
stcQspiInit.u32IntervalTime = QSPI_QSSN_INTERVAL_QSCK2;
QSPI_Init(&stcQspiInit);

/* 4. ROM 映射读取：直接通过地址指针读 Flash 数据 */
uint8_t data = *(volatile uint8_t *)(0x98000000UL + flashAddr);

/* 5. 直接通信模式：擦除/写入操作 */
QSPI_EnterDirectCommMode();
QSPI_WriteDirectCommValue(0x06U);  /* Write Enable */
QSPI_ExitDirectCommMode();
/* ... 后续发送 Sector Erase / Page Program 指令 */
```

## 常见陷阱与注意事项

1. **读模式与 Dummy 周期必须配套**：不同读模式需要不同数量的虚拟周期（如 Quad I/O Fast Read 需 6 个，Fast Read 需 8 个），配置不匹配会导致数据错误
2. **模块复位后处于停止状态**：必须先通过 FCG1 开启 QSPI 时钟才能访问寄存器
3. **直接通信模式下不能读 ROM**：进入 DCOME 后对 ROM 区域的读访问会触发 RAER 错误中断
4. **直接通信不支持多线式**：直接通信模式只能走 SPI 单线（QSIO0），Quad 写入需使用自定义模式
5. **XIP 仅适用于快速读类模式**：标准读无虚拟周期，无法传送 XIP 模式代码
6. **预读取监测程序不能放在目标 Flash 中**：否则预读取目标频繁切换导致无限循环
7. **自定义模式下 CS 需 GPIO 手动控制**：硬件不自动管理 QSSN，必须用 GPIO 拉低/拉高
8. **写入前必须发送 Write Enable (0x06)**：且 WE 命令和后续命令需分别独立的 CS 帧（中间 CS 拉高 ≥1μs）
9. **地址宽度影响 ROM 空间镜像**：选择 8/16/24 位时高位空间访问会出现低位空间的重复映像
10. **寄存器配置顺序**：必须在通信开始前完成所有配置，否则总线周期可能在配置完成前启动

## 官方例程索引

| 例程名 | 绝对路径 | 用途简述 |
|--------|---------|---------:|
| qspi_base | `$EXAMPLES\qspi\qspi_base` | W25Q64 四线 I/O 快速读 + ROM 映射读取 + 直接通信擦写 |
| qspi_custom_mode | `$EXAMPLES\qspi\qspi_custom_mode` | 自定义协议模式：Quad 写入(0x32) + 标准读(0x03)，CS 手动控制 |

> `$EXAMPLES` = `D:\Dev\SDKs\HC32\HC32F4A0\HC32F4A0_DDL_Rev2.4.0\projects\ev_hc32f4a0_lqfp176\examples`

## 相关应用笔记

| 应用笔记 | 绝对路径 |
|---------|---------|
| QSPI 自定义模式使用 | `D:\Library\10_Datasheets\11_MCU\HC32系列\HC32F4A0\AN_QSPI的自定义模式的使用_Rev1.01` |

## 源文件引用

- **手册 Markdown**: `D:\Library\10_Datasheets\11_MCU\HC32系列\HC32F4A0\31-QSPI-四线式串行外设接口\31-QSPI-四线式串行外设接口.md`
- **手册 PDF**: `D:\Library\10_Datasheets\11_MCU\HC32系列\HC32F4A0\RM_HC32F4A0系列参考手册_Rev1.40.pdf`
