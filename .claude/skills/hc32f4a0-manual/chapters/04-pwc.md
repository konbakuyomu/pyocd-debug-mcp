# PWC — 电源控制

> ✅ 本知识卡已填充。最后更新：2026-03-25

## 模块概述

HC32F4A0 的电源控制器 (PWC) 管理芯片多个电源域（VCC/VDD/AVCC/VBAT/VDDR）的供电、模式切换和电压检测。由功耗控制逻辑 (PWCL)、电源电压检测单元 (PVD)、电池备份控制模块 (BATBKUP) 三部分构成。支持 2 种运行模式（高速 ≤240MHz / 超低速 ≤8MHz）和 3 类低功耗模式（睡眠 / 停止 / 掉电×4 子模式）。掉电模式下 VBAT 域可维持 RTC、WKTM 和 4KB Backup-SRAM 运行。

## 关键特性

- **电源域架构**：VCC 域（IO/LDO/PVD） → VDD 域（CPU/RAM/FLASH/数字外设） → AVCC 域（ADC/DAC/CMP/PGA） → VBAT 域（RTC/WKTM/Backup-SRAM） → VDDR 域（4KB Backup-SRAM，RLDO 供电）
- **运行模式**：高速(DVS=11, DDAS=0xFFF, ≤240MHz) / 超低速(DVS=10, DDAS=0x000, ≤8MHz, 需 LVM=1 + RAMOPM=0x9062)
- **低功耗模式**：
  - 睡眠：CPU 停止，外设继续。任意中断唤醒
  - 停止：CPU+外设+大部分时钟停止。EIRQ/PVD/SWDT/RTC/WKTM/CMP/USART1_RX/Timer0/Timer2 可唤醒
  - 掉电 1~4：VDD 域断电。PD1(PVD 有效) / PD2(POR 有效) / PD3(最低功耗,唤醒近似冷启动) / PD4
- **PVD 电压检测**：PVD1(检测 VCC) / PVD2(检测 VCC 或外部输入)。可配置为复位/中断/NMI/AOS 触发。支持数字滤波
- **唤醒定时器 WKTM**：RTCLRC/XTAL32/64Hz 时钟源，12bit 比较值，可唤醒停止和掉电模式
- **VBAT 电池备份**：VCC 断电自动切换 VBAT 供电。128 字节备份寄存器 + 4KB Backup-SRAM
- **内部电压采样**：通过 ADC 扩展通道测量内部基准电压(~1.15V)和 VBAT(1/2 分压)
- **RAM 分域掉电控制**：SRAM1~SRAMH(11 模块) + CAN/Cache/USB/ETH/SDIOC/NFC RAM 可独立掉电
- **功能时钟门控**：PWC_FCG0~FCG3 控制各外设模块时钟开关
- **寄存器写保护**：PWC_FPRC (FPRCB0/B1/B3) 保护 CMU/PWC/PVD 相关寄存器

## 功能导航大纲

> 小节编号对应原始手册 `4-PWC-电源控制.md`。

| 区域 | 小节 | 关键内容 |
|------|------|----------|
| 简介 | 5.1 | PWCL/PVD/BATBKUP 三部分构成 |
| **电源分布** | 5.2 | VCC/VDD/AVCC/VBAT/VDDR 域划分（图 5-1） |
| 电池备份域 | 5.2.1 | VCC→VBAT 自动切换、Backup-SRAM、RLDO |
| **PVD 电压检测** | 5.3 | POR/PDR/BOR/PVD1/PVD2/基准测量/VBAT 检测 |
| BOR 欠压复位 | 5.3.2 | ICG 配置 BORDIS/BOR_LEV，4 级阈值 |
| PVD1/PVD2 | 5.3.3-5.3.7 | 阈值可编程、复位/中断/NMI/AOS、数字滤波 |
| 内部电压采样 | 5.3.8 | 基准电压测量(ADBUFS=0) + VBAT 检测/测量 |
| 唤醒定时器 WKTM | 5.4 | 12bit 加计数，RTCLRC/XTAL32/64Hz 时钟源 |
| **运行模式** | 5.5.1 | 高速↔超低速切换流程（DVS/DDAS/LVM/RAMOPM） |
| **睡眠模式** | 5.5.2 | STOP=0, PWDN=0 + WFI/WFE |
| **停止模式** | 5.5.3 | STOP=1, PWDN=0 + WFI/WFE，唤醒源列表 |
| **掉电模式** | 5.5.4 | STOP=1, PWDN=1 + WFI，PD1~PD4 子模式 |
| 降低功耗方法 | 5.5.5-5.5.8 | 降频/关时钟源/FCGn 门控/RAM 掉电 |
| 寄存器保护 | 5.6 | FPRCB0(CMU)/B1(PWC/RMU)/B3(PVD) |

