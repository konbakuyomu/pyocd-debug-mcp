# USART — 通用同步异步收发器

> ✅ 本知识卡已填充。最后更新：2026-03-25

## 模块概述

HC32F4A0 搭载 10 个独立 USART 单元（USART_1~10），支持 UART 异步全双工/半双工、时钟同步通信、智能卡接口（ISO/IEC 7816-3）和 LIN 总线等多种工作模式。各单元通过 TX/RX/CK/CTS/RTS 五根引脚通信，内建双缓冲收发结构、小数波特率发生器（8 单元支持）、数字滤波、接收超时（4 单元支持）、多处理器通信（站地址 + 静默模式）。USART_1 额外支持通过 RX 线唤醒 STOP 模式。USART_5/10 支持 LIN 总线（间隔段检测/发送、波特率同步测量、回环模式）。

## 关键特性

- 10 个独立单元，全双工异步/同步通信
- **UART 模式**：8/9 位数据、奇/偶/无校验、1/2 停止位、LSB/MSB 可选、CTS/RTS 调制解调器
- **时钟同步模式**：全通道支持，CK 引脚输出/输入时钟，8 位数据
- **智能卡接口**：USART 1~4, 6~9 支持，自动错误信号、数据重发
- **LIN 总线**：USART 5/10 支持，10/11/13/14 位间隔段发送，同步段测量，总线冲突检测
- 小数波特率：USART 1~4, 6~9 支持（FBME=1 使能 DIV_Fraction）
- 接收超时 TIMEOUT：USART 1/2/6/7 支持，配合 Timer0 检测帧间隔
- 多处理器通信：全通道支持，站地址 ID + 静默模式过滤
- 半双工：仅 TX 管脚，全通道支持
- 波特率公式：B = C / [8×(2-OVER8)×(DIV_Integer+1)]，最高 PCLK/8
- 数字滤波器（NFE）、下降沿/低电平开始位检测（SBS）
- USART_1 支持 STOP 模式唤醒

## 功能导航大纲

> 小节编号对应原始手册 `kuma_HC32F4A0手册_USART.md` 中的 29.x 标题。

| 区域 | 小节 | 关键内容 |
|------|------|----------|
| 概述 | 29.1-29.3 | 特性总述、系统框图、引脚说明（TX/RX/CK/CTS/RTS） |
| **UART 时钟** | 29.4.1.1 | 内部/外部时钟源选择（CLKC[1:0]）、波特率公式、最高波特率 |
| UART 数据格式 | 29.4.1.2 | 开始位+数据位(8/9)+校验+停止位(1/2) |
| 调制解调器 | 29.4.1.3 | CTS（流控接收）/ RTS（流控发送） |
| **UART 发送** | 29.4.1.4 | 9 步设定、TXE/TC 中断、双缓冲连续发送 |
| **UART 接收** | 29.4.1.5 | 开始位检测（低电平/下降沿）、采样容差、接收错误（PE/FE/ORE） |
| UART TIMEOUT | 29.4.1.6 | Timer0 联动、接收超时帧检测 |
| UART 唤醒 | 29.4.1.7 | USART_1 通过 RX 线唤醒 STOP 模式 |
| 多处理器 | 29.4.2 | 站地址 ID 发送/接收、静默模式自动过滤 |
| 时钟同步 | 29.4.3 | Master(内部时钟)/Slave(外部时钟)、全双工同步 |
| 智能卡 | 29.4.4 | ISO 7816-3、自动错误/重发、BCN 基本时钟数 |
| **LIN** | 29.4.5 | 间隔段发送/检测、同步段测量(LBMC)、总线冲突(BE)、回环 |
| 中断与 DMA | 29.4.6 | TI/TCI/RI/EI/RTOI/LBDI/WKUPI/BEI 八种中断 |
| 寄存器 | 29.5 | 10 个寄存器（含 LIN 专用 LBMC 和 USART1 专用 NFC） |

