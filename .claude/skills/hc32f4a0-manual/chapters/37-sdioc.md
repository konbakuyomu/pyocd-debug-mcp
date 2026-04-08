# SDIOC — SDIO 控制器

> ✅ 本知识卡已填充。最后更新：2026-03-25

## 模块概述

SDIOC（SD I/O Controller）提供 SD 主机接口和 MMC 主机接口，用于与 SD2.0 协议的 SD 卡/SDIO 设备以及 eMMC4.2 协议的 MMC 设备通信。HC32F4A0 内置 2 个独立 SDIO 控制器（SDIOC1/SDIOC2），可同时与 2 个 SD/MMC/SDIO 设备通信。基于 SD Host Controller Standard Specification 标准设计。

## 关键特性

- **2 个独立控制器**：SDIOC1 + SDIOC2，可同时操作
- **SD 卡支持**：SDSC/SDHC/SDXC 格式 SD 卡及 SDIO 设备
- **MMC 支持**：eMMC4.2 协议，支持 8 位总线
- **总线宽度**：SD 1bit/4bit，MMC 1bit/4bit/8bit
- **SD 时钟**：PCLK1 分频产生，最高 50MHz（高速模式）
- **卡识别和硬件写保护**
- **命令/数据分离**：CMD 线发送命令+接收应答，DATA 线收发数据
- **内置 FIFO**：数据缓冲区加速 CPU/DMA 数据交换
- **DMA 支持**：读/写均可通过 DMA 传输
- **中断**：普通中断（传输完成/缓冲就绪/卡插入移除/卡中断）+ 错误中断（超时/CRC/终止命令等）
- **唤醒**：支持通过卡插入/移除/卡中断唤醒 STOP/Power Down 模式
- **自动 CMD12**：多块传输结束后可自动发送停止命令
- **引脚**：SDIOx_CK、SDIOx_CMD、SDIOx_D[7:0]、SDIOx_CD、SDIOx_WP

## 功能导航大纲

> 小节编号对应原始手册标题

| 区域 | 小节 | 关键内容 |
|------|------|----------|
| 简介 | 38.1 | SDIOC 功能特性总览 |
| 端口分配 | 38.2.1 | CK/CMD/D0~D7/CD/WP 管脚 |
| 基本访问 | 38.2.2 | 寄存器读写顺序，CMD 寄存器最后写 |
| 数据传输 | 38.2.3 | FIFO 缓冲，CPU/DMA 读写流程 |
| SD 时钟 | 38.2.4 | PCLK1 分频，卡识别 ≤400kHz，传输 ≤50MHz |
| 中断和 DMA | 38.2.5 | SD 中断/SDIO 中断/DMA 请求 |
| 卡插拔 | 38.2.5.4 | CD 信号检测，插入/移除中断 |
| 主机初始化 | 38.2.6.1 | 6 步 SDIOC 主机初始化 |
| SD/MMC/SDIO 卡初始化 | 38.2.6.2~4 | CMD0→CMD8→ACMD41→CMD2→CMD3 |
| 单块读写 | 38.2.7 | CMD24(写)/CMD17(读) |
| 多块读写 | 38.2.8 | CMD25(写)/CMD18(读)，自动 CMD12 |
| 终止/挂起/恢复 | 38.2.9 | 异步/同步终止，suspend/resume |
| 读等待 | 38.2.10 | SDIO read wait 机制 |
| 唤醒 | 38.2.11 | STOP/Power Down 唤醒流程 |
| 寄存器 | 38.3 | 30+ 寄存器详述 |

## 寄存器速查

> SDIOC1: 0x4006FC00 | SDIOC2: 0x40070400 | 系统控制: 0x40055404

| 寄存器 | 偏移 | 用途 |
|--------|------|------|
| SDIOC_BLKSIZE | 0x04 | 数据块长度 |
| SDIOC_BLKCNT | 0x06 | 数据块计数 |
| SDIOC_ARG0/ARG1 | 0x08/0x0A | 命令参数 |
| SDIOC_TRANSMODE | 0x0C | 传输模式（读写/单多块/自动CMD12/块计数使能） |
| SDIOC_CMD | 0x0E | 命令寄存器（IDX/TYP/DAT/ICE/CCE/RESTYP） |
| SDIOC_RESP0~7 | 0x10~0x1E | 应答寄存器 |
| SDIOC_BUF0/BUF1 | 0x20/0x22 | 数据缓冲端口 |
| SDIOC_PSTAT | 0x24 | 主机状态（CDL 卡检测） |
| SDIOC_HOSTCON | 0x28 | 主机控制（总线宽度/高速模式） |
| SDIOC_PWRCON | 0x29 | 电源控制 |
| SDIOC_CLKCON | 0x2C | 时钟控制（分频系数） |
| SDIOC_TOUTCON | 0x2E | 超时控制 |
| SDIOC_SFTRST | 0x2F | 软件复位 |
| SDIOC_NORINTST | 0x30 | 普通中断状态 |
| SDIOC_ERRINTST | 0x32 | 错误中断状态 |
| SDIOC_NORINTSTEN | 0x34 | 普通中断状态使能 |
| SDIOC_ERRINTSTEN | 0x36 | 错误中断状态使能 |
| SDIOC_NORINTSGEN | 0x38 | 普通中断信号使能 |
| SDIOC_ERRINTSGEN | 0x3A | 错误中断信号使能 |
| SDIOC_ATCERRST | 0x3C | 自动命令错误状态 |
| SDIOC_SYCTLREG | 0x40055404 | 系统控制（SD/MMC 模式切换） |

