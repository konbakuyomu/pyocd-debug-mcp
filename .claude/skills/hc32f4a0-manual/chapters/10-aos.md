# AOS — 自动运行系统

> ✅ 本知识卡已填充。最后更新：2026-03-25

## 模块概述

AOS（Automatic Operation System）用于在不借助 CPU 的情况下实现外设之间的硬件联动。利用外设产生的事件（如定时器溢出、ADC 转换结束、通信收发状态等）作为 AOS 源，自动触发另一个外设的动作（AOS 目标），实现零 CPU 开销的外设协同工作。

## 关键特性

- 共 368 种 AOS 源事件可选（事件编号见 INTC 章节表 10-3 中"可选择为事件"列）
- 每个 AOS 目标可配 1 个专用触发源 + 2 个公共触发源，合计最多 3 路同时触发
- 2 个公共触发源寄存器（COMTRG1/COMTRG2）被所有 AOS 目标共享
- 支持硬件事件触发和软件写寄存器触发（INTSFTTRG）
- AOS 目标覆盖：DCU(1~8)、DMA1/2(各 8 通道)、Timer6/0/2、TimerA、Event Port、HASH、OTS、ADC1~3
- DCU1&5/DCU2&6/DCU3&7/DCU4&8 分别共用触发源选择寄存器
- DMA1 和 DMA2 共用通道重置触发源寄存器
- HASH 触发源 A 仅限 DMA_BTCx(x=0~7)，触发源 B 仅限 DMA_TCx(x=0~7)

## 功能导航大纲

> 小节编号对应原始手册标题

| 区域 | 小节 | 关键内容 |
|------|------|----------|
| 简介 | 11.1 | 模块概念、AOS 源/目标定义 |
| 功能概览 | 11.1.1 | 368 种源、35 个目标分类（DCU/DMA/Timer/HASH/ADC 等） |
| 模块示意图 | 11.1.2 | AOS 源 → AOS 路由 → AOS 目标的信号流 |
| AOS 源事件列表 | 11.2.1 | 引用 INTC 表 10-3（事件编号 9bit） |
| AOS 目标列表 | 11.2.2 | 35 个目标序号 0~34 及对应动作 |
| 专用触发源 | 11.3.1 | 每个目标一个独立 TRGSEL 寄存器，写入事件编号 |
| 公共触发源 | 11.3.2 | COMTRG1/2 共享机制、COMEN 使能位控制 |
| 寄存器一览 | 11.4.1 | 基地址 0x40010800，19 组寄存器 |
| 寄存器详述 | 11.4.2~11.4.19 | 各目标 TRGSEL 寄存器位字段 |

## 寄存器速查

> BASE_ADDR: 0x40010800

| 寄存器 | 偏移 | 用途 | 关键位字段 |
|--------|------|------|-----------|
| INTSFTTRG | 0x00 | 软件触发事件 | 写入产生一次触发 |
| DCU_TRGSELx (x=1~4) | 0x04~0x10 | DCU 触发源选择 | COMEN[31:30], TRGSEL[8:0] |
| DMA1_TRGSELx (x=0~7) | 0x14~0x30 | DMA1 各通道触发源 | COMEN[31:30], TRGSEL[8:0] |
| DMA2_TRGSELx (x=0~7) | 0x34~0x50 | DMA2 各通道触发源 | COMEN[31:30], TRGSEL[8:0] |
| DMA_RC_TRGSEL | 0x54 | DMA 通道重置触发源 | COMEN[31:30], TRGSEL[8:0] |
| TMR6_TRGSELx (x=0~3) | 0x58~0x64 | Timer6 触发源（8 单元共有） | COMEN[31:30], TRGSEL[8:0] |
| PEVNT_TRGSEL12 | 0x68 | Event Port1&2 触发源 | COMEN[31:30], TRGSEL[8:0] |
| PEVNT_TRGSEL34 | 0x6C | Event Port3&4 触发源 | COMEN[31:30], TRGSEL[8:0] |
| TMR0_TRGSEL | 0x70 | Timer0 触发源（2 单元共有） | COMEN[31:30], TRGSEL[8:0] |
| TMR2_TRGSEL | 0x74 | Timer2 触发源（4 单元共有） | COMEN[31:30], TRGSEL[8:0] |
| HASH_TRGSELB | 0x78 | HASH 触发源 B（限 DMA_TC） | COMEN[31:30], TRGSEL[8:0] |
| HASH_TRGSELA | 0x7C | HASH 触发源 A（限 DMA_BTC） | COMEN[31:30], TRGSEL[8:0] |
| TMRA_TRGSELx (x=0~3) | 0x80~0x8C | TimerA 触发源 | COMEN[31:30], TRGSEL[8:0] |
| OTS_TRGSEL | 0x90 | OTS 触发源 | COMEN[31:30], TRGSEL[8:0] |
| ADC1_TRGSELx (x=0,1) | 0x94, 0x98 | ADC1 触发源 | COMEN[31:30], TRGSEL[8:0] |
| ADC2_TRGSELx (x=0,1) | 0x9C, 0xA0 | ADC2 触发源 | COMEN[31:30], TRGSEL[8:0] |
| ADC3_TRGSELx (x=0,1) | 0xA4, 0xA8 | ADC3 触发源 | COMEN[31:30], TRGSEL[8:0] |
| AOS_COMTRG1 | 0xAC | 公共触发源 1 | COMTRG[8:0] |
| AOS_COMTRG2 | 0xB0 | 公共触发源 2 | COMTRG[8:0] |

