# CMU — 时钟控制器

> ✅ 本知识卡已填充。最后更新：2026-03-25

## 模块概述

HC32F4A0 的时钟控制单元 (CMU) 管理芯片全部时钟源和时钟分配。提供 XTAL（4~25MHz 外部高速）、XTAL32（32.768kHz 外部低速）、HRC（16/20MHz 内部高速）、MRC（8MHz 内部中速）、LRC（32.768kHz 内部低速）、RTCLRC、SWDTLRC（10kHz）共 7 种振荡源，以及 PLLH/PLLA 两个 PLL。系统时钟最高 240MHz，通过 CMU_SCFGR 分频后产生 HCLK、PCLK0~4、EXCLK 等内部总线时钟。还提供 FCM 时钟频率测量、MCO 时钟输出、XTAL 故障检测等功能。

## 关键特性

- 6 种系统时钟源可选：HRC / MRC / LRC / XTAL / XTAL32 / PLLH
- PLLH：VCO 600~1200MHz，三路独立输出 P/Q/R（2~16 分频），PLLHP 驱动系统时钟最高 240MHz
- PLLA：VCO 240~480MHz，三路独立输出 P/Q/R，为 USB/I2S/CAN/ADC 等提供独立时钟
- 7 级总线分频：HCLK / PCLK0~4 / EXCLK 各自独立 1~64 分频
- 外设独立时钟选择：USB(UCLK)、CAN(CANCLK)、ADC/TRNG/DAC(PERICKSEL)、I2S(I2SCKSEL)
- MCO 时钟输出：2 路（MCO_1/MCO_2），支持 1~128 分频，最高 100MHz
- XTAL 故障检测：检测到故障时可自动切换到 MRC、触发中断或复位、联动 EMB 刹车
- FCM 时钟频率测量：可测量任意时钟源频率，超限可中断或复位

## 功能导航大纲

> 小节编号对应原始手册 `kuma_HC32F4A0手册_CMU.md` 中的标题。

| 区域 | 小节 | 关键内容 |
|------|------|----------|
| 概述 | 4.1 | 时钟源列表、系统时钟源选择 |
| 系统框图 | 4.2.1-4.2.2 | **时钟树框图**、FCM 框图 |
| **时钟源规格** | 4.3 | 9 种时钟源频率/范围/特性总表 |
| **工作时钟规格** | 4.4 | HCLK/PCLK0~4/EXCLK/UCLK/CANCLK 等作用范围 + 频率约束 |
| 晶振电路 | 4.5.1-4.5.3 | XTAL 振荡器/时钟输入模式、XTAL32 初始化流程 |
| **XTAL 故障检测** | 4.5.2 | 故障检测使能、自动切 MRC、中断/复位选择 |
| 内部 RC 时钟 | 4.6.1-4.6.5 | HRC/MRC/LRC/SWDTLRC/RTCLRC 特性与校准 |
| **PLL 时钟** | 4.7 | PLLH/PLLA 配置、M/N/P/Q/R 分频系数 |
| **时钟切换步骤** | 4.8 | 时钟源切换流程图、分频切换流程图 |
| 时钟输出 | 4.9 | MCO_1/MCO_2 输出源选择与分频 |
| FCM 频率测量 | 4.10 | 测量时序、数字滤波、中断/复位 |
| 寄存器-振荡器 | 4.11.1-4.11.15 | XTALCFGR/XTALCR/XTALSTDCR/HRCCR/MRCCR/LRCCR 等 |
| **寄存器-PLL** | 4.11.16-4.11.19 | PLLHCFGR/PLLHCR/PLLACFGR/PLLACR |
| **寄存器-时钟分配** | 4.11.20-4.11.28 | OSCSTBSR/CKSWR/SCFGR/USBCKCFGR/CANCKCFGR/PERICKSEL/MCO |
| 寄存器-FCM | 4.11.29-4.11.37 | FCM_LVR/UVR/CNTR/STR/MCCR/RCCR/RIER/SR/CLR |

## 寄存器速查

> CMU BASE: 0x40054000, FCM BASE: 0x40048400, XTAL32 BASE: 0x4004C400

