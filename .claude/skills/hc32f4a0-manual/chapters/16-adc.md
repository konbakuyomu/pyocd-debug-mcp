# ADC — 模数转换模块

> ✅ 本知识卡已填充。最后更新：2026-03-25

## 模块概述

HC32F4A0 搭载 3 个 12 位逐次逼近型 ADC 单元（ADC1/ADC2 各 16 通道，ADC3 有 20 通道），共 28 个外部模拟输入 + 2 个内部模拟输入（内部基准电压、VBAT 分压）。支持虚拟通道映射、双序列扫描（A/B 独立触发，B 优先级高于 A）、多次转换平均、模拟看门狗、PGA 可编程增益放大、专用采样保持电路（SH）、以及多 ADC 协同工作模式（并行/延迟触发）。转换时钟 PCLK2 最高 60MHz，最高采样率 2.5MSPS。

## 关键特性

- 3 个 ADC 单元：ADC1/2 各 16 通道 (CH0~15)，ADC3 有 20 通道 (CH0~19)
- 分辨率可配 12/10/8 位（ADC_CR0.ACCSEL）
- 转换时钟 PCLK2 最高 60MHz；PCLK4:PCLK2 比率可选 1:1/2:1/4:1/8:1/1:2/1:4
- 2 个扫描序列 A/B，各自独立选通道和触发源；序列 B 优先级 > A
- 触发源：软件(STR)、外部引脚(ADTRGx 下降沿)、内部事件(IN_TRGx0/x1 经 AOS 路由)
- 虚拟通道↔物理通道可自由映射（ADC_CHMUXR0~3）
- 数据平均：同一通道连续 2/4/8/16/32/64/128/256 次转换取平均
- 模拟看门狗 AWD0/AWD1：窗口内/外比较，可组合（OR/AND/XOR）
- PGA 可编程增益放大器：ADC1 有 PGA1~3，ADC2 有 PGA4；增益 ×2~×32
- 专用采样保持 SH：仅 ADC1 CH0~2，三路同时采样后依次转换
- 多 ADC 协同模式：单次/循环 × 并行/延迟触发，ADC1 为主控
- 4 种事件输出：EOCA/EOCB/CMP0/CMP1，均可触发 DMA
- 数据寄存器自动清除功能（ADC_CR0.CLREN）

## 功能导航大纲

> 小节编号对应原始手册 `16-ADC-模数转换模块.md` 中的标题。

| 区域 | 小节 | 关键内容 |
|------|------|----------|
| 概述 | 17.1-17.2 | 特性列表、3 单元规格表、框图 |
| **ADC 时钟** | 17.3.1 | PCLK2(转换时钟) + PCLK4(数字接口)；PCLK2≤60MHz |
| **通道选择** | 17.3.2 | 虚拟↔物理通道映射(CHMUXR)；扩展通道 EXCHSELR |
| **触发源** | 17.3.3 | 软件/ADTRGx 引脚/IN_TRGx0,1(AOS) |
| **序列 A 单次扫描** | 17.3.4 | MS=00b，STRT 触发，EOCAF 标志 |
| 序列 A 连续扫描 | 17.3.5 | MS=01b，STRT 不自动清零，推荐 DMA 读取 |
| **双序列扫描** | 17.3.6 | MS=10b/11b，A/B 独立触发，B 可抢占 A |
| 模拟看门狗 | 17.3.7 | AWD0/1 窗口比较 + 组合(OR/AND/XOR) |
| 采样/转换时间 | 17.3.8 | tconv = tSPL + tCMP；SSTR 可独立编程 |
| DR 自动清除 | 17.3.9 | CLREN=1 读后自动清零 |
| **数据平均** | 17.3.10 | AVCNT 选次数 + AVCHSELR 选通道 |
| PGA 增益放大 | 17.3.11 | PGA1~4，增益 ×2~×32，需使能 CMBIAS |
| 采样保持 SH | 17.3.12 | 仅 ADC1 CH0~2，需使能 CMBIAS |
| **协同工作模式** | 17.3.13 | 4 种模式，ADC1 为主；禁用序列 B |
| 中断与事件 | 17.3.14 | EOCA/EOCB/CMP0/CMP1 均可触发 DMA |
| 寄存器 | 17.4 | STR/CR0/CR1/TRGSR/CHSELR/SSTR/DR/AWD/SYNCCR/PGA/SH |

## 寄存器速查

> ADC1 BASE: 0x40040000, ADC2: 0x40040400, ADC3: 0x40040800

