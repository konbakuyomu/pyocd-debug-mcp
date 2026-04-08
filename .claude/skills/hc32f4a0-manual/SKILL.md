---
name: hc32f4a0-manual
description: HC32F4A0 芯片参考手册+数据手册知识库。查询 MCU 外设寄存器配置、初始化流程、时钟树、中断、DMA、定时器、USART、SPI、I2C、ADC、DAC、CAN、USB、以太网、EXMC 等模块，以及芯片选型、引脚配置、5V耐压、电气参数、功耗特性时使用。Use when user asks about HC32F4A0 peripheral registers, initialization, clock tree, GPIO, timer, communication interfaces, chip selection, pinout, electrical characteristics, or any on-chip module.
---

# HC32F4A0 参考手册知识库

## 何时使用

- 用户询问 HC32F4A0 任何外设模块的寄存器、配置、初始化方法
- 用户需要某个模块的典型用法或官方例程参考
- 用户调试 HC32F4A0 相关代码，需要查阅手册确认行为
- 用户询问芯片选型（型号对比、封装、Flash 大小、CAN FD 支持）
- 用户询问引脚配置（5V 耐压、Func Group 分组、引脚复用）
- 用户询问电气参数（功耗、时钟源特性、绝对最大额定值、外设时序）

## 检索策略

1. **先读索引**：阅读 [00-index.md](00-index.md) 定位目标章节编号和对应文件路径
2. **读章节知识卡**：阅读 `chapters/<编号>-<模块名>.md` 获取精炼知识
3. **按需深入**：如果知识卡信息不足，根据卡中记录的绝对路径去读原始手册 Markdown 或 SDK 例程源码
4. **单次只读 1 个章节**，禁止批量读入多个章节

## 核心规则

1. 回答必须引用具体寄存器名称和位字段，标注来源章节编号
2. 涉及例程时，给出例程名称和关键代码片段，不要照搬整个文件

## 章节导航