## 寄存器速查

> 多个 BASE_ADDR，分组列出

| 寄存器 | BASE+偏移 | 位宽 | 用途 | 关键位字段 |
|--------|-----------|------|------|-----------|
| PWC_PWRC0 | 0x4004CC00+0x00 | 8 | 掉电模式控制 | PWDN[7] IORTN[5:4] PDMDS[1:0] |
| PWC_PWRC1 | +0x04 | 8 | 电源模式控制 | STPDAS[7:6] PDTS[3] VHRCSD[2] VPLLSD[1:0] |
| PWC_PWRC2 | +0x08 | 8 | 运行模式电压 | DVS[5:4] DDAS[11:8] |
| PWC_PWRC3 | +0x0C | 8 | 驱动选择 | DDAS[7:0] |
| PWC_PWRC4 | +0x10 | 8 | 内部电压采样控制 | ADBUFS ADBUFE VBATME VBATREFSEL VBATMON |
| PWC_PVDCR0 | +0x14 | 8 | PVD 使能 | PVD1EN PVD2EN |
| PWC_PVDCR1 | +0x18 | 8 | PVD 中断/复位选择 | PVD1IRS PVD2IRS PVD1CMPOE PVD2CMPOE |
| PWC_PVDFCR | +0x1C | 8 | PVD 滤波 | PVD1NFCKS PVD2NFCKS PVD1NFDIS PVD2NFDIS |
| PWC_PVDLCR | +0x20 | 8 | PVD 阈值电平 | PVD1LVL[2:0] PVD2LVL[2:0] |
| PWC_PDWKE0/1/2 | +0x28/2C/30 | 8 | 掉电唤醒使能 | WKUPn 引脚选择 |
| PWC_PDWKES | +0x34 | 8 | 唤醒边沿选择 | PD_WKUP_TRIG |
| PWC_PDWKF0/1 | +0x38/3C | 8 | 唤醒标志 | 各唤醒源标志位 |
| PWC_RAMPC0 | +0xE0 | 32 | RAM 掉电控制 | RAMPDC[10:0] |
| PWC_RAMOPM | +0xE4 | 16 | RAM 运行模式 | 高速=0x8043, 超低速=0x9062 |
| PWC_PRAMLPC | +0xE8 | 32 | 外设 RAM 低功耗 | PRAMDC[9:0] (CAN/USB/ETH 等) |
| PWC_PVDICR | +0xF0 | 8 | PVD 中断控制 | PVD1ICRE PVD2ICRE |
| PWC_PVDDSR | +0xF4 | 8 | PVD 检测状态 | PVD1DETFLG PVD2DETFLG |
| PWC_STPMCR | 0x40054000+0x0C | 16 | STOP 模式配置 | STOP CKSMRC FLNWT |
| PWC_FPRC | 0x40054000+0x3FE | 8 | 功能保护 | FPRCB0(CMU) FPRCB1(PWC) FPRCB3(PVD) |
| PWC_FCG0~3 | 0x40048000+0x00~0C | 32 | 功能时钟门控 | 各外设模块时钟开关 |
| PWC_VBATRSTR | 0x4004C400+0x30 | 8 | VBAT 域复位 | 写 0xA5 初始化 VBAT 域 |
| PWC_VBATCR | +0x40 | 8 | VBAT 域控制 | VBTRSD（Backup-SRAM 关闭） |
| PWC_WKTC0/1/2 | +0x50/54/58 | 8 | 唤醒定时器 | WKTCMP[11:0] WKTCE |
| PWC_BKR000~127 | +0x200~0x3F8 | 8×128 | 备份寄存器 | VBAT 域保持 |

