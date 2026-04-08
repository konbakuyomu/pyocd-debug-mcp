# ETHMAC — 以太网 MAC 控制器

> ✅ 本知识卡已填充。最后更新：2026-03-26

## 模块概述

ETHMAC 用于在以太网网络中按照 IEEE802.3-2002 标准发送和接收数据。支持 MII 和 RMII 两种 PHY 接口，10/100Mbps 全双工/半双工操作。内含 DMA 控制器（描述符架构）、2KB TX FIFO + 2KB RX FIFO、COE 校验卸载引擎、IEEE1588-2008 PTP 时间戳、MMC 统计计数器。可通过 SMI 接口管理最多 32 个 PHY 设备。

## 关键特性

- **PHY 接口**：MII（16 引脚）或 RMII（7 引脚），通过 ETH_MAC_IFCONFR.IFSEL 选择
- **速率**：10/100Mbps，全双工/半双工
- **地址过滤**：5 个完美 DA + 4 个完美 SA + 64 位 Hash 滤波器 + L3/L4 过滤
- **VLAN 过滤**：12/16 位 VLAN 标记 + Hash 滤波
- **COE 引擎**：IPv4/TCP/UDP/ICMP 校验自动计算和验证
- **DMA**：环式/链式描述符，每描述符最大 8KB 数据，存储转发模式
- **FIFO**：2KB TX + 2KB RX，可编程阈值，支持自动暂停帧流控
- **PTP**：IEEE1588-2008 时间戳，2 组目标时间，2 组 PPS 输出
- **MMC**：硬件统计计数器（发送/接收帧计数、错误计数等）
- **远程唤醒**：4 组唤醒帧过滤器 + Magic Packet 检测
- **发送特性**：SA 插入/替换、CRC 插入/替换、VLAN 标记操作、PAD 自动填充、可编程帧间隔
- **巨型帧**：支持可编程帧长度，最大 16KB

## 功能导航大纲

> 小节编号对应原始手册标题

| 区域 | 小节 | 关键内容 |
|------|------|----------|
| 概要 | 39.1 | IEEE802.3-2002/IEEE1588-2008/RMII 规范 |
| 框图 | 39.2.1 | AHB Master/Slave + DMA + MAC + FIFO 架构 |
| MAC 特性 | 39.2.2 | 帧处理/地址过滤/VLAN/L3L4/COE/MMC |
| PTP 特性 | 39.2.3 | 时间戳快照/粗细校准/目标时间/PPS |
| DMA 特性 | 39.2.4 | 描述符/突发/存储转发/仲裁 |
| MII 接口 | 39.3.1 | 16 引脚全功能连接 |
| RMII 接口 | 39.3.2 | 7 引脚精简连接，50MHz 参考时钟 |
| SMI 接口 | 39.3.3 | MDC/MDIO 管理 PHY |
| 寄存器 | 39.4 | MAC/DMA/PTP/MMC 寄存器详述 |

## 寄存器速查

> 基址: 0x40050000

| 寄存器组 | 偏移范围 | 说明 |
|---------|---------|------|
| MAC 配置 | 0x0000~0x00FF | CONFIGR/FLTCTLR/FLWCTLR/MACADDRHR/LR 等 |
| MAC L3L4 | 0x0400~0x04FF | L3/L4 过滤和 VLAN 配置 |
| MMC 计数器 | 0x0100~0x02FF | 发送/接收帧统计计数器 |
| PTP 时间戳 | 0x0700~0x07FF | 时间戳控制/秒/纳秒/目标时间/PPS |
| DMA | 0x1000~0x10FF | BUSMODR/DMASTSR/TXPOLLR/RXPOLLR 描述符控制 |
| ETH_MAC_IFCONFR | 0x40055404 | 接口模式选择（MII/RMII） |

## 典型初始化流程

```c
/* 以 RMII 接口 100Mbps 全双工为例 */

/* 1. 使能时钟 */
FCG_Fcg1PeriphClockCmd(FCG1_PERIPH_ETHMAC, ENABLE);

/* 2. GPIO 配置：RMII 引脚复用 */
/* RMII_REF_CLK, RMII_MDIO, RMII_MDC, RMII_CRS_DV,
   RMII_TXD0/1, RMII_TX_EN, RMII_RXD0/1 */

/* 3. 选择 RMII 接口 */
/* ETH_MAC_IFCONFR.IFSEL = 1 (RMII) */

/* 4. ETHMAC 初始化 */
stc_eth_init_t stcEthInit;
ETH_StructInit(&stcEthInit);
stcEthInit.stcMacInit.u32Speed    = ETH_MAC_SPEED_100M;
stcEthInit.stcMacInit.u32DuplexMode = ETH_MAC_DUPLEX_MD_FULL;
stcEthInit.stcMacInit.u32ChecksumMode = ETH_MAC_CHECKSUM_MD_HW;
ETH_Init(&stcEthInit);

/* 5. 配置 DMA 描述符（环式/链式） */

/* 6. 使能 MAC TX/RX */
ETH_MAC_TransCmd(ENABLE);
ETH_MAC_ReceiveCmd(ENABLE);
ETH_DMA_TxCmd(ENABLE);
ETH_DMA_RxCmd(ENABLE);
```

## 常见陷阱与注意事项

1. **IFSEL 必须最先配置**：在对 ETHMAC 其他特性配置之前，必须优先设定 MII/RMII 接口选择
2. **RMII 需 50MHz 参考时钟**：RMII_REF_CLK 必须为 50MHz
3. **卡识别时钟限制**：MII 模式下 100Mbps 参考时钟 25MHz，10Mbps 为 2.5MHz
4. **描述符对齐**：DMA 描述符必须字对齐
5. **COE 不检查 IP payload 错误**：COE 只校验 Header/TCP/UDP checksum，不检查上层协议逻辑
6. **PTP 需外部晶振**：精确时间同步需高精度时钟源
7. **MII_COL/CRS 全双工无意义**：全双工模式下载波侦听和冲突检测信号无效
8. **MAC 地址配置**：至少配置 MAC 地址 0（MACADDRHR0/LR0）用于接收帧过滤

## 官方例程索引

| 例程名 | 绝对路径 | 用途简述 |
|--------|---------|--------:|
| eth_loopback | `$EXAMPLES\eth\eth_loopback` | 以太网回环测试 |
| eth_pps_output | `$EXAMPLES\eth\eth_pps_output` | PTP PPS 脉冲输出 |
| eth_twoboards | `$EXAMPLES\eth\eth_twoboards` | 双板以太网通信 |

> `$EXAMPLES` = `D:\Dev\SDKs\HC32\HC32F4A0\HC32F4A0_DDL_Rev2.4.0\projects\ev_hc32f4a0_lqfp176\examples`

## 相关应用笔记

| 应用笔记 | 绝对路径 |
|---------|---------:|
| 以太网 LWIP 协议栈移植 | `D:\Library\10_Datasheets\11_MCU\HC32系列\HC32F4A0\AN_HC32F4A0系列的以太网LWIP协议栈移植_Rev1.1` |

## 源文件引用

- **手册 Markdown**: `D:\Library\10_Datasheets\11_MCU\HC32系列\HC32F4A0\38-ETHMAC-以太网MAC控制器\38-ETHMAC-以太网MAC控制器.md`
- **手册 PDF**: `D:\Library\10_Datasheets\11_MCU\HC32系列\HC32F4A0\RM_HC32F4A0系列参考手册_Rev1.40.pdf`
