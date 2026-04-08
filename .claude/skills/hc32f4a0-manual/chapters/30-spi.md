# SPI — 串行外设接口

> ✅ 本知识卡已填充。最后更新：2026-03-25

## 模块概述

HC32F4A0 搭载 6 个独立 SPI 通道（SPI1~SPI6），支持 4 线式 SPI 模式（SCK/MOSI/MISO/SS0~3）和 3 线式时钟同步运行模式（仅 SCK/MOSI/MISO），主机/从机可选。每通道配备 4 根片选线（SS0~SS3），支持全双工同步传输和只发送模式。数据宽度可选 4~32 位（16 档），支持 MSB/LSB 优先、奇偶校验、双缓冲（TX_BUFF→shifter→RX_BUFF）、通信自动挂起（CSUSPE）、模式故障/过载/欠载/奇偶校验错误检测。主机波特率为 PCLK1 的 2~256 分频，从机最大允许 PCLK1/6。SPI1~3 时钟来自 PCLK1，SPI4~6 时钟来自 PCLK1。

## 关键特性

- 6 个独立通道，主机/从机可选，全双工 + 只发送模式
- **4 线式 SPI**：SCK + MOSI + MISO + SS0~SS3（4 路片选，极性可调）
- **3 线式时钟同步**：仅 SCK + MOSI + MISO，SS 释放作通用 IO
- 数据宽度：4/5/6/7/8/9/10/11/12/13/14/15/16/20/24/32 位（DSIZE[3:0]）
- 单次最多传送 4 帧（FTHLV[1:0]），16 字节数据缓冲区
- MSB/LSB 优先可选，奇/偶校验可选
- 主机波特率：PCLK1/2 ~ PCLK1/256（MBR[2:0]，8 档分频）
- 从机最大波特率：PCLK1/6
- SCK 极性（CPOL）+ 相位（CPHA）：4 种 SPI Mode 组合
- 片选时序控制：SCK 延迟（MSSI）、SS 无效延迟（MSSDL）、下次存取延迟（MIDI）
- 通信自动挂起（CSUSPE）：主接收模式下 RX_BUFF 满时自动暂停 SCK
- 错误检测：模式故障（MODFERF）、过载（OVRERF）、欠载（UDRERF）、奇偶校验（PERF）
- 回环自测（SPLPBK / SPLPBK2）
- 中断：TX 空（SPTI）、RX 满（SPRI）、错误（SPEI）、空闲（SPII）；传输完成（仅事件源）

## 功能导航大纲

> 小节编号对应原始手册 `30-SPI-串行外设接口.md` 中的 31.x 标题。

| 区域 | 小节 | 关键内容 |
|------|------|----------|
| 概述 | 31.1-31.3 | 特性总述、系统框图、引脚说明（SCK/MOSI/MISO/SS0~3） |
| **管脚状态** | 31.4 | 主机/从机在 SPI/时钟同步模式下的引脚方向（CMOS/OD/Hi-Z） |
| 波特率 | 31.5.1 | PCLK1/(2^(N+1))，N=MBR[2:0] |
| **数据格式** | 31.5.2 | DSIZE 宽度、MSB/LSB、奇偶校验位位置 |
| 传送格式 | 31.5.3 | CPHA=0/1 的采样/更新时序 |
| 通信方式 | 31.5.4 | 全双工（TXMDS=0）vs 只发送（TXMDS=1） |
| **SPI 主机** | 31.6.2 | 4 线主机动作、初始化 10 步、片选时序控制 |
| SPI 从机 | 31.6.3 | SS0 触发、CPHA=0 需 SS 电平变化 |
| 时钟同步主机 | 31.6.4 | 3 线主机动作，无 SS |
| 时钟同步从机 | 31.6.5 | 3 线从机，CPHA 只能为 1 |
| 自动挂起 | 31.6.6 | CSUSPE=1，RX_BUFF 满时暂停 SCK |
| 错误检测 | 31.7-31.10 | 模式故障/过载/欠载/奇偶校验 |
| 中断 | 31.11 | SPTI/SPRI/SPEI/SPII 四类中断 |
| 寄存器 | 31.12 | 5 个寄存器 |

## 寄存器速查

> SPI1: 0x4001C000, SPI2: 0x4001C400, SPI3: 0x4001C800, SPI4: 0x40020000, SPI5: 0x40020400, SPI6: 0x40020800

| 寄存器 | 偏移 | 用途 | 关键位字段 |
|--------|------|------|-----------|
| SPI_DR | 0x00 | 数据寄存器 | SPD[31:0]（读=RX_BUFF，写=TX_BUFF） |
| **SPI_CR1** | 0x04 | 控制寄存器 | **SPE[6]** **MSTR[3]** SPIMDS[0] TXMDS[1] RXIE[10] TXIE[9] EIE[8] IDIE[11] PAE[15] CSUSPE[7] SPLPBK[4] MODFE[12] |
| **SPI_CFG1** | 0x0C | 配置 1 | FTHLV[1:0] SS0~3PV[8:11] **MSSI[22:20]** MSSDL[26:24] MIDI[30:28] |
| SPI_SR | 0x14 | 状态寄存器 | **RDFF[7]** **TDEF[5]** OVRERF[0] MODFERF[2] PERF[3] UDRERF[4] IDLNF[1] |
| **SPI_CFG2** | 0x18 | 配置 2 | **MBR[4:2]** **CPOL[1]** **CPHA[0]** DSIZE[11:8] LSBF[12] SSA[7:5] MSSIE[15] MSSDLE[14] MIDIE[13] |