| 寄存器 | 偏移 | 用途 | 关键位字段 |
|--------|------|------|-----------|
| CMU_XTALCR | 0x032 | XTAL 开关 | XTALSTP[0] |
| CMU_XTALCFGR | (0x4004CC00+0x78) | XTAL 模式/驱动力 | XTALMS[6], XTALDRV[5:4] |
| CMU_XTALSTDCR | 0x040 | XTAL 故障检测 | XTALSTDE[7], XTALSTDRIS[2], XTALSTDRE[1], XTALSTDIE[0] |
| CMU_HRCCR | 0x036 | HRC 开关 | HRCSTP[0] |
| CMU_MRCCR | 0x038 | MRC 开关 | MRCSTP[0] |
| CMU_LRCCR | (0x4004C400+0x01C) | LRC 开关 | LRCSTP[0] |
| **CMU_PLLHCFGR** | 0x100 | **PLLH 配置** | PLLHP[31:28], PLLHQ[27:24], PLLHR[23:20], PLLHN[15:8], PLLSRC[7], PLLHM[1:0] |
| CMU_PLLHCR | 0x02A | PLLH 开关 | PLLHOFF[0] |
| CMU_PLLACFGR | 0x104 | PLLA 配置 | PLLAP[31:28], PLLAQ[27:24], PLLAR[23:20], PLLAN[16:8], PLLAM[4:0] |
| CMU_PLLACR | 0x02E | PLLA 开关 | PLLAOFF[0] |
| CMU_OSCSTBSR | 0x03C | 时钟稳定标志 | PLLASTBF[6], PLLHSTBF[5], XTALSTBF[3], HRCSTBF[0] |
| **CMU_CKSWR** | 0x026 | **系统时钟源选择** | CKSW[2:0]（0=HRC,1=MRC,2=LRC,3=XTAL,4=XTAL32,5=PLLH） |
| **CMU_SCFGR** | 0x020 | **总线分频配置** | HCLKS[26:24], EXCKS[22:20], PCLK4S[18:16], PCLK3S[14:12], PCLK2S[10:8], PCLK1S[6:4], PCLK0S[2:0] |
| CMU_USBCKCFGR | 0x024 | USB 48MHz 时钟选择 | USBCKS[7:4] |
| CMU_CANCKCFGR | 0x018 | CAN 时钟选择 | CAN2CKS[7:4], CAN1CKS[3:0] |

## 典型初始化流程

```c
/* === 切换系统时钟到 PLLH 240MHz（XTAL 8MHz 输入） === */
// 1. 解除写保护
LL_PERIPH_WE(LL_PERIPH_EFM | LL_PERIPH_FCG | LL_PERIPH_GPIO |
             LL_PERIPH_PWC_CLK_RMU | LL_PERIPH_SRAM);

// 2. 设置总线分频（必须在切换前设好，防止超频）
CLK_SetClockDiv(CLK_BUS_CLK_ALL,
    CLK_HCLK_DIV1 | CLK_EXCLK_DIV2 | CLK_PCLK0_DIV1 |
    CLK_PCLK1_DIV2 | CLK_PCLK2_DIV4 | CLK_PCLK3_DIV4 | CLK_PCLK4_DIV2);

// 3. 设置 Flash/SRAM 等待周期（240MHz 需 5 个等待）
EFM_SetWaitCycle(EFM_WAIT_CYCLE5);
SRAM_SetWaitCycle(SRAM_SRAM_ALL, SRAM_WAIT_CYCLE1, SRAM_WAIT_CYCLE1);
SRAM_SetWaitCycle(SRAM_SRAMH, SRAM_WAIT_CYCLE0, SRAM_WAIT_CYCLE0);

// 4. 配置 XTAL 并使能
stc_clock_xtal_init_t stcXtalInit;
(void)CLK_XtalStructInit(&stcXtalInit);
stcXtalInit.u8State = CLK_XTAL_ON;
stcXtalInit.u8Mode  = CLK_XTAL_MD_OSC;
stcXtalInit.u8Drv   = CLK_XTAL_DRV_ULOW;       // 8MHz 用超小驱动力
stcXtalInit.u8StableTime = CLK_XTAL_STB_2MS;
GPIO_AnalogCmd(BSP_XTAL_PORT, BSP_XTAL_PIN, ENABLE);  // XTAL 引脚设模拟
(void)CLK_XtalInit(&stcXtalInit);

// 5. 配置 PLLH: 8MHz / 1 * 120 = 960MHz(VCO), /4 = 240MHz(PLLHP)
stc_clock_pll_init_t stcPLLHInit;
(void)CLK_PLLStructInit(&stcPLLHInit);
stcPLLHInit.PLLCFGR = 0UL;
stcPLLHInit.PLLCFGR_f.PLLM = 1UL - 1UL;   // M=1
stcPLLHInit.PLLCFGR_f.PLLN = 120UL - 1UL;  // N=120
stcPLLHInit.PLLCFGR_f.PLLP = 4UL - 1UL;    // P=4 → 240MHz
stcPLLHInit.PLLCFGR_f.PLLQ = 4UL - 1UL;    // Q=4 → 240MHz
stcPLLHInit.PLLCFGR_f.PLLR = 4UL - 1UL;    // R=4 → 240MHz
stcPLLHInit.u8PLLState = CLK_PLL_ON;
stcPLLHInit.PLLCFGR_f.PLLSRC = CLK_PLL_SRC_XTAL;
(void)CLK_PLLInit(&stcPLLHInit);

// 6. 切换系统时钟到 PLLH
CLK_SetSysClockSrc(CLK_SYSCLK_SRC_PLL);

// 7. 恢复写保护
LL_PERIPH_WP(LL_PERIPH_EFM | LL_PERIPH_GPIO | LL_PERIPH_SRAM);
```

