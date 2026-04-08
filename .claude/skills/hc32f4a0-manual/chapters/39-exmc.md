# EXMC — 外部存储器控制器

> ✅ 本知识卡已填充。最后更新：2026-03-25

## 模块概述

EXMC (External Memory Controller) 用于访问各种片外存储器，将内部 AHB 协议转换为外部存储器专用接口。内部划分三个独立子控制器：SMC（SRAM/PSRAM/NOR Flash）、DMC（SDRAM）、NFC（NAND Flash）。通过端口 MUX 逻辑共享引脚，**同一时刻只能访问一个外部器件**。外部存储器空间总计 1GB（SMC 512MB + DMC 128MB + NFC 1MB + QSPI 128MB）。

## 关键特性

- 三子控制器：SMC（静态存储器）、DMC（动态存储器）、NFC（NAND Flash）
- 支持 SRAM、PSRAM、NOR Flash、SDRAM、NAND Flash（SLC/MLC，ONFI 协议）
- 数据总线宽度：SMC/DMC 支持 16/32 位，NFC 支持 8/16 位
- AHB 与存储器位宽不匹配时自动分割传输 + 字节选择控制（BLS/DQM）
- SMC：同步/异步读写可选，地址数据线复用，可编程突发长度，PSRAM 自动刷新
- DMC：行/Bank 边界自动管理，可编程自动刷新/自刷新，CKE/CLK 空闲自动关断
- NFC：页大小 2K/4K/8K，1-bit 汉明码 ECC + 4-bit BCH ECC 硬件计算
- 各子控制器独立低功耗状态管理
- 每个子控制器独立使能（SMC_ENAR/DMC_ENAR/NFC_ENAR），挂在 FCG3

## 功能导航大纲

> 小节编号对应原始手册 `39-EXMC-外部存储器控制器.md` 中的标题。

| 区域 | 小节 | 关键内容 |
|------|------|----------|
| 概述 | 40.1-40.2 | 架构框图、功能列表、基本访问规范（AHB 与 MEM 位宽匹配表） |
| **地址映射** | 40.2.4 | SMC 4xChip 512MB、DMC 4xChip 128MB、NFC 64KB；CS 空间大小可编程 |
| 协议接口 | 40.2.5 | SMC/DMC/NFC 各自信号定义、EXMC 端口复用分配表 |
| **SMC 功能** | 40.3.1 | 初始设定流程、同步/异步读写时序、地址数据复用、突发、FIFO、低功耗 |
| **DMC 功能** | 40.3.2 | SDRAM Bank/行激活/预充电/刷新、初始设定流程、命令真值表、FIFO、低功耗 |
| **NFC 功能** | 40.3.3 | ONFI 命令表、Page Read/Write/Erase/Reset/ReadID 操作流程、ECC |
| 中断 | 40.4 | NFC 专用：ECC 计算完成、ECC 错误、RB 上升沿（设备就绪） |
| 寄存器-SMC | 40.5.1 | SMC_ENAR/STSR/CMDR/STCR/RFTR/BACR/CSCR/CPCR/CPSR/TMCR 等 20 个 |
| 寄存器-DMC | 40.5.2 | DMC_ENAR/STSR/CMDR/STCR/RFTR/BACR/CSCR/CPCR + 14 个时序寄存器 |
| 寄存器-NFC | 40.5.3 | NFC_ENAR/STSR/STCR/DATR/CMDR/IDXR/BACR/IENR/ISTR/TMCR/ECCR 等 16 个 |

## 寄存器速查

> BASE: SMC=0x88000000, DMC=0x88000400, NFC=0x88100000; 使能寄存器统一在 0x4005540C

