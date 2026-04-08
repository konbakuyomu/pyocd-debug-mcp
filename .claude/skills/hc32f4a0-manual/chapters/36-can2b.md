# CAN2.0B — CAN2.0B 控制器

> ✅ 本知识卡已填充。最后更新：2026-03-25

## 模块概述

CAN2.0B 控制器对应 CAN 通道 1（CAN_1），部分型号还包含通道 2（CAN_2）。完全支持 CAN2.0A/CAN2.0B 协议，向上兼容 CAN FD（可自动忽略 FD 帧）。最高通信波特率 1Mbit/s。缓冲器架构与 CANFD 控制器相同：1 个 PTB + 3 个 STB（FIFO/优先级仲裁）+ 8 个 RB（FIFO）+ 16 组筛选器。支持 TTCAN（ISO11898-4 Level 1）。

## 关键特性

- **协议**：CAN2.0A / CAN2.0B，向上兼容 CAN FD（自动忽略 FD 帧，不返回 ACK）
- **波特率**：最高 1Mbit/s，支持 1~1/256 预分频，仅使用 SBT 寄存器（无 FBT 快速段）
- **通道**：CAN_1（全型号），CAN_2 取决于产品型号
- **发送缓冲器**：1 个 PTB（最高优先级）+ 3 个 STB（FIFO 或优先级仲裁模式）
- **接收缓冲器**：8 级 RB FIFO，错误/不接收的数据不覆盖已存储消息
- **筛选器**：16 组独立筛选器，支持 11 位标准 ID / 29 位扩展 ID
- **单次发送**：PTB/STB 均支持
- **特殊模式**：静默模式、内部/外部回环模式
- **TTCAN**：ISO11898-4 Level 1，16 位计时器，5 种触发方式
- **错误处理**：5 种错误类型，可编程警告阈值，TECNT/RECNT 计数器
- **数据长度**：最大 8 字节/帧（标准 CAN 帧）
- **时钟**：通信时钟 can_clk 源自外部高速振荡器，PCLK1 ≥ 1.5× can_clk

## 功能导航大纲

> 小节编号对应原始手册标题

| 区域 | 小节 | 关键内容 |
|------|------|----------|
| 简介 | 37.1 | CAN2.0B 总体功能描述，对应 CAN 通道 1(/2) |
| 系统框图 | 37.2 | 控制器架构 |
| 管脚说明 | 37.3 | CANn_TX/RX + 测试观测引脚（n=1~2） |
| 动作模式 | 37.4.1 | 复位模式 vs 动作模式 |
| 波特率 | 37.4.2 | SBT 位时间计算公式，推荐配置表 |
| 发送缓冲器 | 37.4.3 | PTB + STB，TBUF/TBSEL/TSNEXT |
| 接收缓冲器 | 37.4.4 | 8 级 RB FIFO，RBUF + RREL |
| 筛选器 | 37.4.5 | 16 组 ACF |
| 数据收发 | 37.4.6~9 | 发送/接收流程，单次发送，取消发送 |
| 错误处理 | 37.4.10~12 | 错误状态机，节点关闭恢复，仲裁失败捕捉 |
| 回环/静默 | 37.4.13~14 | 内部/外部回环，静默模式 |
| TTCAN | 37.4.16 | 时间触发通信 |
| 中断 | 37.4.18 | 14 种中断源 |
| 寄存器 | 37.5 | 寄存器详述 |
| 注意事项 | 37.6 | 总线抗干扰、噪声制约 |

## 寄存器速查

> CAN_1 基址: 0x40009000 | CAN_2 基址: 0x40078000

| 寄存器 | 偏移 | 位宽 | 用途 |
|--------|------|------|------|
| CAN_RBUF | 0x00~0x0F | - | 接收 BUF（4 字节头 + 最多 8 字节数据） |
| CAN_TBUF | 0x50~0x5F | - | 发送 BUF |
| CAN_CFG_STAT | 0xA0 | 8 | 配置状态（RESET/BUSOFF/TPSS/TSSS） |
| CAN_TCMD | 0xA1 | 8 | 发送命令（TPE/TSONE/TSALL/TPA/TSA/TBSEL） |
| CAN_TCTRL | 0xA2 | 8 | 发送控制（TSNEXT/TSMODE） |
| CAN_RCTRL | 0xA3 | 8 | 接收控制（RREL/ROM/SACK） |
| CAN_RTIE | 0xA4 | 8 | 收发中断使能 |
| CAN_RTIF | 0xA5 | 8 | 收发中断标志 |
| CAN_ERRINT | 0xA6 | 8 | 错误中断使能和标志 |
| CAN_LIMIT | 0xA7 | 8 | 错误警告限定 |
| CAN_SBT | 0xA8 | 32 | Slow 位时序（S_PRESC/S_SEG_1/S_SEG_2/S_SJW） |
| CAN_EALCAP | 0xB0 | 8 | 错误类型(KOER) + 仲裁失败位置(ALC) |
| CAN_RECNT | 0xB2 | 8 | 接收错误计数器 |
| CAN_TECNT | 0xB3 | 8 | 发送错误计数器 |
| CAN_ACFCTRL | 0xB4 | 8 | 筛选器组控制 |
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
/* 以 CAN1 经典模式 500kbit/s 为例 */

