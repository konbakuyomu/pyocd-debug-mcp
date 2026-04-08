# CANFD — CAN FD 控制器

> ✅ 本知识卡已填充。最后更新：2026-03-25

## 模块概述

CAN FD 控制器对应 CAN 通道 2（CAN_2），完全支持 CAN2.0A/CAN2.0B/CAN FD 协议。CAN FD 数据段最高通信波特率 8Mbit/s。具有 1 个高优先主发送缓冲器（PTB）、3 个副发送缓冲器（STB，FIFO/优先级仲裁模式）、8 个接收缓冲器（RB，FIFO）、16 组独立筛选器。支持时间触发 CAN（TTCAN，ISO11898-4 Level 1）、TDC/RDC 延迟补偿、回环/静默模式。

## 关键特性

- **协议**：CAN2.0A / CAN2.0B / CAN FD，向上兼容（CAN FD 禁止时自动忽略 FD 帧）
- **波特率**：CAN FD 数据段最高 8Mbit/s，仲裁段遵循 CAN2.0 波特率，支持 1~1/256 预分频
- **发送缓冲器**：1 个 PTB（最高优先级，单帧）+ 3 个 STB（FIFO 或优先级仲裁模式）
- **接收缓冲器**：8 级 RB FIFO，错误/不接收的数据不覆盖已存储消息
- **筛选器**：16 组独立筛选器，支持 11 位标准 ID / 29 位扩展 ID，可编程 CODE + MASK
- **单次发送**：PTB/STB 均支持单次发送模式（不自动重传）
- **特殊模式**：静默模式（仅监听）、内部/外部回环模式（测试）
- **TTCAN**：ISO11898-4 Level 1 硬件支持，16 位计时器，5 种触发方式
- **TDC/RDC**：发送器/接收器延迟补偿，SSP 偏移可编程
- **错误处理**：5 种错误类型（位/形式/填充/应答/CRC），可编程警告阈值（EWL），TECNT/RECNT 计数器
- **时钟**：通信时钟 can_clk 源自外部高速振荡器，需满足 PCLK1 ≥ 1.5× can_clk
- **FD 推荐时钟**：20MHz / 40MHz / 80MHz

## 功能导航大纲

> 小节编号对应原始手册标题

| 区域 | 小节 | 关键内容 |
|------|------|----------|
| 简介 | 36.1 | CAN FD 总体功能描述，对应 CAN 通道 2 |
| 系统框图 | 36.2 | 控制器架构 |
| 管脚说明 | 36.3 | CAN2_TX/RX + 测试观测引脚 |
| 动作模式 | 36.4.1 | 复位模式 vs 动作模式 |
| 波特率 | 36.4.2 | SBT（仲裁段）+ FBT（数据段）位时间计算公式，20/40/80MHz 推荐配置表 |
| 发送缓冲器 | 36.4.3 | PTB + STB，TBUF/TBSEL/TSNEXT 操作 |
| 接收缓冲器 | 36.4.4 | 8 级 RB FIFO，RBUF 读取 + RREL 释放 |
| 筛选器 | 36.4.5 | 16 组 ACF，ACFCTRL/ACFEN/ACF 配置 |
| 数据收发 | 36.4.6~9 | 发送/接收流程，单次发送，取消发送 |
| 错误处理 | 36.4.10~12 | 错误状态机，节点关闭恢复，仲裁失败捕捉(ALC) |
| 回环/静默 | 36.4.13~14 | 内部/外部回环，静默模式 |
| TTCAN | 36.4.17 | 时间触发通信，5 种触发方式，看门时间 |
| TDC/RDC | 36.4.18 | 发送器/接收器延迟补偿 |
| 中断 | 36.4.19 | 14 种中断源 |
| 寄存器 | 36.5 | 寄存器详述 |

## 寄存器速查

> CAN_2 基址: 0x40078000

| 寄存器 | 偏移 | 位宽 | 用途 |
|--------|------|------|------|
| CAN_RBUF | 0x00~0x4F | - | 接收 BUF（8 字节头 + 最多 64 字节数据） |
| CAN_TBUF | 0x50~0x97 | - | 发送 BUF（PTB/STB 共用访问口） |
| CAN_CFG_STAT | 0xA0 | 8 | 配置状态（RESET/BUSOFF/TPSS/TSSS） |
| CAN_TCMD | 0xA1 | 8 | 发送命令（TPE/TSONE/TSALL/TPA/TSA/TBSEL） |
| CAN_TCTRL | 0xA2 | 8 | 发送控制（TSNEXT/TSMODE/FD_ISO） |
| CAN_RCTRL | 0xA3 | 8 | 接收控制（RREL/ROM/SACK） |
| CAN_RTIE | 0xA4 | 8 | 收发中断使能 |
| CAN_RTIF | 0xA5 | 8 | 收发中断标志 |
| CAN_ERRINT | 0xA6 | 8 | 错误中断使能和标志 |
| CAN_LIMIT | 0xA7 | 8 | 错误警告限定（AFWL/EWL） |
| CAN_SBT | 0xA8 | 32 | Slow 位时序（S_PRESC/S_SEG_1/S_SEG_2/S_SJW） |
| CAN_FBT | 0xAC | 32 | Fast 位时序（F_PRESC/F_SEG_1/F_SEG_2/F_SJW） |
| CAN_EALCAP | 0xB0 | 8 | 错误类型(KOER) + 仲裁失败位置(ALC) |
| CAN_TDC | 0xB1 | 8 | TDC 使能 + SSP 偏移 |
| CAN_RECNT | 0xB2 | 8 | 接收错误计数器 |
| CAN_TECNT | 0xB3 | 8 | 发送错误计数器 |
| CAN_ACFCTRL | 0xB4 | 8 | 筛选器组控制（ACFADR/SELMASK） |
| CAN_ACFEN | 0xB6 | 8 | 筛选器组使能 |
| CAN_ACF | 0xB8 | 32 | 筛选器 CODE/MASK |
| CAN_TBSLOT | 0xBE | 8 | TTCAN TB slot 指针 |
| CAN_TTCFG | 0xBF | 8 | TTCAN 配置 |
| CAN_REF_MSG | 0xC0 | 32 | TTCAN 参考消息 |
| CAN_TRG_CFG | 0xC4 | 16 | TTCAN 触发配置 |
| CAN_TT_TRIG | 0xC6 | 16 | TTCAN 触发时间 |
| CAN_TT_WTRIG | 0xC8 | 16 | TTCAN 触发看门时间 |