| 寄存器 | 偏移 | 用途 | 关键位字段 |
|--------|------|------|-----------|
| SMC_ENAR | (0x4005540C) | SMC 使能 | SMCEN[1] |
| **SMC_CPCR** | 0x0018 | Chip 配置（写入型） | MW[9:8] RSYN[0] WSYN[4] RBL[3:1] WBL[7:5] ADV[11] BLS[12] |
| SMC_TMCR | 0x0014 | 时序配置（写入型） | T_RC/T_WC/T_CEOE/T_WP/T_PC/T_TR |
| SMC_BACR | 0x0200 | 基本控制 | CKSEL[15:14] MUXMD[4]（地址数据复用） |
| SMC_CSCR0/1 | 0x0208/0x020C | 片选地址掩码/匹配 | ADDMSK[7:0] ADDMAT[7:0] |
| DMC_ENAR | (0x4005540C) | DMC 使能 | DMCEN |
| **DMC_CPCR** | 0x000C | Chip 配置 | DMCMW[1:0] BURST COL ROW CKSTOP CKEDIS |
| DMC_RFTR | 0x0010 | 刷新周期 | REFPRD |
| DMC_STCR | 0x0004 | 状态控制（Go/Pause/Sleep/Wakeup） | STCTL[2:0] |
| DMC_TMCR_* | 0x0014~0x0048 | 14 个时序寄存器 | T_CASL/T_RAS/T_RC/T_RCD/T_RFC/T_RP/T_WR 等 |
| DMC_CSCR0~3 | 0x0200~0x020C | 片选地址配置 | ADDMSK/ADDMAT/ADDDEC |
| NFC_ENAR | (0x4005540C) | NFC 使能 | NFCEN |
| **NFC_BACR** | 0x8054 | 基础配置 | PAGE_SIZE MW BANK ECCM ROWADDR WP CAPACITY |
| NFC_CMDR | 0x8000 | 命令寄存器 | CMD + BANK + ARG |
| NFC_TMCR0~2 | 0x804C~0x805C | 时序配置 | TS/TWP/TRP/TH/TWH/TRH/TRR/TWB/TCCS/TWTR/TRTW/TADL |

## 典型初始化流程

```c
/* === SMC — 外部 SRAM 示例 (IS62WV51216) === */
// 1. 使能时钟
FCG_Fcg3PeriphClockCmd(FCG3_PERIPH_SMC, ENABLE);
CLK_SetClockDiv(CLK_BUS_EXCLK, CLK_EXCLK_DIV8); // EXCLK=30MHz

// 2. 配置 GPIO（所有 EXMC 引脚: 高驱动 + GPIO_FUNC_12）
GPIO_SetFunc(port, pin, GPIO_FUNC_12);

// 3. 使能 SMC 并退出低功耗
EXMC_SMC_Cmd(ENABLE);
EXMC_SMC_ExitLowPower();
while (EXMC_SMC_READY != EXMC_SMC_GetStatus()) {}

// 4. 配置 Chip + 时序
EXMC_SMC_StructInit(&stcSmcInit);
stcSmcInit.stcChipConfig.u32MemoryWidth = EXMC_SMC_MEMORY_WIDTH_16BIT;
stcSmcInit.stcChipConfig.u32ReadMode    = EXMC_SMC_READ_ASYNC;
stcSmcInit.stcChipConfig.u32WriteMode   = EXMC_SMC_WRITE_ASYNC;
stcSmcInit.stcTimingConfig.u8RC = 4; stcSmcInit.stcTimingConfig.u8WC = 4;
EXMC_SMC_Init(EXMC_SMC_CHIP2, &stcSmcInit);
EXMC_SMC_SetCommand(EXMC_SMC_CHIP2, EXMC_SMC_CMD_UPDATEREGS, 0, 0);

// 5. 直接指针访问 (起始地址由 CS 空间决定)
*(uint16_t *)0x60000000 = 0x1234;

/* === DMC — SDRAM 示例 (IS42S16400J7TLI) === */
// 1. 使能时钟
FCG_Fcg3PeriphClockCmd(FCG3_PERIPH_DMC, ENABLE);
EXMC_DMC_Cmd(ENABLE);

// 2. 配置 DMC（列/行/突发/刷新/时序）
EXMC_DMC_Init(&stcDmcInit);
EXMC_DMC_ChipConfig(EXMC_DMC_CHIP1, &stcCsConfig);

// 3. SDRAM 初始化命令序列
EXMC_DMC_SetCommand(chip, bank, EXMC_DMC_CMD_NOP, 0);
EXMC_DMC_SetCommand(chip, bank, EXMC_DMC_CMD_PRECHARGE_ALL, 0);
EXMC_DMC_SetCommand(chip, bank, EXMC_DMC_CMD_AUTO_REFRESH, 0); // x2
EXMC_DMC_SetCommand(chip, bank, EXMC_DMC_CMD_MDREG_CONFIG, mdRegVal);

// 4. 切换至 Ready 状态
EXMC_DMC_SetState(EXMC_DMC_CTRL_STATE_GO);
EXMC_DMC_SetState(EXMC_DMC_CTRL_STATE_WAKEUP);
EXMC_DMC_SetState(EXMC_DMC_CTRL_STATE_GO);
while (EXMC_DMC_CURR_STATUS_RDY != EXMC_DMC_GetStatus()) {}

// 5. 直接指针访问
*(uint32_t *)0x80000000 = 0xDEADBEEF;
```

