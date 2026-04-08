# EFM — 嵌入式 FLASH

> ✅ 本知识卡已填充。最后更新：2026-03-25

## 模块概述

HC32F4A0 内置最大 2MB 嵌入式 FLASH，由两块独立 1MB FLASH 构成 dual bank，支持 BGO（后台操作）。编程单位 4 字节，擦除单位 8KB（扇区），共 256 个扇区。提供 ICODE/DCODE 缓存加速（5KB 缓存空间）、16 字节指令预取、134KB OTP 区域、引导交换、4 级数据安全保护和 D-BUS 读保护。

## 关键特性

- 2MB 容量 = 2×1MB dual bank，支持 BGO（擦写一块时另一块可执行代码）
- 256 个扇区，每扇区 8KB；编程 4 字节对齐，128 位宽读取
- ICODE 缓存 4KB（256×128bit）+ DCODE 缓存 1KB（64×128bit），LRU 替换策略
- 16 字节 ICODE 预取指加速
- 3 种编程模式：单编程、单编程回读、连续编程（节省 50%+ 时间）
- 擦除：扇区擦除 + 单块全擦除 + 双块全擦除
- 134KB OTP（One Time Program）：16×8KB + 2×2KB + 4×256B + 32×16B + 128×4B
- 引导交换：写 0x0300_2000 = 0x5A5A5A 后 FLASH0 与 FLASH1 地址互换
- 4 级安全保护（Level 0~3），防调试/ISP/测试接口读取
- D-BUS 读保护：ICG3.DBUSPRT=0x4450 使能，保护 0~128KB 区域
- 每扇区独立写保护 + 写保护锁定（WLOCK 一旦置 1 仅复位可恢复）
- CHIPID（0x484404A0）+ 96 位 Unique ID（LOT + Wafer + XY 坐标）
- 3 个中断源：PE 错误、读写冲突、操作结束

## 功能导航大纲

> 小节编号对应原始手册 `6-EFM-嵌入式FLASH.md` 中的标题，可直接搜索定位。

| 区域 | 小节 | 关键内容 |
|------|------|----------|
| 概述 | 7.1-7.3 | 简介、主要特性、FLASH 地址分布（2MB/1MB 单/双 FLASH） |
| **读接口** | 7.4 | CPU 频率与 FLWT 等待周期对照表（核心！调频必须先改 FLWT） |
| **缓存加速** | 7.5 | ICACHE/DCACHE 使能、缓冲命中/不命中周期数 |
| 编程擦除-解锁 | 7.6.1 | EFM_FAPRT 解锁序列 + EFM_KEY1 解锁序列 |
| 编程擦除-写保护 | 7.6.2 | F0/1NWPRTx 扇区保护、WLOCK 锁定 |
| **单编程** | 7.6.3-7.6.4 | 无回读模式（PEMOD=001）、回读模式（PEMOD=010） |
| **连续编程** | 7.6.5 | PEMOD=011，写间隔不超 16μs，结束后立即退出 |
| **擦除** | 7.6.6-7.6.7 | 扇区擦除（PEMOD=100）、全擦除（101/110） |
| 数据安全保护 | 7.6.8 | Level 0~3，保护地址/写入值/叠加规则 |
| D-BUS 读保护 | 7.6.9 | ICG3.DBUSPRT=0x4450，128KB 区域保护 |
| **BGO** | 7.6.10 | BUSHLDCTL=1 释放总线，跨块编程擦除 |
| 中断 | 7.6.11 | EFM_PEERR / EFM_COLERR / EFM_OPTEND |
| **OTP** | 7.7 | OTP 地址分布表、KEY2 解锁、锁存操作流程 |
| **引导交换** | 7.8 | 0x0300_2000 写 0x5A5A5A、OTP 启用/未启用地址变换规则 |
| 寄存器 | 7.9 | EFM_FAPRT/KEY1/KEY2/FSTP/FRMC/FWMC/FSR/FSCLR/FITE 等 23 个 |
| 注意事项 | 7.10 | 擦写中复位数据丢失、禁止重复编程、连续编程禁低功耗等 |

## 寄存器速查

> BASE_ADDR: 0x40010400