## 典型初始化流程

```c
/* 以 SDIOC1 读取 SD 卡为例 */

/* 1. 使能时钟 */
FCG_Fcg1PeriphClockCmd(FCG1_PERIPH_SDIOC1, ENABLE);

/* 2. GPIO 配置 */
/* SDIOx_CK, SDIOx_CMD, SDIOx_D0~D3, SDIOx_CD 设为对应复用功能 */

/* 3. SDIOC 初始化 */
stc_sdioc_init_t stcSdiocInit;
SDIOC_StructInit(&stcSdiocInit);
stcSdiocInit.u32Mode     = SDIOC_MD_SD;         /* SD 模式 */
stcSdiocInit.u8CardDetect = SDIOC_CARD_DETECT_CD_PIN; /* CD 引脚检测 */
stcSdiocInit.u8SpeedMode  = SDIOC_SPEED_MD_HIGH; /* 高速模式 */
stcSdiocInit.u8BusWidth   = SDIOC_BUS_WIDTH_4BIT; /* 4 位总线 */
stcSdiocInit.u16ClockDiv  = SDIOC_CLK_DIV2;      /* 时钟分频 */
SDIOC_Init(CM_SDIOC1, &stcSdiocInit);

/* 4. SD 卡初始化（通过中间件） */
/* SDCARD_Init() / SDIOC_MidwateInit() 完成卡识别和初始化 */

/* 5. 读写数据 */
/* SDCARD_ReadBlocks() / SDCARD_WriteBlocks() */
```

## 常见陷阱与注意事项

1. **写命令寄存器须最后进行**：写 CMD 寄存器会触发 SDIOC 发送命令，之前必须先完成 TRANSMODE/ARG 等配置
2. **卡识别时钟 ≤400kHz**：SD 协议要求卡识别阶段时钟不超过 400kHz，需根据 PCLK1 合理分频
3. **SD 和 MMC 模式切换**：通过 SDIOC_SYCTLREG 控制，两个控制器共用此寄存器
4. **自动 CMD12**：多块传输建议使能自动 CMD12，否则需手动发送 CMD12 结束传输
5. **SDIO 中断需四线模式**：SDIO 卡中断通过 D1 线传输，需在 4bit 模式下才能使用
6. **读等待仅 SDIO**：read wait 功能需要 SDIO 设备支持且需在四线式传输下
7. **挂起恢复需备份寄存器**：挂起后如需恢复，须备份偏移 00h~0Dh 寄存器
8. **DMA 目标地址固定**：使用 DMA 时，BUF0/BUF1 地址必须配置为固定地址模式
9. **8bit 仅 MMC**：八线式通信仅限 MMC 设备，SD 卡最多 4bit

## 官方例程索引

| 例程名 | 绝对路径 | 用途简述 |
|--------|---------|--------:|
| sdioc_sd | `$EXAMPLES\sdioc\sdioc_sd` | SD 卡读写演示 |
| sdioc_mmc | `$EXAMPLES\sdioc\sdioc_mmc` | MMC 卡读写演示 |
| sdioc_sdio | `$EXAMPLES\sdioc\sdioc_sdio` | SDIO 设备通信演示 |

> `$EXAMPLES` = `D:\Dev\SDKs\HC32\HC32F4A0\HC32F4A0_DDL_Rev2.4.0\projects\ev_hc32f4a0_lqfp176\examples`
>
> SDIOC 中间件：`D:\Dev\SDKs\HC32\HC32F4A0\HC32F4A0_DDL_Rev2.4.0\midwares\hc32\sdioc\`

## 相关应用笔记

| 笔记名 | 路径 | 关键内容 |
|--------|------|----------|
| 基于 SDIO 的 FatFS 文件系统移植 | `$MANUAL\AN_HC32F4A0系列的基于SDIO的FatFS文件系统移植_Rev1.1\AN_HC32F4A0系列的基于SDIO的FatFS文件系统移植_Rev1.1.md` | FatFS 移植步骤、sd_diskio 驱动接口和文件读写验证 |

> `$MANUAL` = `D:\Library\10_Datasheets\11_MCU\HC32系列\HC32F4A0`

## 源文件引用

- **手册 Markdown**: `D:\Library\10_Datasheets\11_MCU\HC32系列\HC32F4A0\37-SDIOC-SDIO控制器\37-SDIOC-SDIO控制器.md`
- **手册 PDF**: `D:\Library\10_Datasheets\11_MCU\HC32系列\HC32F4A0\RM_HC32F4A0系列参考手册_Rev1.40.pdf`
