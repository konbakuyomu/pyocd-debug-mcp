# DMA — DMA 控制器

> ✅ 本知识卡已填充。最后更新：2026-03-25

## 模块概述

HC32F4A0 内置 2 个独立 DMA 控制单元（DMA1/DMA2），共 16 个通道（每单元 8 通道）。DMA 总线独立于 CPU（AMBA AHB-Lite 协议），可在存储器↔存储器、存储器↔外设、外设↔外设之间自主搬运数据，无需 CPU 干预。支持连锁传输（LLP）、不连续地址传输、地址重载、通道重置等高级功能，并可通过 AOS 事件系统灵活绑定触发源。

## 关键特性

- 2 个 DMA 单元 × 8 通道，共 16 通道独立配置
- 每通道通过 AOS 触发源选择寄存器（DMA_TRGSELx）独立绑定启动源
- 数据宽度可选 8/16/32bit（DMA_CHCTLx.HSIZE）
- 块大小 1~1024 个数据（BLKSIZE=0 代表 1024）；传输次数 1~65535（CNT=0 代表无限次）
- 源/目标地址独立配置：固定、递增、递减、重载（Repeat）、不连续跳转（Non-Sequence）
- 连锁传输（Linked-List Pointer）：链式描述符自动加载，支持等待触发/立即执行两种模式
- 通道重置（Reconfig）：外部事件动态修改通道内部状态（地址/计数器）
- 3 种中断：块传输完成(BTC)、传输完成(TC)、传输错误(ERR)；BTC/TC 同时可作 AOS 事件输出
- 通道优先级：CH0 > CH1 > … > CH7（不可抢占正在传输的通道）
- DMA 寄存器仅支持 32bit 读写

## 功能导航大纲

> 小节编号对应原始手册 `kuma_HC32F4A0手册_DMA.md` 中的标题。