## 典型初始化流程

```c
/* === 进入 Sleep 模式 === */
LL_PERIPH_WE(LL_PERIPH_PWC_CLK_RMU);
// STOP=0 时执行 WFI 即为 Sleep
PWC_SLEEP_Enter(PWC_SLEEP_WFI);
// 任意中断唤醒后从此处继续执行

/* === 进入 Stop 模式 === */
stc_pwc_stop_mode_config_t stcStopCfg;
PWC_STOP_StructInit(&stcStopCfg);
stcStopCfg.u8StopDrv    = PWC_STOP_DRV_HIGH;
stcStopCfg.u16ExBusHold = PWC_STOP_EXBUS_HIZ;
stcStopCfg.u16Clock     = PWC_STOP_CLK_KEEP;
stcStopCfg.u16FlashWait = PWC_STOP_FLASH_WAIT_ON;
PWC_STOP_Config(&stcStopCfg);
INTC_WakeupSrcCmd(INTC_STOP_WKUP_EXTINT_CH0, ENABLE);  // 选择唤醒源
PWC_STOP_Enter(PWC_STOP_WFI);
// 唤醒后从此处继续执行

/* === 进入 Power-Down 模式 === */
stc_pwc_pd_mode_config_t stcPdCfg;
PWC_PD_StructInit(&stcPdCfg);
stcPdCfg.u8Mode     = PWC_PD_MD1;       // 掉电模式 1
stcPdCfg.u8IOState  = PWC_PD_IO_KEEP1;  // IO 保持状态
stcPdCfg.u8VcapCtrl = PWC_PD_VCAP_0P1UF;
PWC_PD_Config(&stcPdCfg);
PWC_PD_WakeupCmd(PWC_PD_WKUP_WKUP00, ENABLE);  // WKUP0_0 唤醒
PWC_PD_SetWakeupTriggerEdge(PWC_PD_WKUP_TRIG_WKUP0, PWC_PD_WKUP_TRIG_FALLING);
PWC_PD_ClearWakeupStatus(PWC_PD_WKUP_FLAG_ALL);
PWC_PD_Enter();
// 掉电唤醒后 MCU 复位重启

/* === PVD 电压检测中断 === */
LL_PERIPH_WE(LL_PERIPH_LVD);
stc_pwc_lvd_init_t stcLvd;
PWC_LVD_StructInit(&stcLvd);
stcLvd.u32State              = PWC_LVD_ON;
stcLvd.u32CompareOutputState = PWC_LVD_CMP_ON;
stcLvd.u32ExceptionType      = PWC_LVD_EXP_TYPE_INT;
stcLvd.u32ThresholdVoltage   = PWC_LVD_THRESHOLD_LVL6;  // ~2.8V
stcLvd.u32TriggerEdge        = PWC_LVD_TRIG_FALLING;
stcLvd.u32Filter             = PWC_LVD_FILTER_ON;
stcLvd.u32FilterClock        = PWC_LVD_FILTER_LRC_MUL2;
PWC_LVD_Init(PWC_LVD_CH1, &stcLvd);
PWC_LVD_ClearStatus(PWC_LVD1_FLAG_DETECT);
// 注册 LVD1 中断...
```

## 常见陷阱与注意事项