| 寄存器 | 偏移 | 用途 | 关键位字段 |
|--------|------|------|-----------|
| ADC_STR | 0x00 | 启动/停止 | STRT[0] |
| **ADC_CR0** | 0x02 | 控制寄存器 0 | DFMT[7] CLREN[6] ACCSEL[5:4] **MS[1:0]** AVCNT[10:8] |
| ADC_CR1 | 0x04 | 控制寄存器 1 | RSCHSEL[2]（序列A被B打断后重启方式） |
| **ADC_TRGSR** | 0x0A | 触发源选择 | TRGENB[15] TRGSELB[9:8] TRGENA[7] **TRGSELA[1:0]** |
| **ADC_CHSELRA** | 0x0C | 序列 A 通道选择 | CHSELA[31:0]（每位选一通道） |
| ADC_CHSELRB | 0x10 | 序列 B 通道选择 | CHSELB[31:0] |
| ADC_AVCHSELR | 0x14 | 平均通道选择 | 每位选一通道参与平均 |
| ADC_EXCHSELR | 0x18 | 扩展通道源 | 0=外部 ADCx_IN15, 1=内部模拟 |
| ADC_SSTRx | 0x20+x | 通道采样周期 | SST[7:0]（×PCLK2 周期） |
| ADC_CHMUXR0~3 | 0x38~0x3E | 通道映射 | 每 4bit 映射 1 个虚拟通道 |
| **ADC_DRy** | 0x50+2*y | 转换数据 | DR[15:0]（16bit） |
| ADC_ISR | 0x44 | 中断状态 | EOCAF[0] EOCBF[1] |
| ADC_ICR | 0x45 | 中断使能 | EOCAIEN[0] EOCBIEN[1] |
| ADC_SYNCCR | 0x4C | 协同模式控制 | SYNCEN[15] SYNCMD[14:12] SYNCDLY[7:0] |
| ADC_AWDCR | 0xA0 | 看门狗控制 | AWD0EN/AWD1EN, AWD0MD/AWD1MD, AWDCM[1:0] |
| ADC_SHCR | 0x1A | 采样保持控制 | SHSEL[2:0], SHSST[7:0] |
| ADC_PGACRn | 0xC0+n | PGA 控制 | PGAEN, GAIN[3:0] |

## 典型初始化流程

```c
/* === ADC 基本软件触发 + 轮询采集 === */
// 1. 使能外设时钟
FCG_Fcg3PeriphClockCmd(FCG3_PERIPH_ADC1, ENABLE);

// 2. 初始化 ADC（单次扫描, 12bit, 右对齐）
stc_adc_init_t stcAdcInit;
ADC_StructInit(&stcAdcInit);
// stcAdcInit.u16ScanMode = ADC_MD_SEQA_SINGLESHOT;  // 默认值
// stcAdcInit.u16Resolution = ADC_RESOLUTION_12BIT;   // 默认值
ADC_Init(CM_ADC1, &stcAdcInit);

// 3. GPIO 设为模拟模式
stc_gpio_init_t stcGpioInit;
GPIO_StructInit(&stcGpioInit);
stcGpioInit.u16PinAttr = PIN_ATTR_ANALOG;
GPIO_Init(GPIO_PORT_A, GPIO_PIN_03, &stcGpioInit);

// 4. 使能通道 + 设置采样时间
ADC_ChCmd(CM_ADC1, ADC_SEQ_A, ADC_CH3, ENABLE);
ADC_SetSampleTime(CM_ADC1, ADC_CH3, 0x40U);

// 5. [可选] 数据平均
ADC_ConvDataAverageConfig(CM_ADC1, ADC_AVG_CNT8);
ADC_ConvDataAverageChCmd(CM_ADC1, ADC_CH3, ENABLE);

// 6. 软件触发 + 轮询
ADC_Start(CM_ADC1);
while (ADC_GetStatus(CM_ADC1, ADC_FLAG_EOCA) != SET) {}
ADC_ClearStatus(CM_ADC1, ADC_FLAG_EOCA);
u16Val = ADC_GetValue(CM_ADC1, ADC_CH3);

/* === 硬件触发 + DMA 读取（高频场景推荐） === */
// ADC 序列 A 硬件触发
ADC_TriggerConfig(CM_ADC1, ADC_SEQ_A, ADC_HARDTRIG_ADTRG_PIN);
ADC_TriggerCmd(CM_ADC1, ADC_SEQ_A, ENABLE);
// DMA 由 EOCA 事件触发自动搬运 ADC_DR
AOS_SetTriggerEventSrc(AOS_DMA1_0, EVT_SRC_ADC1_EOCA);
```