## 寄存器速查

> USART1: 0x4001CC00 ~ USART5: 0x4001DC00; USART6: 0x40020C00 ~ USART10: 0x40021C00

| 寄存器 | 偏移 | 用途 | 关键位字段 |
|--------|------|------|-----------|
| **USART_SR** | 0x00 | 状态寄存器 | PE FE ORE **RXNE** BE **TC TXE** RTOF WKUP LBD MPB |
| USART_TDR | 0x04 | 发送数据 | TDR[8:0] MPID[9] |
| USART_RDR | 0x06 | 接收数据 | RDR[8:0] MPB[9] |
| **USART_BRR** | 0x08 | 波特率 | DIV_Integer[15:8] DIV_Fraction[6:0] |
| **USART_CR1** | 0x0C | 控制 1（核心） | **TE[3] RE[2]** RIE[5] TXEIE[7] TCIE[6] RTOE[0] RTOIE[1] M[12] PCE[10] OVER8[15] FBME[29] SBS[31] NFE[30] ML[28] MS[24] 清零位:CPE~CRTOF |
| USART_CR2 | 0x10 | 控制 2 | CLKC[12:11] STOP[13] MPE[0] **LINEN[14]** LBDL SBKL SBK WKUPE |
| USART_CR3 | 0x14 | 控制 3 | HDSEL[3] CTSE[9] RTSE[8] SCEN[5] LOOP[4] BCN[23:21] |
| USART_PR | 0x18 | 预分频 | PSC[1:0]（PCLK/1/4/16/64）LBMPSC[3:2] |
| USART_LBMC | 0x1C | LIN 波特率测量 | LBMC[15:0]（仅 USART5/10） |

## 典型初始化流程

```c
/* === UART 中断收发（115200, 8N1） === */
// 1. 使能时钟
FCG_Fcg3PeriphClockCmd(FCG3_PERIPH_USART1, ENABLE);

// 2. 配置 GPIO 复用（TX/RX）
GPIO_SetFunc(GPIO_PORT_H, GPIO_PIN_15, GPIO_FUNC_32); // USART1_TX
GPIO_SetFunc(GPIO_PORT_H, GPIO_PIN_13, GPIO_FUNC_33); // USART1_RX

// 3. 初始化 UART
stc_usart_uart_init_t stcUartInit;
USART_UART_StructInit(&stcUartInit);
stcUartInit.u32ClockDiv      = USART_CLK_DIV64;
stcUartInit.u32Baudrate      = 115200UL;
stcUartInit.u32OverSampleBit = USART_OVER_SAMPLE_8BIT;
USART_UART_Init(CM_USART1, &stcUartInit, NULL);  // NULL=不关心实际误差

// 4. 注册中断（RX_FULL / RX_ERR / TX_EMPTY / TX_CPLT）
stc_irq_signin_config_t stcIrq;
stcIrq.enIntSrc    = INT_SRC_USART1_RI;
stcIrq.enIRQn      = INT001_IRQn;
stcIrq.pfnCallback = &USART_RxFull_Callback;
INTC_IrqSignIn(&stcIrq);
NVIC_ClearPendingIRQ(INT001_IRQn);
NVIC_SetPriority(INT001_IRQn, DDL_IRQ_PRIO_DEFAULT);
NVIC_EnableIRQ(INT001_IRQn);
// ... 同理注册 EI / TI / TCI ...

// 5. 使能接收 + 接收中断
USART_FuncCmd(CM_USART1, USART_RX | USART_INT_RX, ENABLE);
// TX 在有数据时按需使能：USART_FuncCmd(USART_TX | USART_INT_TX_EMPTY, ENABLE)
```

## 常见陷阱与注意事项