## 典型初始化流程

```c
/* 以 CAN FD 500kbit/s(仲裁) + 4Mbit/s(数据) 为例，40MHz 通信时钟 */

/* 1. 使能时钟 */
CLK_SetCANClockSrc(CLK_CAN2, CLK_CANCLK_XTAL_CLK);  /* 外部高速振荡器 */
FCG_Fcg1PeriphClockCmd(FCG1_PERIPH_CAN2, ENABLE);

/* 2. GPIO 配置 */
GPIO_SetFunc(GPIO_PORT_D, GPIO_PIN_05, GPIO_FUNC_62);  /* CAN2_TX */
GPIO_SetFunc(GPIO_PORT_D, GPIO_PIN_06, GPIO_FUNC_62);  /* CAN2_RX */

/* 3. CAN 初始化 */
stc_can_init_t stcCanInit;
CAN_StructInit(&stcCanInit);
stcCanInit.stcBitCfg.u32Prescaler = 1U;    /* 仲裁段：500kbit/s */
stcCanInit.stcBitCfg.u32TimeSeg1  = 64U;
stcCanInit.stcBitCfg.u32TimeSeg2  = 16U;
stcCanInit.stcBitCfg.u32SJW       = 16U;
stcCanInit.stcFDCfg.u8Mode        = CAN_FD_MD_BOSCH;  /* 或 ISO 模式 */
stcCanInit.stcFDCfg.stcFBT.u32Prescaler = 1U;  /* 数据段：4Mbit/s */
stcCanInit.stcFDCfg.stcFBT.u32TimeSeg1  = 8U;
stcCanInit.stcFDCfg.stcFBT.u32TimeSeg2  = 2U;
stcCanInit.stcFDCfg.stcFBT.u32SJW       = 2U;
CAN_Init(CM_CAN2, &stcCanInit);

/* 4. 配置筛选器 */
stc_can_filter_config_t stcFilter = {
    .u32ID = 0x00U, .u32IDMask = 0x1FFFFFFFU,  /* 接收所有 ID */
    .u32IDType = CAN_ID_STD_EXT
};
CAN_FilterConfig(CM_CAN2, &stcFilter, 1U);

/* 5. 退出复位模式，进入动作模式 */
```

## 常见陷阱与注意事项

1. **PCLK1 频率要求**：PCLK1 必须 ≥ 1.5× can_clk，否则控制逻辑时序异常
2. **通信时钟源必须为外部高速振荡器**：不可使用内部 RC 振荡器
3. **复位模式下才能配置位时序**：SBT、FBT、ACF 等寄存器只能在 RESET=1 时写入
4. **FD 推荐时钟**：建议使用 20/40/80MHz，不推荐任意频率
5. **SEG 设定规则**：必须满足 SEG_1 ≥ SEG_2+1 且 SEG_2 ≥ SJW
6. **TDC SSP 偏移**：建议与 F_segment1 设定值相同
7. **回环模式退出**：从回环模式返回正常模式应通过置位 RESET 复位实现
8. **单次发送判断**：不能仅依靠 TPIF 判断完成，需结合 BEIF 和 ALIF
9. **CAN FD 禁止时的兼容性**：控制器自动忽略 FD 帧，不返回 ACK
10. **节点关闭恢复**：TECNT>255 时进入节点关闭，需上电复位或接收 128 个隐性位序列恢复

## 官方例程索引

| 例程名 | 绝对路径 | 用途简述 |
|--------|---------|--------:|
| can_fd | `$EXAMPLES\can\can_fd` | CAN FD 收发演示 |

> `$EXAMPLES` = `D:\Dev\SDKs\HC32\HC32F4A0\HC32F4A0_DDL_Rev2.4.0\projects\ev_hc32f4a0_lqfp176\examples`

## 相关应用笔记

| 应用笔记 | 绝对路径 |
|---------|---------:|
| CAN 控制器未定义波形检测及恢复 | `D:\Library\10_Datasheets\11_MCU\HC32系列\HC32F4A0\AN_HC32F4A0系列CAN控制器未定义波形检测及恢复_Rev1.0` |
| 控制器局域网络 CAN | `D:\Library\10_Datasheets\11_MCU\HC32系列\HC32F4A0\AN_HC32F4A0系列的控制器局域网络CAN__Rev1.1` |

## 源文件引用

- **手册 Markdown**: `D:\Library\10_Datasheets\11_MCU\HC32系列\HC32F4A0\35-CANFD-CANFD控制器\35-CANFD-CANFD控制器.md`
- **手册 PDF**: `D:\Library\10_Datasheets\11_MCU\HC32系列\HC32F4A0\RM_HC32F4A0系列参考手册_Rev1.40.pdf`
