# DS-Overview — 芯片概览与选型

> ✅ 本知识卡已填充。最后更新：2026-03-26

## 模块概述

HC32F4A0 系列是基于 ARM Cortex-M4F 内核（FPU+DSP）的高性能 MCU，最高主频 240MHz（300DMIPS / 825CoreMarks）。内置最大 2MB dual-bank Flash + 512+4KB SRAM，支持 1.8~3.6V 宽电压、-40~105°C 宽温。提供 6 种封装（100~208 pin），覆盖高性能变频控制、数字电源、IoT 等场景。

## 型号命名规则

```
HC32F4A0 □ □ □ □ - 封装
           │ │ │ └─ B = Rev.B
           │ │ └── T = LQFP / H = BGA
           │ └─── I = 2MB Flash / G = 1MB Flash
           └──── T = TFBGA208 / S = 176pin / R = 144pin / P = 100pin
```

示例：`HC32F4A0SITB-LQFP176` = 176pin LQFP、2MB Flash、Rev.B

## 型号功能对比速查

| 型号后缀 | 封装 | 尺寸(mm) | 引脚 | GPIO | 5V耐压GPIO | Flash | CAN |
|----------|------|----------|------|------|-----------|-------|-----|
| TIHB | TFBGA208 | 13×13 | 208 | 142 | 134 | 2MB | 2.0B+FD |
| SIHB | VFBGA176 | 10×10 | 176 | 142 | 134 | 2MB | 2.0B+FD |
| SITB | LQFP176 | 24×24 | 176 | 142 | 134 | 2MB | 2.0B+FD |
| SGHB | VFBGA176 | 10×10 | 176 | 142 | 134 | 1MB | 2×2.0B |
| SGTB | LQFP176 | 24×24 | 176 | 142 | 134 | 1MB | 2×2.0B |
| RITB | LQFP144 | 20×20 | 144 | 116 | 112 | 2MB | 2×2.0B |
| RGTB | LQFP144 | 20×20 | 144 | 116 | 112 | 1MB | 2×2.0B |
| PIHB | VFBGA100 | 7×7 | 100 | 83 | 79 | 2MB | 2×2.0B |
| PITB | LQFP100 | 14×14 | 100 | 83 | 79 | 2MB | 2×2.0B |
| PGTB | LQFP100 | 14×14 | 100 | 83 | 79 | 1MB | 2×2.0B |

**型号间差异仅在**：封装/引脚数、Flash 大小（1MB/2MB）、CAN FD 支持（仅 xIxB 的 176+pin 型号）。其余外设（SRAM 512+4KB、ADC×3、DAC×4、USART×10、SPI×6、I2C×6、USB×2、ETH×1 等）全系一致。

**ADC 通道数随封装变化**：176+pin = 28ch，144pin = 24ch，100pin = 16ch。

## 封装信息速查

| 封装 | 尺寸(mm) | 引脚间距 | 热阻 θJA(°C/W) | PCB Pad Pitch |
|------|----------|---------|---------------|---------------|
| LQFP100 | 14×14 | 0.5mm | 50 ±10% | — |
| VFBGA100 | 7×7 | 0.5mm | 42 ±10% | Dpad 0.29mm |
| LQFP144 | 20×20 | 0.5mm | 45 ±10% | — |
| LQFP176 | 24×24 | 0.5mm | 30 ±10% | — |
| VFBGA176 | 10×10 | 0.65mm | — | Dpad 0.28mm |
| TFBGA208 | 13×13 | 0.8mm | — | Dpad 0.40mm |

## 结温计算

```
Tj = TA + (PD × θJA)
PD = PINT + PI/O
PINT = ICC × VCC
PI/O = Σ(VOL × IOL) + Σ((VCC - VOH) × IOH)
```

Tj 不得超过 125°C（绝对最大结温）。

## 典型应用领域

高性能变频控制、数字电源、智能硬件、IoT 连接模块

## 常见选型陷阱

1. ⚠️ CAN FD 仅限 176+pin 且 Flash=2MB 的型号（TIHB/SIHB/SITB），1MB 型号均为 2×CAN 2.0B
2. ⚠️ ADC 通道数随封装变化：28ch（176+pin）/ 24ch（144pin）/ 16ch（100pin）
3. ⚠️ 5V 耐压 GPIO 并非全部引脚——PA0/PA1/PA2/PA6/PA11/PA12/PB14/PB15 不支持 5V 耐压
4. ⚠️ BGA 封装无热阻数据（VFBGA176/TFBGA208），需自行热仿真
5. ⚠️ 所有型号 SRAM 均为 512+4KB（4KB 为掉电保持 SRAMB），不因封装而变

## 交叉引用

- 引脚复用详情 → [ds-pinouts.md](ds-pinouts.md)
- 电气参数详情 → [ds-electrical.md](ds-electrical.md)
- 存储器映射 → [01-memory-map.md](01-memory-map.md)
- 时钟树 → [03-cmu.md](03-cmu.md)
- 电源控制 → [04-pwc.md](04-pwc.md)

## 相关应用笔记

| 笔记名 | 路径 | 关键内容 |
|--------|------|----------|
| 小华半导体 MCU 硬件设计指南（Rev1.00） | `$MANUAL\AN_小华半导体MCU硬件设计指南_Rev1.00\AN_小华半导体MCU硬件设计指南_Rev1.00.md` | 通用 MCU 最小系统、电源/VCAP、振荡器与调试接口设计 |
| 小华半导体 MCU 硬件设计指南（Rev1_1.00 目录） | `$MANUAL\AN_小华半导体MCU硬件设计指南_Rev1_1.00\AN_小华半导体MCU硬件设计指南_Rev1.00.md` | 特殊引脚、EMC、去耦、电源地与 IO 处理建议 |

> `$MANUAL` = `D:\Library\10_Datasheets\11_MCU\HC32系列\HC32F4A0`

## 源文件引用

- **数据手册 Markdown**: `D:\Library\10_Datasheets\11_MCU\HC32系列\HC32F4A0\DS_HC32F4A0系列数据手册_Rev1.60\DS_HC32F4A0系列数据手册_Rev1.60.md`
- **数据手册 PDF**: `D:\Library\10_Datasheets\11_MCU\HC32系列\HC32F4A0\DS_HC32F4A0系列数据手册_Rev1.60\DS_HC32F4A0系列数据手册_Rev1.60.pdf`
