# HRPWM — 高精度 PWM

> ✅ 本知识卡已填充。最后更新：2026-03-25

## 模块概述

HRPWM（High-Resolution PWM）扩展 Timer6 的 PWM 信号分辨率，通过可编程延迟线将 1 个 PCLK0 时钟周期细分为多个单位延迟量，实现亚纳秒级边沿调整精度。搭配 TMR6 最多可产生 16 路高分辨率 PWM 波形（对应 TMR6_1~TMR6_8 的 PWMA/PWMB），主要面向数字电源、D 类功放、LED 驱动等场景。

## 关键特性

- 16 个独立通道（CH1~CH16），对应 TMR6_1~TMR6_8 的 PWMA/PWMB 输出
- 上升沿、下降沿可独立配置延迟量（PSEL / NSEL），范围 1~256 个单位延迟量
- 两个校准控制器：CALCR0（CH1~CH12）、CALCR1（CH13~CH16）
- 校准过程与通道功能独立，不影响 PWM 输出
- EN=0 时 PWM 信号直通，不产生额外延迟

## 功能导航大纲

| 区域 | 小节 | 关键内容 |
|------|------|----------|
| 概述 | 21.1 | 扩展 Timer6 PWM 分辨率 |
| 框图 | 21.2 | 校准控制器 + 16 通道延迟线 |
| **校准功能** | 21.3.1 | CALCR0/1 流程：CALEN→等待 ENDF→读 CALCODE |
| **高分辨率调整** | 21.3.2 | 通道流程：校准→NSEL/PSEL→NE/PE→EN |
| **使用注意** | 21.3.3 | PCLK0>120MHz; 仅峰/谷点改 NSEL/PSEL; STOP 模式 |
| 寄存器-通道控制 | 21.4.1 | CRn: EN/PE/NE/PSEL/NSEL |
| 寄存器-校准控制 | 21.4.2 | CALCRn: CALEN/ENDF/CALCODE |

## 寄存器速查

> BASE_ADDR: 0x4003C000

| 寄存器 | 偏移 | 用途 | 关键位字段 |
|--------|------|------|-----------|
| HRPWM_CR1~CR16 | 0x00~0x3C | 通道 1~16 控制 | **EN**[31] PE[30] NE[29] **PSEL**[15:8] **NSEL**[7:0] |
| HRPWM_CALCR0 | 0x50 | 校准控制 0 (CH1~12) | **CALEN**[15] **ENDF**[12](R) **CALCODE**[7:0] |
| HRPWM_CALCR1 | 0x54 | 校准控制 1 (CH13~16) | CALEN[15] ENDF[12](R) CALCODE[7:0] |

## 典型初始化流程

```c
/* === HRPWM 校准 + 通道配置 === */
// 1. 使能 HRPWM 时钟
FCG_Fcg1PeriphClockCmd(FCG1_PERIPH_HRPWM, ENABLE);

// 2. 校准：获取 1 个 PCLK0 内的单位延迟数
HRPWM_CalibrateCmd(HRPWM_CALIB_UNIT0, ENABLE);
while (HRPWM_GetCalibrateState(HRPWM_CALIB_UNIT0) != SET) { ; }
uint8_t u8CalCode = HRPWM_GetCalibratCode(HRPWM_CALIB_UNIT0);

// 3. 配置通道（以 CH1 = TMR6_1_PWMA 为例）
HRPWM_CHCmd(HRPWM_CH1, ENABLE);
HRPWM_SetFunc(HRPWM_CH1, HRPWM_RISING_EDGE_DELAY, (u8CalCode / 4U));
HRPWM_SetFunc(HRPWM_CH1, HRPWM_FALLING_EDGE_DELAY, 0U);

// 4. Timer6 正常配置 PWM 输出（见 19-timer6 知识卡）
```

## 常见陷阱与注意事项

1. ⚠️ **PCLK0 必须 > 120MHz**：低于此频率校准和延迟线无法正常工作
2. ⚠️ **动态修改 NSEL/PSEL 的时机**：只能在 TMR6 计数器的峰点或谷点更新，否则产生毛刺
3. ⚠️ **延迟段数不得超过 CALCODE**：溢出将导致延迟扩展到下一个 PCLK0 周期
4. ⚠️ **STOP 模式输出强制拉低**：HRPWM 输出在 STOP 模式下为低电平
5. ⚠️ **两个校准控制器独立**：CALCR0 负责 CH1~12，CALCR1 负责 CH13~16，CALCODE 可能不同
6. ⚠️ **HRPWM 仅调整边沿不改变频率**：周期/频率由 TMR6 的 PERAR 和分频决定

## 官方例程索引

| 例程名 | 绝对路径 | 用途简述 |
|--------|---------|---------|
| hrpwm_base | `$EXAMPLES\hrpwm\hrpwm_base` | 校准 + 通道基本配置，演示高分辨率 PWM 输出 |

> `$EXAMPLES` = `D:\Dev\SDKs\HC32\HC32F4A0\HC32F4A0_DDL_Rev2.4.0\projects\ev_hc32f4a0_lqfp176\examples`

## 相关应用笔记

暂无专门针对 HRPWM 的应用笔记。Timer6 PWM 相关可参考 19-timer6 知识卡。

## 源文件引用

- **手册 Markdown**: `D:\Library\10_Datasheets\11_MCU\HC32系列\HC32F4A0\20-HRPWM-高精度PWM\20-HRPWM-高精度PWM.md`
- **手册 PDF**: `D:\Library\10_Datasheets\11_MCU\HC32系列\HC32F4A0\RM_HC32F4A0系列参考手册_Rev1.40.pdf`