| 区域 | 小节 | 关键内容 |
|------|------|----------|
| 概述 | 15.1-15.2 | 简介、DMA 结构框图 |
| **使能 DMA** | 15.3.1 | FCG0.DMAx=0 + FCG0.AOS=0 + DMA_EN.EN=1 |
| 通道选择与优先级 | 15.3.2 | 8 通道，CH0 优先级最高；不可抢占 |
| **启动 DMA** | 15.3.3 | DMA_TRGSELx 绑定触发源；软件触发 DMA_SWREQ |
| 数据块 | 15.3.4 | BLKSIZE × HSIZE 确定单次传输量 |
| **传输地址控制** | 15.3.5 | 固定/递增/递减/重载/不连续跳转 |
| 传输次数 | 15.3.6 | CNT 减到 0 自动清 CHEN；CNT=0 无限次 |
| **中断与事件** | 15.3.7 | BTC/TC/ERR 三种中断；BTC/TC 可作 AOS 事件输出 |
| **连锁传输 (LLP)** | 15.3.8 | 8-word 描述符链表；LLPRUN 控制自动/等待模式 |
| 不连续地址传输 | 15.3.9 | SNSEQEN/DNSEQEN + OFFSET 跳转控制 |
| 通道重置 | 15.3.10 | RCFGCTL 配置；链指针式/不连续式/重复式三种方式 |
| 传输提前终止 | 15.3.11 | CHENCLR 写 1 → 当次读写完成后终止，不保存断点 |
| 应用举例 | 15.4 | 存储器→存储器 / 存储器→外设 / 连锁传输 |
| 寄存器-全局 | 15.5.2-15.5.14 | DMA_EN/INTSTAT/INTMASK/INTCLR/CHEN/RCFGCTL/SWREQ/CHSTAT 等 |
| **寄存器-通道** | 15.5.15-15.5.25 | SARx/DARx/DTCTLx/RPTx/SNSEQCTLx/DNSEQCTLx/LLPx/**CHCTLx** |
| 寄存器-监视 | 15.5.26 | MONSARx/MONDARx/MONDTCTLx 等（只读，反映实时状态） |
| 注意事项 | 15.6 | 32bit 读写、总线错误锁死检测与规避 |

## 寄存器速查

> DMA1 BASE: 0x40053000, DMA2 BASE: 0x40053400; x=0~7

| 寄存器 | 偏移 | 用途 | 关键位字段 |
|--------|------|------|-----------|
| DMA_EN | 0x00 | DMA 使能 | EN[0] |
| DMA_INTSTAT0 | 0x04 | 错误中断状态 | REQERR[23:16], TRNERR[7:0] |
| DMA_INTSTAT1 | 0x08 | 传输中断状态 | BTC[23:16], TC[7:0] |
| DMA_INTMASK0 | 0x0C | 错误中断屏蔽 | MSKREQERR[23:16], MSKTRNERR[7:0] |
| DMA_INTMASK1 | 0x10 | 传输中断屏蔽 | MSKBTC[23:16], MSKTC[7:0] |
| DMA_INTCLR0 | 0x14 | 错误中断清除 | CLRREQERR[23:16], CLRTRNERR[7:0] |
| DMA_INTCLR1 | 0x18 | 传输中断清除 | CLRBTC[23:16], CLRTC[7:0] |
| DMA_CHEN | 0x1C | 通道使能（写1置位，写0无效） | CHEN[7:0] |
| DMA_CHENCLR | 0x34 | 通道使能清除（写1强制终止） | CHENCLR[7:0] |
| DMA_CHSTAT | 0x24 | 通道状态观测 | CHACT[23:16], DMAACT[0] |
| DMA_RCFGCTL | 0x2C | 通道重置控制 | CNTMD, DARMD, SARMD, RCFGCHS, RCFGLLP, RCFGEN |
| DMA_SWREQ | 0x30 | 软件启动（需写保护码） | WP2[31:24]=0xA2, WP[23:16]=0xA1, SWREQ[7:0] |
| **DMA_SARx** | 0x40+0x40*x | 源地址 | SAR[31:0] |
| **DMA_DARx** | 0x44+0x40*x | 目标地址 | DAR[31:0] |
| **DMA_DTCTLx** | 0x48+0x40*x | 数据控制 | **CNT[31:16]**, BLKSIZE[9:0] |
| DMA_RPTx | 0x4C+0x40*x | 重复区域大小 | DRPT[25:16], SRPT[9:0] |
| DMA_SNSEQCTLx | 0x50+0x40*x | 源不连续控制 | SNSCNT[31:20], SOFFSET[19:0] |
| DMA_DNSEQCTLx | 0x54+0x40*x | 目标不连续控制 | DNSCNT[31:20], DOFFSET[19:0] |
| DMA_LLPx | 0x58+0x40*x | 链指针 | LLP[31:0]（下一描述符地址） |
| **DMA_CHCTLx** | 0x5C+0x40*x | **通道控制（核心）** | IE[12] LLPRUN[11] LLPEN[10] **HSIZE[9:8]** DNSEQEN[7] SNSEQEN[6] DRPTEN[5] SRPTEN[4] **DINC[3:2]** **SINC[1:0]** |

## 典型初始化流程

```c
/* === DMA 基本传输（存储器→存储器，软件触发） === */
// 1. 使能时钟（DMA + AOS 必须同时开启）
FCG_Fcg0PeriphClockCmd(FCG0_PERIPH_DMA2 | FCG0_PERIPH_AOS, ENABLE);

// 2. 配置触发源（软件触发事件 → DMA2 通道 1）
AOS_SetTriggerEventSrc(AOS_DMA2_1, EVT_SRC_AOS_STRG);

// 3. 初始化通道参数
stc_dma_init_t stcDmaInit;
DMA_StructInit(&stcDmaInit);
stcDmaInit.u32IntEn      = DMA_INT_ENABLE;
stcDmaInit.u32BlockSize  = 5;                        // 每块 5 个数据
stcDmaInit.u32TransCount = 4;                        // 传输 4 次（共 20 个）
stcDmaInit.u32DataWidth  = DMA_DATAWIDTH_32BIT;
stcDmaInit.u32SrcAddr    = (uint32_t)&u32SrcBuf[0];
stcDmaInit.u32DestAddr   = (uint32_t)&u32DestBuf[0];
stcDmaInit.u32SrcAddrInc  = DMA_SRC_ADDR_INC;
stcDmaInit.u32DestAddrInc = DMA_DEST_ADDR_INC;
DMA_Init(CM_DMA2, DMA_CH1, &stcDmaInit);

