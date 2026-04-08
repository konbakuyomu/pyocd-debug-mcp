# SRAM — 内置 SRAM

> ✅ 本知识卡已填充。最后更新：2026-03-25

## 模块概述

HC32F4A0 内置 512KB 系统 SRAM + 4KB 备份 SRAM，分为 6 个区域：SRAMH（128KB 高速）、SRAM1/2（各 128KB）、SRAM3（96KB）、SRAM4（32KB ECC）、SRAMB（4KB 备份 ECC）。SRAMH 经 AHBH 总线直连 CPU，240MHz 下可 0 等待访问。SRAM4 和 SRAMB 支持 ECC 纠一检二校验，其余区域支持奇偶校验。SRAMB 在 Power Down 模式下可保持数据。

## 关键特性

- 总计 516KB：SRAMH 128KB + SRAM1 128KB + SRAM2 128KB + SRAM3 96KB + SRAM4 32KB + SRAMB 4KB
- SRAMH 240MHz 0 等待访问（经 AHBH 高速总线），适合放 DMA 缓冲、中断向量表
- SRAM1/2/3/H：奇偶校验（Even-parity check），每字节 1 位校验位
- SRAM4/SRAMB：ECC 校验，纠一检二（纠正 1-bit 错误，检测 2-bit 错误）
- 所有 SRAM 可独立配置读/写等待周期（0~7 wait）
- 校验错误可触发 NMI 中断或系统复位（可选）
- SRAMB 在 Power Down 模式保持数据（需初始化 VBAT 域）
- CACHE RAM 也有奇偶校验（CKSR.CACHERAMYPERR 标志）

## 功能导航大纲

> 小节编号对应原始手册 `kuma_HC32F4A0手册_SRAM.md` 中的标题。

| 区域 | 小节 | 关键内容 |
|------|------|----------|
| 概述 | 8.1 | SRAM 空间分配表、地址范围、等待周期与频率关系 |
| **等待控制** | 8.2.1 | SRAM_WTCR：各区域独立读/写等待周期配置 |
| 等待保护 | 8.2.2 | SRAM_WTPR：写关键码 0x3B 解锁 WTCR |
| **校验控制** | 8.2.3 | SRAM_CKCR：ECC 模式（4 档）、奇偶/ECC 出错操作（NMI/复位） |
| 校验保护 | 8.2.4 | SRAM_CKPR：写关键码 0x3B 解锁 CKCR |
| **校验状态** | 8.2.5 | SRAM_CKSR：各区域错误标志，写 1 清零 |

## 寄存器速查

> BASE_ADDR: 0x40050800

| 寄存器 | 地址 | 用途 | 关键位字段 |
|--------|------|------|-----------|
| **SRAM_WTCR** | 0x40050800 | 等待周期控制 | SRAM123RWT[2:0], SRAM123WWT[6:4], SRAM4RWT[10:8], SRAM4WWT[14:12], SRAMHRWT[18:16], SRAMHWWT[22:20], SRAMBKRWT[26:24], SRAMBKWWT[30:28] |
| SRAM_WTPR | 0x40050804 | 等待保护 | WTPRC[0]（写 1 使能 WTCR 写入），WTPRKW[7:1]（关键码写 0x3B） |
| **SRAM_CKCR** | 0x40050808 | 校验控制 | PYOAD[0]（奇偶出错操作 0=NMI/1=RST），ECCOAD[16]（SRAM4 ECC 出错操作），BECCOAD[17]（SRAMB ECC 出错操作），ECCMOD[25:24]（SRAM4 ECC 模式），BECCMOD[27:26]（SRAMB ECC 模式） |
| SRAM_CKPR | 0x4005080C | 校验保护 | CKPRC[0]（写 1 使能 CKCR 写入），CKPRKW[7:1]（关键码写 0x3B） |
| **SRAM_CKSR** | 0x40050810 | 校验状态 | SRAM1PYERR[0], SRAM2PYERR[1], SRAM3PYERR[2], SRAMHPYERR[3], SRAM41ERR[4], SRAM42ERR[5], SRAMB1ERR[6], SRAMB2ERR[7], CACHERAMPYERR[8]（写 1 清零） |

## SRAM 地址分配