1. ⚠️ **CR1/CR2/CR3/BRR 必须在 TE=0 且 RE=0 时设置**：大部分配置位只能在收发器禁止状态下修改
2. ⚠️ **时钟差异**：USART 1~4 使用 PCLK3（APB3），USART 6~10 使用 PCLK6（APB6），波特率计算需对应正确的 PCLK
3. ⚠️ **小数波特率仅 8 单元支持**：USART 5/10 无 DIV_Fraction，FBME 位读出为 0
4. ⚠️ **接收超时仅 4 单元支持**：USART 1/2/6/7，需配合 Timer0 使用，RTOE=1 + RTOIE=1
5. ⚠️ **ORE 后无法继续接收**：上溢错误后必须清除 ORE（写 CORE=1）才能恢复接收
6. ⚠️ **PE/FE 错误后数据保留但 RI 不触发**：发生校验/帧错误时数据被保存但不产生接收中断
7. ⚠️ **TXEIE=1 写入时机**：TE=1 时写 TXEIE=1 须等待 TC=1 后才能写入，否则可能丢失中断
8. ⚠️ **LIN 仅 USART 5/10**：其他单元的 LIN 相关位必须保持复位值
9. ⚠️ **半双工 TX 管脚双用**：HDSEL=1 时仅使用 TX 管脚，RX 管脚可作通用 IO
10. ⚠️ **DMA 收发每次请求仅读写一次**：通过 DMA 中断/请求读取接收数据或写入发送数据时，一次请求只能操作一次

## 官方例程索引

| 例程名 | 绝对路径 | 用途简述 |
|--------|---------|---------:|
| usart_uart_polling | `$EXAMPLES\usart\usart_uart_polling` | UART 轮询收发回显（最简模式） |
| usart_uart_int | `$EXAMPLES\usart\usart_uart_int` | UART 中断收发 + 环形缓冲（标准模型） |
| usart_uart_dma | `$EXAMPLES\usart\usart_uart_dma` | UART DMA + TMR0 接收超时 + LLP 自动重装 |
| usart_uart_halfduplex_polling | `$EXAMPLES\usart\usart_uart_halfduplex_polling` | UART 半双工轮询（仅 TX 管脚） |
| usart_uart_halfduplex_int | `$EXAMPLES\usart\usart_uart_halfduplex_int` | UART 半双工中断（Master/Slave 切换） |
| usart_uart_multiprocessor | `$EXAMPLES\usart\usart_uart_multiprocessor` | 多处理器通信（站地址 ID + 静默模式） |
| usart_clocksync_polling | `$EXAMPLES\usart\usart_clocksync_polling` | 时钟同步轮询（Master 内部时钟 / Slave 外部时钟） |
| usart_clocksync_int | `$EXAMPLES\usart\usart_clocksync_int` | 时钟同步中断收发 |
| usart_clocksync_dma | `$EXAMPLES\usart\usart_clocksync_dma` | 时钟同步 DMA 收发 |
| usart_smartcard_atr | `$EXAMPLES\usart\usart_smartcard_atr` | 智能卡 ATR 接收（冷复位序列） |
| usart_lin | `$EXAMPLES\usart\usart_lin` | LIN 总线 Slave 收发（中间件封装） |

> `$EXAMPLES` = `D:\Dev\SDKs\HC32\HC32F4A0\HC32F4A0_DDL_Rev2.4.0\projects\ev_hc32f4a0_lqfp176\examples`

## 相关应用笔记

| AN 名称 | 路径 |
|---------|------|
| UART 不定长数据接收 | `$MANUAL\AN_HC32F4A0系列的通用同步异步收发器的UART不定长数据接收_Rev1.1\` |

## 源文件引用

- **手册 Markdown**: `D:\Library\10_Datasheets\11_MCU\HC32系列\HC32F4A0\28-USART-通用同步异步收发器\kuma_HC32F4A0手册_USART.md`
- **手册 PDF**: `D:\Library\10_Datasheets\11_MCU\HC32系列\HC32F4A0\RM_HC32F4A0系列参考手册_Rev1.40.pdf`