// 4. 注册 TC 中断
stc_irq_signin_config_t stcIrq;
stcIrq.enIntSrc    = INT_SRC_DMA2_TC1;
stcIrq.enIRQn      = INT002_IRQn;
stcIrq.pfnCallback = &DMA2_TC1_Callback;
INTC_IrqSignIn(&stcIrq);
NVIC_ClearPendingIRQ(INT002_IRQn);
NVIC_SetPriority(INT002_IRQn, DDL_IRQ_PRIO_DEFAULT);
NVIC_EnableIRQ(INT002_IRQn);

// 5. 使能 DMA 模块 + 通道
DMA_Cmd(CM_DMA2, ENABLE);
DMA_ChCmd(CM_DMA2, DMA_CH1, ENABLE);

// 6. 触发传输（每次触发传 1 个 Block）
AOS_SW_Trigger();   // 或 DMA_MxChSWTrigger(CM_DMA2, DMA_MX_CH1)
```

## 常见陷阱与注意事项

1. ⚠️ **必须同时使能 AOS 时钟**：DMA 依赖 AOS 事件路由，`FCG0_PERIPH_AOS` 必须一起开启，否则触发源无效
2. ⚠️ **寄存器仅支持 32bit 读写**：对 DMA 寄存器进行 8/16bit 读写操作无效
3. ⚠️ **CHEN=1 时不可写描述符**：通道使能后对 SARx/DARx/DTCTLx 等描述符寄存器的写操作无效，必须先 CHENCLR 清除
4. ⚠️ **CHENCLR 终止不保存断点**：软件终止后重新使能会从头开始传输被终止的数据块，不是断点续传
5. ⚠️ **CNT=0 是无限次传输**：不会自动清 CHEN，不会产生 TC 中断
6. ⚠️ **传输完成后重启通道**：CHEN 自动清 0 后需重新配置描述符再写 CHEN=1，否则会按上次结束状态（CNT=0 无限次）继续
7. ⚠️ **总线错误可导致 DMA 锁死**：传输中发生总线错误且有其它通道等待时，DMA 进入不可恢复的锁死状态，只能系统复位。检测方法：TRNERR≠0 且 CHACT 长时间为 1 且 CHENCLR 无法清除
8. ⚠️ **避免请求溢出**：上次请求未响应时再次触发会产生 REQERR，第二次请求被丢弃
9. ⚠️ **重置功能使用 B 系列寄存器**：通道重置开启后，RPTx/SNSEQCTLx/DNSEQCTLx 无效，改用 RPTBx/SNSEQCTLBx/DNSEQCTLBx
10. ⚠️ **RCFGCTL 须在 DMA_EN=0 时设置**，且必须在重置通道的首次传输前完成

## 官方例程索引

| 例程名 | 绝对路径 | 用途简述 |
|--------|---------|---------|
| dmac_base | `$EXAMPLES\dmac\dmac_base` | 基本传输：软件触发 + AOS 事件触发，BTC/TC 中断 |
| dmac_repeat | `$EXAMPLES\dmac\dmac_repeat` | 源地址重复模式：传 N 个后源地址自动回绕 |
| dmac_non_sequence | `$EXAMPLES\dmac\dmac_non_sequence` | 源地址不连续传输：块内跳跃读取稀疏数据 |
| dmac_link_list_pointer | `$EXAMPLES\dmac\dmac_link_list_pointer` | 连锁传输 (LLP)：3 段不同数据宽度的描述符链 |
| dmac_channel_reconfig | `$EXAMPLES\dmac\dmac_channel_reconfig` | 通道重置：按键事件动态修改源地址/计数器 |

> `$EXAMPLES` = `D:\Dev\SDKs\HC32\HC32F4A0\HC32F4A0_DDL_Rev2.4.0\projects\ev_hc32f4a0_lqfp176\examples`

## 相关应用笔记

（无专门针对 DMA 的 AN，DMA 使用散见于各外设 AN 中）

## 源文件引用

- **手册 Markdown**: `D:\Library\10_Datasheets\11_MCU\HC32系列\HC32F4A0\14-DMA-DMA控制器\kuma_HC32F4A0手册_DMA.md`
- **手册 PDF**: `D:\Library\10_Datasheets\11_MCU\HC32系列\HC32F4A0\RM_HC32F4A0系列参考手册_Rev1.40.pdf`
