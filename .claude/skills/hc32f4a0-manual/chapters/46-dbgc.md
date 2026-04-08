# DBGC — 调试控制器

> ✅ 本知识卡已填充。最后更新：2026-03-26

## 模块概述

DBGC（Debug Controller）基于 ARM Cortex-M4F 内核内置的调试硬件，支持 SWD（2 线串行）和 JTAG（5 线并行）两种调试接口。包含 SWJ-DP 调试端口、AHB-AP 访问端口、ITM 指令跟踪、ETM 嵌入式跟踪宏单元、FPB Flash 断点、DWT 数据断点、TPIU 跟踪端口接口。支持在调试模式下暂停外设定时器计数。

## 关键特性

- **调试接口**：SWD（SWDIO+SWCLK，2 线）+ JTAG（5 线），默认 JTAG
- **SWD/JTAG 切换**：通过专用 JTAG 序列（50×TMS=1 → 0x79E7 → 50×TMS=1）切换到 SWD
- **跟踪输出**：TRACESWO（异步，仅 SWD 模式）+ TRACED[3:0]+TRACECK（同步）
- **外设暂停**：调试暂停时可停止 SWDT/WDT/RTC/TMR0~TMR6/TMR4/TMR2/TMRA 的计数
- **引脚释放**：5 个 JTAG 引脚复位后全部分配，可通过 GPIO PSPCR 释放未用引脚
- **内部上拉**：NJTRST/JTDI/JTMS/JTCK 均有内部上拉，JTDO 高阻
- **PPB 区域**：寄存器位于特权模式 PPB 区域

## 功能导航大纲

> 小节编号对应原始手册标题

| 区域 | 小节 | 关键内容 |
|------|------|----------|
| 简介 | 47.1 | Cortex-M4F 调试功能概述 |
| 系统框图 | 47.2 | SWJ-DP/AHB-AP/ITM/ETM/FPB/DWT/TPIU |
| SWJ-DP | 47.3 | SWD/JTAG 双模调试端口，切换序列 |
| 引脚分配 | 47.4 | 5 引脚 JTAG + 灵活释放为 GPIO |
| 寄存器 | 47.5 | MCUDBGSTAT/MCUSTPCTL/MCUTRACECTL/MCUSTPCTL2 |
| SW 协议 | 47.6 | SWCLK+SWDIO，LSB 先发 |
| TPIU | 47.7 | 跟踪端口，异步/同步模式配置 |

## 寄存器速查

> 基址: 0xE0042000（PPB 区域，特权模式访问）

| 寄存器 | 偏移 | 用途 | 关键位字段 |
|--------|------|------|-----------:|
| MCUDBGSTAT | 0x1C | 调试状态 | CDBGPWRUPREQ, CDBGPWRUPACK |
| MCUSTPCTL | 0x20 | 外设暂停控制 1 | SWDTSTP, WDTSTP, RTCSTP, TMR0~TMR6/TMR4/TMR2 暂停 |
| MCUTRACECTL | 0x24 | TRACE 配置 | TRACE_IOEN, TRACE_MODE[1:0]（00异步/01同步1位/10同步2位/11同步4位） |
| MCUSTPCTL2 | 0x28 | 外设暂停控制 2 | TMRA1~TMRA12 暂停 |

## 典型初始化流程

```c
/* 调试模式下暂停看门狗和定时器 */

/* 1. 配置外设暂停（内核停止时定时器也暂停） */
/* 默认值 MCUSTPCTL = 0x3B：SWDT/WDT 已暂停 */
/* 如需暂停 TMR6_1: */
SET_REG32_BIT(CM_DBGC->MCUSTPCTL, DBGC_MCUSTPCTL_M15STP);

/* 2. 配置 TRACE 输出（可选，用于 ITM printf） */
/* 异步跟踪模式 */
MODIFY_REG32(CM_DBGC->MCUTRACECTL,
    DBGC_MCUTRACECTL_TRACE_IOEN | DBGC_MCUTRACECTL_TRACE_MODE,
    DBGC_MCUTRACECTL_TRACE_IOEN);  /* TRACE_MODE=00: 异步 */

/* 3. 释放未用 JTAG 引脚为 GPIO（如使用 SWD 模式）——通过 GPIO PSPCR */
```

## 常见陷阱与注意事项

1. **默认 JTAG 模式**：复位后默认 JTAG-DP，调试器需发送切换序列才能使用 SWD
2. **异步跟踪仅 SWD**：TRACESWO 引脚与 JTDO 复用，JTAG 模式下不可用异步跟踪
3. **PPB 区域特权访问**：寄存器只能在特权模式下由 CPU 或调试 IDE 访问
4. **释放引脚顺序**：先切换到 SWD 模式，再通过用户软件释放 JTDI/JTDO/NJTRST
5. **JTAG 引脚内部弱上拉**：< 100kΩ，建议外接 10kΩ 上拉
6. **TRACECLKIN 频率**：连接内部时钟，复位状态与正常运行频率不同，复位中不宜使能跟踪
7. **MCUSTPCTL 复位值 0x3B**：默认暂停 SWDT、WDT，b3~b5 为保留位须写 1
8. **看门狗调试**：未暂停 WDT/SWDT 时，断点调试中看门狗可能超时复位

## 官方例程索引

| 例程名 | 绝对路径 | 用途简述 |
|--------|---------|--------:|
| dbgc_swo_print | `$EXAMPLES\dbgc\dbgc_swo_print` | SWO 异步跟踪 printf 输出 |

> `$EXAMPLES` = `D:\Dev\SDKs\HC32\HC32F4A0\HC32F4A0_DDL_Rev2.4.0\projects\ev_hc32f4a0_lqfp176\examples`

## 相关应用笔记

| 笔记名 | 路径 | 关键内容 |
|--------|------|----------|
| SWO Trace 使用方法 | `$MANUAL\AN_HC32F460_F4A0_F451_F452_F448系列的SWO_Trace使用方法_Rev1.0\AN_HC32F460_F4A0_F451_F452_F448系列的SWO_Trace使用方法_Rev1.0.md` | IAR/Keil SWO Trace 配置、printf 重定向和变量实时跟踪 |

> `$MANUAL` = `D:\Library\10_Datasheets\11_MCU\HC32系列\HC32F4A0`

## 源文件引用

- **手册 Markdown**: `D:\Library\10_Datasheets\11_MCU\HC32系列\HC32F4A0\46-DBGC-调试控制器\46-DBGC-调试控制器.md`
- **手册 PDF**: `D:\Library\10_Datasheets\11_MCU\HC32系列\HC32F4A0\RM_HC32F4A0系列参考手册_Rev1.40.pdf`