## 常见陷阱与注意事项

1. ⚠️ **切换前必须配好 Flash/SRAM 等待周期**：240MHz 时 EFM 需 5 等待周期，否则 HardFault。先设等待再提频
2. ⚠️ **切换前必须设好总线分频**：PCLK1 最高 120MHz、PCLK2/3 最高 60MHz，分频不当会超频
3. ⚠️ **总线频率约束**：HCLK >= PCLK2/3/4；PCLK0 >= PCLK1/3；HCLK:PCLK0 = N:1 或 1:N；使用 ETH/SDIOC 时 HCLK > PCLK1
4. ⚠️ **PLL 参数只能在停止状态配置**：PLLHCFGR/PLLACFGR 的 M/N/P/Q/R 须在 PLLxOFF=1 时写入
5. ⚠️ **PLLH VCO 范围 600~1200MHz**：PFD 输入 8~25MHz，PLLN 25~150。PLLA VCO 240~480MHz
6. ⚠️ **XTAL 故障检测须在 XTAL 稳定后使能**：确认 XTALSTBF=1 后才设 XTALSTDE=1
7. ⚠️ **XTAL 用作 PLL 源时故障检测只能选复位**：不可选中断（XTALSTDRIS 必须为 1）
8. ⚠️ **不可在时钟源活跃时关闭**：XTAL 用作系统时钟/PLL 源时禁止写 XTALSTP=1，HRC/MRC 同理
9. ⚠️ **LRC 在等待其他时钟稳定时强制振荡**：等待 XTAL/HRC/PLLH/PLLA 稳定期间，LRCSTP 无效
10. ⚠️ **停止模式唤醒后 CKSMRC=1 时时钟被初始化**：PWC_STPMCR.CKSMRC=1 时，唤醒后系统时钟切回 MRC、分频恢复 1 分频

## 官方例程索引

| 例程名 | 绝对路径 | 用途简述 |
|--------|---------|---------|
| clk_switch_sysclk | `$EXAMPLES\clk\clk_switch_sysclk` | 系统时钟源切换：演示 XTAL/PLLH/HRC/MRC/LRC/XTAL32 之间切换，MCO 输出观测 |
| clk_xtalstop_detect | `$EXAMPLES\clk\clk_xtalstop_detect` | XTAL 故障检测：演示中断模式和复位模式两种处理方式 |

> `$EXAMPLES` = `D:\Dev\SDKs\HC32\HC32F4A0\HC32F4A0_DDL_Rev2.4.0\projects\ev_hc32f4a0_lqfp176\examples`

## 相关应用笔记

| 笔记名 | 路径 | 关键内容 |
|--------|------|----------|
| 硬件开发指南 | `$MANUAL\AN_HC32F4A0系列的硬件开发指南` | 晶振选型、负载电容、PCB 布局建议 |
| 冷启动判断方法 | `$MANUAL\AN_HC32F4A0系列冷启动判断方法_Rev1.0` | 复位后时钟源判断逻辑 |

> `$MANUAL` = `D:\Library\10_Datasheets\11_MCU\HC32系列\HC32F4A0`

## 源文件引用

- **手册 Markdown**: `D:\Library\10_Datasheets\11_MCU\HC32系列\HC32F4A0\3-CMU-时钟控制器\kuma_HC32F4A0手册_CMU.md`
- **手册 PDF**: `D:\Library\10_Datasheets\11_MCU\HC32系列\HC32F4A0\RM_HC32F4A0系列参考手册_Rev1.40.pdf`