## 典型初始化流程

```c
/* === SPI Master 轮询全双工（8bit, Mode1, 64分频） === */
// 1. 使能时钟
FCG_Fcg1PeriphClockCmd(FCG1_PERIPH_SPI6, ENABLE);

// 2. 配置 GPIO 复用
GPIO_SetFunc(GPIO_PORT_E, GPIO_PIN_06, GPIO_FUNC_49); // SPI6_SS0
GPIO_SetFunc(GPIO_PORT_E, GPIO_PIN_03, GPIO_FUNC_46); // SPI6_SCK
GPIO_SetFunc(GPIO_PORT_E, GPIO_PIN_04, GPIO_FUNC_47); // SPI6_MOSI
GPIO_SetFunc(GPIO_PORT_E, GPIO_PIN_05, GPIO_FUNC_48); // SPI6_MISO

// 3. 初始化 SPI
stc_spi_init_t stcSpiInit;
SPI_StructInit(&stcSpiInit);
stcSpiInit.u32WireMode     = SPI_4_WIRE;
stcSpiInit.u32TransMode    = SPI_FULL_DUPLEX;
stcSpiInit.u32MasterSlave  = SPI_MASTER;
stcSpiInit.u32SpiMode      = SPI_MD_1;         // CPOL=0, CPHA=1
stcSpiInit.u32BaudRatePrescaler = SPI_BR_CLK_DIV64;
stcSpiInit.u32DataBits     = SPI_DATA_SIZE_8BIT;
stcSpiInit.u32FirstBit     = SPI_FIRST_MSB;
stcSpiInit.u32FrameLevel   = SPI_1_FRAME;
SPI_Init(CM_SPI6, &stcSpiInit);

// 4. 使能 SPI
SPI_Cmd(CM_SPI6, ENABLE);

// 5. 阻塞式全双工收发
SPI_TransReceive(CM_SPI6, txBuf, rxBuf, len, 0x20000000UL);
```

## 常见陷阱与注意事项

1. ⚠️ **时钟同步从机 CPHA 只能为 1**：3 线式时钟同步从机模式不支持 CPHA=0，否则无法正常传输
2. ⚠️ **从机模式 CPHA=0 需 SS 电平变化触发**：SS0 输入信号从无效→有效才触发传输开始，不能将 SS0 固定为有效电平
3. ⚠️ **从机最大速率 PCLK1/6**：不是 PCLK1/2，超过此速率会出错
4. ⚠️ **只发送模式下无接收功能**：TXMDS=1 时 RDFF 始终为 0，不检测过载/奇偶校验错误
5. ⚠️ **切换只发送模式前清 RDFF 和 OVRERF**：确保 RX_BUFF 无残留数据和过载标志
6. ⚠️ **GPIO 需设 CMOS 输入 + 高驱动力**：SPI 引脚须通过 GPIO PCR 设为 PIN_IN_TYPE_CMOS 和 PIN_HIGH_DRV
7. ⚠️ **3 线模式须禁用 ModeFault 检测**：SPIMDS=1 时无 SS 输入，MODFE 必须置 0
8. ⚠️ **中断模式下 RX 优先级应高于 TX**：防止 RX_BUFF 过载，RX 中断优先级建议比 TX 高一级
9. ⚠️ **DMA 事件源需通过 AOS 关联**：SPI TX/RX 事件源绑定 DMA 通道前须使能 FCG0_PERIPH_AOS
10. ⚠️ **写 DR 前必须等 TDEF=1**：TX_BUFF 满时写入会被忽略；读 DR 前必须等 RDFF=1

## 官方例程索引

| 例程名 | 绝对路径 | 用途简述 |
|--------|---------|---------|
| spi_polling | `$EXAMPLES\spi\spi_polling` | SPI 轮询全双工收发（最简模式，SPI_TransReceive） |
| spi_int | `$EXAMPLES\spi\spi_int` | SPI 中断收发（TX 空 + RX 满中断逐字节驱动） |
| spi_dma | `$EXAMPLES\spi\spi_dma` | SPI DMA 收发（DMA1_CH0 TX + DMA1_CH1 RX + AOS 事件触发） |
| spi_write_read_flash | `$EXAMPLES\spi\spi_write_read_flash` | W25Q64 Flash 读写（3 线模式，GPIO 软件 CS，SPI_Trans + SPI_Receive） |

> `$EXAMPLES` = `D:\Dev\SDKs\HC32\HC32F4A0\HC32F4A0_DDL_Rev2.4.0\projects\ev_hc32f4a0_lqfp176\examples`

## 相关应用笔记

| 笔记名 | 路径 | 关键内容 |
|--------|------|----------|
| SPI 应用笔记 | `$MANUAL\AN_HC32F4A0系列的串行外设接口SPI__Rev1.1\AN_HC32F4A0系列的串行外设接口SPI_Rev1.1.md` | SPI 模式配置、管脚连接、应用代码与工作流程 |

> `$MANUAL` = `D:\Library\10_Datasheets\11_MCU\HC32系列\HC32F4A0`

## 源文件引用

- **手册 Markdown**: `D:\Library\10_Datasheets\11_MCU\HC32系列\HC32F4A0\30-SPI-串行外设接口\30-SPI-串行外设接口.md`
- **手册 PDF**: `D:\Library\10_Datasheets\11_MCU\HC32系列\HC32F4A0\RM_HC32F4A0系列参考手册_Rev1.40.pdf`