| 名称 | 容量 | 地址范围 | 校验方式 | 240MHz 最少等待 |
|------|------|----------|---------|----------------|
| SRAMH | 128KB | 0x1FFE0000~0x1FFFFFFF | 奇偶校验 | 0 wait |
| SRAM1 | 128KB | 0x20000000~0x2001FFFF | 奇偶校验 | 0 wait |
| SRAM2 | 128KB | 0x20020000~0x2003FFFF | 奇偶校验 | 0 wait |
| SRAM3 | 96KB | 0x20040000~0x20057FFF | 奇偶校验 | 0 wait |
| SRAM4 | 32KB | 0x20058000~0x2005FFFF | ECC | 0 wait |
| SRAMB | 4KB | 0x200F0000~0x200F0FFF | ECC | 1 wait |

## 典型初始化流程

```c
/* === SRAM 等待周期 + 校验配置 === */
// 1. 解除写保护
LL_PERIPH_WE(LL_PERIPH_SRAM);

// 2. 初始化等待周期（DDL 默认配置）
SRAM_Init();  // 根据 hclk 自动设置各区域等待周期

// 3. 配置校验出错操作（NMI 或 复位）
SRAM_SetExceptionType(SRAM_CHECK_SRAMH_1_2_3, SRAM_EXP_TYPE_NMI);
// 或 SRAM_EXP_TYPE_RST

// 4. 配置 ECC 模式（若用 SRAM4/SRAMB）
SRAM_SetEccMode(SRAM_ECC_SRAM4, SRAM_SRAM4_ECC_MD3);
// MD1: 纠错不报标志  MD2: 纠错报1-bit标志  MD3: 纠错报所有标志+中断

// 5. 注册 NMI 中断
stc_nmi_init_t stcNmiInit;
stcNmiInit.u32Src = NMI_SRC_SRAM_PARITY;  // 或 NMI_SRC_SRAM_ECC
(void)NMI_Init(&stcNmiInit);

// 6. 恢复写保护
LL_PERIPH_WP(LL_PERIPH_SRAM);
```

## 常见陷阱与注意事项

1. ⚠️ **使能校验前必须初始化 SRAM**：奇偶/ECC 使能后，读取未初始化的 SRAM 地址会立即触发 NMI 或复位。必须先以字（32-bit）为单位清零所用区域
2. ⚠️ **SRAMH 执行指令需额外初始化**：从 SRAMH 执行代码时，需初始化所用 RAM 空间 + 额外 3 个字的区域（CPU 预取指）
3. ⚠️ **ECC 使能时仅支持 32-bit 写**：SRAM4/SRAMB 开启 ECC 后，必须以 32-bit 写入，字节/半字写会导致 ECC 校验位不正确
4. ⚠️ **SRAMB 使用前需初始化 VBAT 域**：参考 PWC 章节的"电池备份电源域"初始化流程
5. ⚠️ **SRAM1/2/3 在 240MHz 下需 0 wait 但 SRAMB 需 1 wait**：SRAMB 在 >120MHz 时必须至少 1 wait
6. ⚠️ **WTCR/CKCR 写保护**：修改等待/校验寄存器前须先向 WTPR/CKPR 写关键码 0x3B 解锁
7. ⚠️ **NMI_Handler 需加 `__DSB()`**：Arm Errata 838869，NMI 处理完成前需 DSB 指令保证写入完成

## 官方例程索引

| 例程名 | 绝对路径 | 用途简述 |
|--------|---------|---------|
| sram_error_check | `$EXAMPLES\sram\sram_error_check` | SRAM 校验演示：奇偶校验 + ECC 校验错误检测，NMI 中断处理 |

> `$EXAMPLES` = `D:\Dev\SDKs\HC32\HC32F4A0\HC32F4A0_DDL_Rev2.4.0\projects\ev_hc32f4a0_lqfp176\examples`

## 源文件引用

- **手册 Markdown**: `D:\Library\10_Datasheets\11_MCU\HC32系列\HC32F4A0\7-SRAM-内置SRAM\kuma_HC32F4A0手册_SRAM.md`
- **手册 PDF**: `D:\Library\10_Datasheets\11_MCU\HC32系列\HC32F4A0\RM_HC32F4A0系列参考手册_Rev1.40.pdf`
