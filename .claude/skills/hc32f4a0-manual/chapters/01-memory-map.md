# 存储器映射+总线架构

> ✅ 本知识卡已填充。最后更新：2026-03-25

## 模块概述

HC32F4A0 基于 Cortex-M4F，4GB 线性地址空间。内置 2MB Flash（双 Bank 各 1MB）、512KB+4KB SRAM。总线系统采用 32 位多层 AHB 矩阵，8 条主机总线通过循环仲裁访问 17 条从机总线，支持并发访问。外设/SRAM 位段提供 bit-band 原子操作；2 个可配置地址重映射区域（4KB~512KB）支持 Flash/SRAMH 重映射。

## 关键特性

- Flash 2MB：Bank0（0x00000000）+ Bank1（0x00100000）
- SRAM：SRAMH 128KB（0x1FFE0000，CPU 0 等待）+ SRAM1~4 + SRAMB 共 516KB
- 外设位段 0x42000000（32MB 别名区）映射 0x40000000
- SRAM 位段 0x22000000（32MB 别名区）映射 0x20000000
- QSPI 外部 128MB + EXMC 外扩（SMC 512MB + DMC 128MB）
- 地址重映射：2 个窗口 REMAP0/REMAP1，大小 4KB~512KB
- 总线矩阵：8 主机 × 17 从机，循环仲裁

## 功能导航大纲

| 区域 | 小节 | 关键内容 |
|------|------|----------|
| 存储器映射 | 1.1 | 完整 4GB 地址空间分配表 |
| 外部空间映射 | 1.2 | QSPI 128MB：设备 64MB + I/O 寄存器 64MB |
| 位段空间 | 1.3 | 外设位段 + SRAM 位段，仅 CPU 有效 |
| 地址重映射 | 1.4 | REMAP0/REMAP1 配置，目标为 Flash 或 SRAMH |
| 重映射寄存器 | 1.5 | MMF_REMPRT/REMCR0/REMCR1 |
| 总线概述 | 2.1 | 8 主机 + 17 从机总线列表 |
| 总线架构 | 2.2 | 总线矩阵拓扑图 |
| 总线功能 | 2.3 | 跨时钟域自动同步、并发访问规则 |

## 地址空间表

### CODE 区域（0x00000000~0x1FFFFFFF）

| 模块 | 起始地址 | 结束地址 | 大小 |
|------|----------|----------|------|
| Flash Bank0 | 0x00000000 | 0x000FFFFF | 1MB |
| Flash Bank1 | 0x00100000 | 0x001FFFFF | 1MB |
| REMAP0 | 0x02000000 | 0x0207FFFF | 512KB |
| REMAP1 | 0x02080000 | 0x020FFFFF | 512KB |
| OTP | 0x03000000 | 0x03001ADB | ~6.7KB |
| SRAMH | 0x1FFE0000 | 0x1FFFFFFF | 128KB |

### SRAM 区域（0x20000000~0x23FFFFFF）

| 模块 | 起始地址 | 大小 |
|------|----------|------|
| SRAM1 | 0x20000000 | 128KB |
| SRAM2 | 0x20020000 | 128KB |
| SRAM3 | 0x20040000 | 96KB |
| SRAM4 | 0x20058000 | 32KB |
| SRAMB | 0x200F0000 | 4KB |
| SRAM BitBand | 0x22000000 | 32MB 别名区 |

### 外设区域（0x40000000~）

| 总线 | 代表模块 | 地址范围 | 时钟 |
|------|---------|----------|------|
| APB1 | EFM/AOS/Timer6/EMB/SPI1-3/USART1-5/I2S1-2 | 0x40010000~ | PCLK1 |
| APB2 | Timer0/Timer2/TimerA5-12/SPI4-6/USART6-10 | 0x40020000~ | PCLK1 |
| APB5 | Timer4/TimerA1-4/HRPWM | 0x40038000~ | PCLK0 |
| APB3 | ADC1-3/DAC1-2/TRNG | 0x40040000~ | PCLK4 |
| APB4 | WDT/SWDT/CTC/CMP/OTS/RTC/PWC/I2C1-6 | 0x40048000~ | PCLK3 |
| AHB1 | INTC/DMA/GPIO/CMU/MAU/DVP/DCU/FMAC | 0x40050000~ | HCLK |

### 外部存储

| 模块 | 起始地址 | 大小 |
|------|----------|------|
| SMC | 0x60000000 | 512MB |
| DMC | 0x80000000 | 128MB |
| QSPI 设备 | 0x98000000 | 64MB |

### 重映射寄存器（BASE: 0x40010500）

| 寄存器 | 偏移 | 关键位字段 |
|--------|------|-----------|
| MMF_REMPRT | 0x00 | 写保护关键码 |
| MMF_REMCR0 | 0x04 | EN0[31], RM0TADDR[28:12], RM0SIZE[4:0] |
| MMF_REMCR1 | 0x08 | EN1[31], RM1TADDR[28:12], RM1SIZE[4:0] |

## 常见陷阱与注意事项

1. ⚠️ **Reserved 区域访问触发 BusFault**：地址空间中 Reserved 区域的任何访问都会触发异常
2. ⚠️ **位段操作仅限 CPU**：DMA 不能使用位段地址
3. ⚠️ **带保护模块需特权模式**：CMU/INTC/EFM/CRC 等在保护有效时只允许 CPU 特权模式访问
4. ⚠️ **重映射大小限制**：RM0SIZE/RM1SIZE 仅 4KB~512KB 有效
5. ⚠️ **重映射寄存器受写保护**：修改前须向 MMF_REMPRT 写关键码解锁
6. ⚠️ **跨时钟域有等待周期**：总线矩阵在主从时钟不同时自动同步，会引入额外等待
7. ⚠️ **Flash 访问路径区分**：CPU 通过 ICODE/DCODE 专用总线，DMA 通过 MCODE 总线

## 官方例程索引

（无官方例程）

## 相关应用笔记

| 笔记名 | 路径 | 关键内容 |
|--------|------|----------|
| 硬件开发指南 | `$MANUAL\AN_HC32F4A0系列的硬件开发指南` | 存储器与总线概览 |
| 嵌入式 FLASH | `$MANUAL\AN_HC32F4A0系列的嵌入式FLASH__Rev1.1` | Flash 地址空间与编程 |

> `$MANUAL` = `D:\Library\10_Datasheets\11_MCU\HC32系列\HC32F4A0`

## 源文件引用

- **手册 Markdown**: `D:\Library\10_Datasheets\11_MCU\HC32系列\HC32F4A0\1-存储器映射+总线架构\1-存储器映射_总线架构.md`
- **手册 PDF**: `D:\Library\10_Datasheets\11_MCU\HC32系列\HC32F4A0\RM_HC32F4A0系列参考手册_Rev1.40.pdf`