## 典型初始化流程

```c
/* 以 "TMR2 溢出事件触发 DMA1 通道0 传输" 为例 */
/* 1. 使能 AOS 时钟 */
FCG_Fcg0PeriphClockCmd(FCG0_PERIPH_AOS, ENABLE);

/* 2. 设置专用触发源：DMA1 通道0 由 TMR2 溢出事件触发 */
AOS_SetTriggerEventSrc(AOS_DMA1_0, EVT_SRC_TMR2_1_CMP_A);

/* 3.（可选）设置公共触发源，使多个目标共享同一触发 */
AOS_CommonTriggerCmd(AOS_DMA1_0, AOS_COMM_TRIG1, ENABLE);
AOS_SetTriggerEventSrc(AOS_COMM_TRIG1, EVT_SRC_TMR4_1_SCMP_UH);

/* 4.（可选）软件触发 */
AOS_SW_Trigger();
```

## 常见陷阱与注意事项

1. ⚠️ **公共触发源默认未隔离**：COMTRG1/2 被所有目标共享，未使用公共触发的目标必须将其 COMEN[0]/COMEN[1] 保持为 0，否则会产生误触发
2. ⚠️ **DCU 共用寄存器**：DCU1&5、DCU2&6、DCU3&7、DCU4&8 分别共用 TRGSEL，配置一方另一方同步生效
3. ⚠️ **HASH 触发源受限**：TRGSELA 仅限 DMA_BTCx，TRGSELB 仅限 DMA_TCx，选择其他事件行为不可预期
4. ⚠️ **Timer 寄存器共用**：TMR6_TRGSEL0~3 为 8 个 Timer6 单元共有，TMR0/TMR2 类似，配置时需统筹
5. ⚠️ **AOS 时钟使能**：使用前必须通过 FCG0 开启 AOS 外设时钟，否则寄存器写入无效
6. ⚠️ **复位值 0x1FF**：所有 TRGSEL 复位值 TRGSEL=0x1FF（编号 511 非有效源），复位后 AOS 处于未触发状态

## 官方例程索引

| 例程名 | 绝对路径 | 用途简述 |
|--------|---------|---------|
| ep_aos_trig | `$EXAMPLES\event_port\ep_aos_trig` | Event Port 与 AOS 联动触发 |

> `$EXAMPLES` = `D:\Dev\SDKs\HC32\HC32F4A0\HC32F4A0_DDL_Rev2.4.0\projects\ev_hc32f4a0_lqfp176\examples`
>
> AOS 通常作为其他外设例程的组成部分（DMA、ADC、Timer 例程中配置触发源），非独立例程目录。

## 相关应用笔记

暂无专属 AOS 应用笔记。

## 源文件引用

- **手册 Markdown**: `D:\Library\10_Datasheets\11_MCU\HC32系列\HC32F4A0\10-AOS-自动运行系统\10-AOS-自动运行系统.md`
- **手册 PDF**: `D:\Library\10_Datasheets\11_MCU\HC32系列\HC32F4A0\RM_HC32F4A0系列参考手册_Rev1.40.pdf`