/* 1. 使能时钟 */
CLK_SetCANClockSrc(CLK_CAN1, CLK_CANCLK_XTAL_CLK);  /* 8MHz 外部晶振 */
FCG_Fcg1PeriphClockCmd(FCG1_PERIPH_CAN1, ENABLE);

/* 2. GPIO 配置 */
GPIO_SetFunc(GPIO_PORT_D, GPIO_PIN_05, GPIO_FUNC_60);  /* CAN1_TX */
GPIO_SetFunc(GPIO_PORT_D, GPIO_PIN_04, GPIO_FUNC_60);  /* CAN1_RX */

/* 3. CAN 初始化（8MHz 晶振下 500kbit/s） */
stc_can_init_t stcCanInit;
CAN_StructInit(&stcCanInit);
stcCanInit.stcBitCfg.u32Prescaler = 1U;
stcCanInit.stcBitCfg.u32TimeSeg1  = 12U;   /* (12+2) TQ */
stcCanInit.stcBitCfg.u32TimeSeg2  = 2U;    /* (2+1)  TQ → 总 16 TQ */
stcCanInit.stcBitCfg.u32SJW       = 2U;
CAN_Init(CM_CAN1, &stcCanInit);

/* 4. 配置筛选器 */
stc_can_filter_config_t stcFilter = {
    .u32ID = 0x00U, .u32IDMask = 0x1FFFFFFFU,
    .u32IDType = CAN_ID_STD_EXT
};
CAN_FilterConfig(CM_CAN1, &stcFilter, 1U);

/* 5. 退出复位模式 → 动作模式 */
```

## 常见陷阱与注意事项

1. **与 CANFD 控制器的区别**：CAN2.0B 无 FBT 寄存器、无 TDC/RDC，RBUF/TBUF 帧最大 8 字节（vs FD 64 字节）
2. **PCLK1 频率要求**：PCLK1 ≥ 1.5× can_clk
3. **通信时钟源必须为外部高速振荡器**
4. **复位模式下才能配置位时序**：SBT、ACF 等只能在 RESET=1 时写入
5. **SEG 设定规则**：SEG_1 ≥ SEG_2+1，SEG_2 ≥ SJW
6. **回环模式退出**：应通过置位 RESET 复位实现
7. **单次发送判断**：需结合 TPIF/BEIF/ALIF 一起判断
8. **FD 兼容性**：CAN FD 禁止时，控制器自动忽略 FD 帧不返回 ACK
9. **总线抗干扰**：恶劣电磁环境需增加电气隔离、屏蔽双绞线、信号保护器
10. **噪声制约**：应确保位时间满足标准协议要求，不满足宽度的噪声可能引起控制器异常

## 官方例程索引

| 例程名 | 绝对路径 | 用途简述 |
|--------|---------|--------:|
| can_classical | `$EXAMPLES\can\can_classical` | CAN2.0 经典模式收发 |
| can_loopback | `$EXAMPLES\can\can_loopback` | CAN 回环模式测试 |
| can_ttcan | `$EXAMPLES\can\can_ttcan` | CAN 时间触发通信（TTCAN） |

> `$EXAMPLES` = `D:\Dev\SDKs\HC32\HC32F4A0\HC32F4A0_DDL_Rev2.4.0\projects\ev_hc32f4a0_lqfp176\examples`

## 相关应用笔记

| 应用笔记 | 绝对路径 |
|---------|---------:|
| CAN 控制器未定义波形检测及恢复 | `D:\Library\10_Datasheets\11_MCU\HC32系列\HC32F4A0\AN_HC32F4A0系列CAN控制器未定义波形检测及恢复_Rev1.0` |
| 控制器局域网络 CAN | `D:\Library\10_Datasheets\11_MCU\HC32系列\HC32F4A0\AN_HC32F4A0系列的控制器局域网络CAN__Rev1.1` |

## 源文件引用

- **手册 Markdown**: `D:\Library\10_Datasheets\11_MCU\HC32系列\HC32F4A0\36-CAN2.0B-CAN2.0B控制器\36-CAN2.0B-CAN2.0B控制器.md`
- **手册 PDF**: `D:\Library\10_Datasheets\11_MCU\HC32系列\HC32F4A0\RM_HC32F4A0系列参考手册_Rev1.40.pdf`