1. ⚠️ **写保护域**：PWC 操作分属 `LL_PERIPH_PWC_CLK_RMU`(FPRCB1) 和 `LL_PERIPH_LVD`(FPRCB3) 两个保护域，配置前须分别解锁
2. ⚠️ **进入 Stop 前必须确认**：FLASH 不在编程/擦除（EFM_FSR.RDY）、DMA 无活动传输、振荡停止检测无效、HCLK:PCLKn 分频比 ≤1:4、EIRQ 数字滤波关闭
3. ⚠️ **掉电模式与 PVD 互斥**：PVD1/PVD2 配置为复位模式时，芯片无法进入掉电模式（会进入停止模式）
4. ⚠️ **SWDT 阻止掉电**：ICG 中 SWDTSLPOFF=0（掉电模式下 SWDT 不停止）时，芯片进入停止而非掉电模式
5. ⚠️ **超低速模式切换**：切换前须先设 FLASH LVM=1 + RAMOPM=0x9062 并确认，切回高速后须恢复为 LVM=0 + RAMOPM=0x8043
6. ⚠️ **VCAP 容量匹配**：VCAP 总容量须与 PWC_PWRC1.PDTS 匹配（0.2μF→PDTS=0, 0.094μF→PDTS=1），否则掉电唤醒行为不确定
7. ⚠️ **掉电唤醒标志须清除**：掉电唤醒后 PWC_PDWKF0/F1 标志不清除则无法再次进入掉电模式
8. ⚠️ **IO 保持释放**：IORTN=01 时掉电唤醒后 IO 仍保持锁定，须软件写 IORTN=00 才释放
9. ⚠️ **PVD 低功耗限制**：停止/掉电模式下使用 PVD 时须关闭数字滤波器；掉电模式下 PVD 仅在 PD1 有效
10. ⚠️ **USB 引脚漏电**：Stop 模式不使用 USB 唤醒时，PA11/PA12/PB14/PB15 应禁止上拉以避免额外电流
11. ⚠️ **VBAT 域初始化**：首次使用电池备份域须写 PWC_VBATRSTR=0xA5；掉电模式 3/4 不能与电池备份功能同时使用
12. ⚠️ **进入 Stop 前确保 PWRC0.PDMS=0b00**

## 官方例程索引

| 例程名 | 绝对路径 | 用途简述 |
|--------|---------|---------|
| pwc_lpc | `$EXAMPLES\pwc\pwc_lpc` | 低功耗综合演示：Sleep/Stop/PD 三种模式循环切换 |
| pwc_lvd | `$EXAMPLES\pwc\pwc_lvd` | PVD1(2.8V)+PVD2(2.3V) 低压检测中断，LED 报警 |
| pwc_pd_wake | `$EXAMPLES\pwc\pwc_pd_wake` | Power-Down 模式 + WKTM 定时唤醒 |
| pwc_sleep_wake | `$EXAMPLES\pwc\pwc_sleep_wake` | Sleep 模式 + 按键 EXTINT 中断唤醒 |
| pwc_stop_wake | `$EXAMPLES\pwc\pwc_stop_wake` | Stop 模式三种进入方式(WFI/WFE_INT/WFE_EVT) + EXTINT 唤醒 |
| pwc_vol_measure | `$EXAMPLES\pwc\pwc_vol_measure` | ADC 扩展通道测量内部基准电压和 VBAT 电压 |

> `$EXAMPLES` = `D:\Dev\SDKs\HC32\HC32F4A0\HC32F4A0_DDL_Rev2.4.0\projects\ev_hc32f4a0_lqfp176\examples`

## 相关应用笔记

| 笔记名 | 路径 | 关键内容 |
|--------|------|----------|
| 掉电模式 IO 保持功能 | `$MANUAL\AN_HC32系列掉电模式IO保持功能的使用_Rev1.00` | 掉电模式下 IO 输出状态保持方法 |
| 冷启动判断方法 | `$MANUAL\AN_HC32F4A0系列冷启动判断方法_Rev1.0` | 区分冷启动与掉电唤醒复位 |
| 硬件设计指南 | `$MANUAL\AN_HC32F4A0系列的硬件开发指南` | VCAP 电容选型、电源走线建议 |

> `$MANUAL` = `D:\Library\10_Datasheets\11_MCU\HC32系列\HC32F4A0`

## 源文件引用

- **手册 Markdown**: `D:\Library\10_Datasheets\11_MCU\HC32系列\HC32F4A0\4-PWC-电源控制\4-PWC-电源控制.md`
- **手册 PDF**: `D:\Library\10_Datasheets\11_MCU\HC32系列\HC32F4A0\RM_HC32F4A0系列参考手册_Rev1.40.pdf`