| 寄存器 | 偏移 | 用途 | 关键位字段 |
|--------|------|------|-----------|
| EFM_FAPRT | 0x00 | 访问写保护 | FAPRT[15:0]（先写 0x0123 再写 0x3210 解锁） |
| EFM_KEY1 | 0x04 | 密钥 1（解锁 FWMC） | 先写 0x01234567 再写 0xFEDCBA98 |
| EFM_KEY2 | 0x08 | 密钥 2（解锁 OTP 锁存） | 先写 0x10325476 再写 0xEFCDAB89 |
| EFM_FSTP | 0x14 | FLASH 停止控制 | F1STP[1], F0STP[0] |
| **EFM_FRMC** | 0x18 | **读模式控制** | **FLWT[3:0]** 等待周期, ICACHE[16], DCACHE[17], PREFE[18], CRST[19], LVM[8] |
| **EFM_FWMC** | 0x1C | **擦写模式控制** | **PEMOD[2:0]** 编程/擦除模式, BUSHLDCTL[8], KEY1LOCK[16], KEY2LOCK[17] |
| **EFM_FSR** | 0x20 | **状态寄存器** | RDY0[8]/RDY1[24], OPTEND0[4]/1[20], COLERR, MISMTCH, PGSZERR, PRTWERR, OTPWERR0 |
| EFM_FSCLR | 0x24 | 状态清除 | 各标志对应 CLR 位写 1 清零 |
| EFM_FITE | 0x28 | 中断许可 | PEERRITE[0], OPTENDITE[1], COLERRITE[2] |
| EFM_FSWP | 0x2C | 引导交换状态 | FSWP[0]（只读） |
| EFM_CHIPID | 0x40 | 芯片标识 | 0x484404A0（只读） |
| EFM_UQID0~2 | 0x50-0x58 | 96 位唯一 ID | LOT number, Wafer number, XY 坐标 |
| EFM_WLOCK | 0x180 | 写保护锁定 | WLOCK[7:0]（写 1 后仅复位可恢复） |
| EFM_F0NWPRTx | 0x190-0x19C | FLASH0 扇区写保护 | 每 bit 对应 1 个扇区，4 个寄存器覆盖 128 扇区 |
| EFM_F1NWPRTx | 0x1A0-0x1AC | FLASH1 扇区写保护 | 同上 |

## 典型初始化流程

```c
/* === 单编程示例（擦除 + 编程 + 回读验证）=== */
// 1. 解除写保护
LL_PERIPH_WE(LL_PERIPH_EFM | LL_PERIPH_FCG | LL_PERIPH_SRAM);

// 2. 等待 FLASH 就绪
while ((SET != EFM_GetStatus(EFM_FLAG_RDY)) ||
       (SET != EFM_GetStatus(EFM_FLAG_RDY1))) { }

// 3. 解锁 EFM_FWMC
EFM_FWMC_Cmd(ENABLE);

// 4. 解除目标扇区写保护
(void)EFM_SingleSectorOperateCmd(EFM_SECTOR10_NUM, ENABLE);

// 5. 擦除扇区
uint32_t u32Addr = EFM_SECTOR_ADDR(EFM_SECTOR10_NUM);
(void)EFM_SectorErase(u32Addr);

// 6. 单编程（4 字节）
(void)EFM_ProgramWord(u32Addr, 0xAA5555AAU);
// 或单编程回读：EFM_ProgramWordReadBack(u32Addr, data);

// 7. 恢复写保护
(void)EFM_SingleSectorOperateCmd(EFM_SECTOR10_NUM, DISABLE);
EFM_FWMC_Cmd(DISABLE);
LL_PERIPH_WP(LL_PERIPH_EFM | LL_PERIPH_FCG | LL_PERIPH_SRAM);

/* === 连续编程示例（批量写入）=== */
EFM_FWMC_Cmd(ENABLE);
EFM_SetBusStatus(EFM_BUS_HOLD);  // BGO: EFM_BUS_RELEASE
(void)EFM_SingleSectorOperateCmd(sectorNum, ENABLE);
(void)EFM_SectorErase(addr);
(void)EFM_SequenceProgram(addr, buf, len);  // 连续编程
(void)EFM_SingleSectorOperateCmd(sectorNum, DISABLE);

/* === FLWT 等待周期设置（调频时必须）=== */
// hclk ≤40MHz: FLWT=0  |  ≤80MHz: 1  |  ≤120MHz: 2
// ≤160MHz: 3  |  ≤200MHz: 4  |  ≤240MHz: 5
EFM_SetWaitCycle(EFM_WAIT_CYCLE5);  // 240MHz
```