| # | 模块 | 知识卡 |
|---|------|--------|
| 1 | 存储器映射+总线架构 | [chapters/01-memory-map.md](chapters/01-memory-map.md) |
| 2 | RMU 复位控制 | [chapters/02-rmu.md](chapters/02-rmu.md) |
| 3 | CMU 时钟控制器 | [chapters/03-cmu.md](chapters/03-cmu.md) |
| 4 | PWC 电源控制 | [chapters/04-pwc.md](chapters/04-pwc.md) |
| 5 | ICG 初始化配置 | [chapters/05-icg.md](chapters/05-icg.md) |
| 6 | EFM 嵌入式 FLASH | [chapters/06-efm.md](chapters/06-efm.md) |
| 7 | SRAM 内置 SRAM | [chapters/07-sram.md](chapters/07-sram.md) |
| 8 | GPIO 通用 IO | [chapters/08-gpio.md](chapters/08-gpio.md) |
| 9 | INTC 中断控制器 | [chapters/09-intc.md](chapters/09-intc.md) |
| 10 | AOS 自动运行系统 | [chapters/10-aos.md](chapters/10-aos.md) |
| 11 | MPU 存储保护单元 | [chapters/11-mpu.md](chapters/11-mpu.md) |
| 12 | KEYSCAN 键盘扫描 | [chapters/12-keyscan.md](chapters/12-keyscan.md) |
| 13 | CTC 内部时钟校准器 | [chapters/13-ctc.md](chapters/13-ctc.md) |
| 14 | DMA 控制器 | [chapters/14-dma.md](chapters/14-dma.md) |
| 15 | CMP 电压比较器 | [chapters/15-cmp.md](chapters/15-cmp.md) |
| 16 | ADC 模数转换 | [chapters/16-adc.md](chapters/16-adc.md) |
| 17 | DAC 数模转换器 | [chapters/17-dac.md](chapters/17-dac.md) |
| 18 | OTS 温度传感器 | [chapters/18-ots.md](chapters/18-ots.md) |
| 19 | Timer6 高级控制定时器 | [chapters/19-timer6.md](chapters/19-timer6.md) |
| 20 | HRPWM 高精度 PWM | [chapters/20-hrpwm.md](chapters/20-hrpwm.md) |
| 21 | Timer4 通用控制定时器 | [chapters/21-timer4.md](chapters/21-timer4.md) |
| 22 | EMB 紧急刹车模块 | [chapters/22-emb.md](chapters/22-emb.md) |
| 23 | TimerA 通用定时器 | [chapters/23-timera.md](chapters/23-timera.md) |
| 24 | Timer2 通用定时器 | [chapters/24-timer2.md](chapters/24-timer2.md) |
| 25 | Timer0 通用定时器 | [chapters/25-timer0.md](chapters/25-timer0.md) |
| 26 | RTC 实时时钟 | [chapters/26-rtc.md](chapters/26-rtc.md) |
| 27 | SWDT 看门狗计数器 | [chapters/27-swdt.md](chapters/27-swdt.md) |
| 28 | USART 通用同步异步收发器 | [chapters/28-usart.md](chapters/28-usart.md) |
| 29 | I2C 集成电路总线 | [chapters/29-i2c.md](chapters/29-i2c.md) |
| 30 | SPI 串行外设接口 | [chapters/30-spi.md](chapters/30-spi.md) |
| 31 | QSPI 四线串行外设接口 | [chapters/31-qspi.md](chapters/31-qspi.md) |
| 32 | I2S 音频总线 | [chapters/32-i2s.md](chapters/32-i2s.md) |
| 33 | USBHS USB2.0 高速 | [chapters/33-usbhs.md](chapters/33-usbhs.md) |
| 34 | USBFS USB2.0 全速 | [chapters/34-usbfs.md](chapters/34-usbfs.md) |
| 35 | CANFD 控制器 | [chapters/35-canfd.md](chapters/35-canfd.md) |
| 36 | CAN2.0B 控制器 | [chapters/36-can2b.md](chapters/36-can2b.md) |
| 37 | SDIOC SDIO 控制器 | [chapters/37-sdioc.md](chapters/37-sdioc.md) |
| 38 | ETHMAC 以太网 MAC | [chapters/38-ethmac.md](chapters/38-ethmac.md) |
| 39 | EXMC 外部存储器控制器 | [chapters/39-exmc.md](chapters/39-exmc.md) |
| 40 | DVP 数字视频接口 | [chapters/40-dvp.md](chapters/40-dvp.md) |
| 41 | CPM 加密协处理模块 | [chapters/41-cpm.md](chapters/41-cpm.md) |
| 42 | CRC 运算 | [chapters/42-crc.md](chapters/42-crc.md) |
| 43 | DCU 数据计算单元 | [chapters/43-dcu.md](chapters/43-dcu.md) |
| 44 | MAU 数学运算单元 | [chapters/44-mau.md](chapters/44-mau.md) |
| 45 | FMAC 滤波数学加速器 | [chapters/45-fmac.md](chapters/45-fmac.md) |
| 46 | DBGC 调试控制器 | [chapters/46-dbgc.md](chapters/46-dbgc.md) |
| DS-1 | 芯片概览与选型 | [chapters/ds-overview.md](chapters/ds-overview.md) |
| DS-2 | 引脚配置与复用 | [chapters/ds-pinouts.md](chapters/ds-pinouts.md) |
| DS-3 | 电气特性速查 | [chapters/ds-electrical.md](chapters/ds-electrical.md) |

## 何时加载 supporting files

| 需求 | 阅读 |
|------|------|
| 查找某模块对应的手册/例程路径 | [00-index.md](00-index.md) |
| 了解章节知识卡的编写标准 | [chapter-template.md](chapter-template.md) |
| 查询具体模块知识 | 上方导航表中对应的 `chapters/*.md` |
| 芯片选型、封装对比 | [chapters/ds-overview.md](chapters/ds-overview.md) |
| 引脚 5V 耐压、复用分组 | [chapters/ds-pinouts.md](chapters/ds-pinouts.md) |
| 功耗、电气参数、时钟源特性 | [chapters/ds-electrical.md](chapters/ds-electrical.md) |