## 常见陷阱与注意事项

1. ⚠️ **模拟引脚必须设 PIN_ATTR_ANALOG**：GPIO 引脚用作 ADC 输入前须设置模拟属性，否则数字缓冲器干扰采样
2. ⚠️ **PCLK2 不超过 60MHz**：转换时钟超频会导致精度下降
3. ⚠️ **序列 A 和 B 不要选相同通道**：会引起采样冲突
4. ⚠️ **STRT=1 时写 1 无效**：只能在 ADC 空闲时软件触发
5. ⚠️ **连续扫描推荐 DMA 读取**：扫描间隔短，轮询/中断可能来不及处理导致数据丢失
6. ⚠️ **所有配置寄存器必须在 STRT=0 时设置**
7. ⚠️ **PGA/SH 需先使能 CMBIAS 时钟**：`FCG_Fcg3PeriphClockCmd(FCG3_PERIPH_CMBIAS, ENABLE)` + 等待 ≥2μs 稳定
8. ⚠️ **SH 仅 ADC1 CH0~2 支持**：SH 有效时对应虚拟通道固定映射 ADC123_IN0~2，不支持通道重映射
9. ⚠️ **双序列模式下序列 B 可抢占 A**：RSCHSEL 决定 A 被打断后是续传还是重头扫描
10. ⚠️ **协同模式禁用序列 B**：否则破坏同步时序；软件触发(STR)在协同模式下无效
11. ⚠️ **扩展通道切换内部模拟源后需等 ≥50μs**：PWC_SetPowerMonitorVoltageSrc 切换后需要延时
12. ⚠️ **同一模拟通道禁止多 ADC 同时采样**：协同模式下同一物理通道同一时刻只能给一个 ADC 采样

## 官方例程索引

| 例程名 | 绝对路径 | 用途简述 |
|--------|---------|---------|
| adc_base | `$EXAMPLES\adc\adc_base` | 基础软件触发+轮询采集，含采样时间和数据平均 |
| adc_hard_trigger | `$EXAMPLES\adc\adc_hard_trigger` | 序列 A ADTRG 引脚触发 + 序列 B TMR0 事件触发，中断读值 |
| adc_dma | `$EXAMPLES\adc\adc_dma` | ADTRG 触发 + DMA 自动搬运多通道数据 |
| adc_awd | `$EXAMPLES\adc\adc_awd` | 模拟看门狗 AWD0 窗口内比较 + 中断 |
| adc_pga | `$EXAMPLES\adc\adc_pga` | PGA 可编程增益放大（增益 ×2.286），比较放大前后的值 |
| adc_sample_hold | `$EXAMPLES\adc\adc_sample_hold` | ADC1 专用采样保持 SH，CH0~2 同时采样 |
| adc_sync_mode | `$EXAMPLES\adc\adc_sync_mode` | ADC1+ADC2 协同模式（单次延迟/并行/循环） |
| adc_channel_remap | `$EXAMPLES\adc\adc_channel_remap` | 虚拟通道重映射（PA3→CH0） |
| adc_extended_channel | `$EXAMPLES\adc\adc_extended_channel` | 扩展通道采集内部基准电压和 VBAT/2 |

> `$EXAMPLES` = `D:\Dev\SDKs\HC32\HC32F4A0\HC32F4A0_DDL_Rev2.4.0\projects\ev_hc32f4a0_lqfp176\examples`

## 相关应用笔记

| 笔记名 | 路径 | 关键内容 |
|--------|------|----------|
| 如何提高ADC采样精度 | `$MANUAL\AN_如何提高ADC采样精度_Rev1.0` | ADC 采样精度优化方法 |
| Timer4 与 ADC 联动 | `$MANUAL\AN_TIMER4与ADC模块在电机FOC控制中单电阻采样联动操作说明_Rev1.02` | 电机 FOC 中 Timer4 触发 ADC 单电阻采样 |

> `$MANUAL` = `D:\Library\10_Datasheets\11_MCU\HC32系列\HC32F4A0`

## 源文件引用

- **手册 Markdown**: `D:\Library\10_Datasheets\11_MCU\HC32系列\HC32F4A0\16-ADC-模数转换模块\16-ADC-模数转换模块.md`
- **手册 PDF**: `D:\Library\10_Datasheets\11_MCU\HC32系列\HC32F4A0\RM_HC32F4A0系列参考手册_Rev1.40.pdf`