## 常见陷阱与注意事项

1. ⚠️ **SMC 双缓冲机制**：`EXMC_SMC_Init()` 写入 shadow 寄存器，必须执行 `EXMC_SMC_SetCommand(chip, EXMC_SMC_CMD_UPDATEREGS, 0, 0)` 才能生效
2. ⚠️ **EXCLK 频率限制**：EXCLK 配置频率不得超过 40MHz（SMC BACR.CKSEL 说明），所有时序参数以 EXCLK 为基准计算
3. ⚠️ **DMC 状态机顺序**：Config → Go → Wakeup → Go → Ready，不可跳步
4. ⚠️ **SDRAM 上电初始化**：必须严格执行 NOP → PrechargeAll → AutoRefresh ×2 → ModeRegConfig → NOP 序列
5. ⚠️ **SMC 复位后为 Low Power 状态**：必须先调 `EXMC_SMC_ExitLowPower()` 并等待 Ready
6. ⚠️ **EXMC 端口共享**：SMC/DMC/NFC 共享同一组物理引脚，同一时刻只能访问一种外部存储器
7. ⚠️ **GPIO 必须高驱动**：所有 EXMC 引脚需配置 `PIN_HIGH_DRV` + `GPIO_FUNC_12`
8. ⚠️ **NFC ECC 读取顺序**：Page Read 完数据后必须先写 0x23 命令触发 ECC 计算，再写 0xFE 结束操作
9. ⚠️ **DMC/SMC 切换使用**：两者共享部分引脚，运行时切换需注意重新初始化（参见 AN 笔记）
10. ⚠️ **NFC 写保护**：WP 引脚需初始化时拉高以解除 NAND Flash 写保护

## 官方例程索引

| 例程名 | 绝对路径 | 用途简述 |
|--------|---------|---------|
| exmc_dmc_sdram_is42s16400j7tli | `$EXAMPLES\exmc\exmc_dmc_sdram_is42s16400j7tli` | DMC 驱动 SDRAM（16bit），8/16/32 位读写校验 |
| exmc_dmc_sdram_is42s16400j7tli_dma | `$EXAMPLES\exmc\exmc_dmc_sdram_is42s16400j7tli_dma` | DMC + DMA 方式访问 SDRAM |
| exmc_nfc_nandflash_mt29f2g08ab | `$EXAMPLES\exmc\exmc_nfc_nandflash_mt29f2g08ab` | NFC 驱动 NAND Flash，含 1-bit/4-bit ECC 读写校验 |
| exmc_sdram_sram | `$EXAMPLES\exmc\exmc_sdram_sram` | DMC 与 SMC 运行时切换访问 SDRAM+SRAM |
| exmc_smc_lcd_nt35510 | `$EXAMPLES\exmc\exmc_smc_lcd_nt35510` | SMC 驱动 TFT LCD（8080 接口） |
| exmc_smc_sram_is62wv51216 | `$EXAMPLES\exmc\exmc_smc_sram_is62wv51216` | SMC 驱动外部 SRAM（16bit），8/16/32 位读写校验 |
| exmc_smc_sram_is62wv51216_dma | `$EXAMPLES\exmc\exmc_smc_sram_is62wv51216_dma` | SMC + DMA 方式访问外部 SRAM |

> `$EXAMPLES` = `D:\Dev\SDKs\HC32\HC32F4A0\HC32F4A0_DDL_Rev2.4.0\projects\ev_hc32f4a0_lqfp176\examples`

## 相关应用笔记

| 笔记名 | 路径 | 关键内容 |
|--------|------|----------|
| EXMC 使用指南 | `$MANUAL\AN_HC32F4A0系列的外部存储器控制器EXMC__Rev1.1` | SMC/DMC/NFC 完整使用说明和配置示例 |
| DMC 和 SMC 切换使用 | `$MANUAL\AN_HC32F4A0系列的EXMC_DMC和SMC切换使用_Rev1.00` | 运行时 DMC↔SMC 切换的方法和注意事项 |

> `$MANUAL` = `D:\Library\10_Datasheets\11_MCU\HC32系列\HC32F4A0`

## 源文件引用

- **手册 Markdown**: `D:\Library\10_Datasheets\11_MCU\HC32系列\HC32F4A0\39-EXMC-外部存储器控制器\39-EXMC-外部存储器控制器.md`
- **手册 PDF**: `D:\Library\10_Datasheets\11_MCU\HC32系列\HC32F4A0\RM_HC32F4A0系列参考手册_Rev1.40.pdf`