## 常见陷阱与注意事项

1. ⚠️ **调频必须先改 FLWT**：升频时先设 EFM_FRMC.FLWT 再切时钟源；降频时先切时钟源再降 FLWT。顺序颠倒会导致 HardFault
2. ⚠️ **解锁序列错误会自锁**：EFM_KEY1/KEY2 写入错误序列后自锁，仅复位可恢复。切勿在中断中操作
3. ⚠️ **编程前必须关缓存和预取指**：擦写操作前将 ICACHE/DCACHE/PREFE 置 0，否则可能读到脏数据
4. ⚠️ **连续编程写间隔不超 16μs**：超时会导致编程失败。结束后必须立即退出连续编程模式（PEMOD=000）
5. ⚠️ **连续编程禁止进入低功耗**：连续编程期间 FLASH 高压状态，禁止睡眠/停止/掉电模式
6. ⚠️ **禁止对同一地址重复编程**：不能保证数据正确性，必须先擦除再编程
7. ⚠️ **擦写中断电数据丢失**：擦写期间复位会强制停止操作，数据无法保证
8. ⚠️ **WLOCK 一旦置 1 不可逆**：仅复位可恢复，用于防止运行时被误改写保护
9. ⚠️ **OTP 锁存不可逆**：OTP 锁存地址写 0 后对应区域永久只读
10. ⚠️ **缓存 RAM 需保持供电**：使用读缓存时确保 PWC_PRAMLPC.PRAMPDC2=0

## 官方例程索引

| 例程名 | 绝对路径 | 用途简述 |
|--------|---------|---------|
| efm_base | `$EXAMPLES\efm\efm_base` | 基础擦写：单编程 + 单编程回读 + 扇区擦除 |
| efm_sequence_program | `$EXAMPLES\efm\efm_sequence_program` | 连续编程：EFM_SequenceProgram 批量写入 |
| efm_chip_erase | `$EXAMPLES\efm\efm_chip_erase` | 全擦除：单块/双块 FLASH 全擦除 |
| efm_int | `$EXAMPLES\efm\efm_int` | EFM 中断：PE 错误中断演示 |
| efm_otp | `$EXAMPLES\efm\efm_otp` | OTP 编程：OTP 块写入与锁存 |
| efm_protect | `$EXAMPLES\efm\efm_protect` | 安全保护：Level 1 密码保护配置 |
| efm_swap | `$EXAMPLES\efm\efm_swap` | 引导交换：FLASH0/1 地址互换 |
| efm_dbus | `$EXAMPLES\efm\efm_dbus` | D-BUS 保护：128KB 区域读保护演示 |
| efm_remap | `$EXAMPLES\efm\efm_remap` | 地址重映射：ROM/RAM remap 配置 |

> `$EXAMPLES` = `D:\Dev\SDKs\HC32\HC32F4A0\HC32F4A0_DDL_Rev2.4.0\projects\ev_hc32f4a0_lqfp176\examples`

## 相关应用笔记

| 笔记名 | 路径 | 关键内容 |
|--------|------|----------|
| 嵌入式 FLASH 应用笔记 | `$MANUAL\AN_HC32F4A0系列的嵌入式FLASH__Rev1.1` | FLASH 擦写流程详解、BGO 使用指南、OTP 操作注意事项 |
| HC32F4xx 编程注意事项 | `$MANUAL\AN_HC32F4xx系列编程注意事项_Rev1.00\AN_HC32F4xx系列编程注意事项_Rev1.00.md` | Flash 编程对齐、BUSHLDCTL/缓存、中断搬移到 RAM 与保护等级注意事项 |

> `$MANUAL` = `D:\Library\10_Datasheets\11_MCU\HC32系列\HC32F4A0`

## 源文件引用

- **手册 Markdown**: `D:\Library\10_Datasheets\11_MCU\HC32系列\HC32F4A0\6-EFM-嵌入式FLASH\6-EFM-嵌入式FLASH.md`
- **手册 PDF**: `D:\Library\10_Datasheets\11_MCU\HC32系列\HC32F4A0\RM_HC32F4A0系列参考手册_Rev1.40.pdf`
