# RMU — 复位控制

> ✅ 本知识卡已填充。最后更新：2026-03-25

## 模块概述

HC32F4A0 的复位管理单元 (RMU) 支持 15 种复位源，覆盖上电、外部引脚、电压监测、看门狗、软件、MPU/RAM 错误、时钟异常、Lockup 等场景。每种复位在 RMU_RSTF0 寄存器中有独立标志位，软件可在启动时读取判断上次复位原因。不同复位源对不同模块寄存器的影响范围不同（部分寄存器仅被上电复位重置）。

## 关键特性

- 15 种复位源：POR / NRST 引脚 / BOR / PVD1 / PVD2 / WDT / SWDT / 掉电唤醒 / 软件 / MPU 错误 / RAM 奇偶校验 / RAMECC / 时钟频率异常(FCM) / XTAL 停振 / Cortex-M4 Lockup
- 独立复位标志位（RMU_RSTF0），支持多复位同时发生检测（MULTIRF）
- 标志位需手动清除（写 CLRF=1），且清除后需等待 ≥6 CPU 时钟才能再次读取
- Cortex-M4 Lockup 复位需先使能 RMU_PRSTCR0.LKUPREN
- 不同复位源对各模块寄存器的重置范围不同（见手册表 3-3）：
  - RTC 寄存器仅被模块软件复位 (RTC_CR0.RESET) 重置
  - VBAT 域寄存器仅被 PWC.VBTRSTR 写 0xA5 重置
  - SRAM_CKSR 仅被上电复位和掉电模式 3 唤醒复位重置

## 功能导航大纲

> 小节编号对应原始手册 `kuma_HC32F4A0手册_RMU.md` 中的标题。

| 区域 | 小节 | 关键内容 |
|------|------|----------|
| 简介 | 3.1 | 15 种复位方式列表 |
| **复位方式与标志** | 3.2 | 产生条件表(表 3-1)、标志位交叉表(表 3-2) |
| 上电复位 | 3.3.1 | VCC > Vpor 后经 TRSTPOR 解除复位 |
| NRST 引脚复位 | 3.3.2 | 低电平宽度 ≥ TNRST，经 Tinrst 解除 |
| 欠压复位(BOR) | 3.3.3 | VCC < VBOR 触发，ICG 配置使能 |
| PVD1/PVD2 复位 | 3.3.4 | 可编程电压检测，参考 PWC 章节配置 |
| WDT/SWDT 复位 | 3.3.5 | 下溢或非法刷新触发 |
| 掉电唤醒复位 | 3.3.6 | 唤醒后经 TIPDx 解除，时间取决于掉电模式 |
| 软件复位 | 3.3.7 | 写 AIRCR.SYSRESETREQ |
| MPU/RAM/ECC 复位 | 3.3.8-3.3.10 | 访问错误/奇偶校验/ECC 错误触发 |
| 时钟/XTAL/Lockup | 3.3.11-3.3.13 | FCM 检测/停振检测/M4 Lockup |
| **复位判断方法** | 3.3.14 | 读 RSTF0 → 清 CLRF → 等 6 周期 |
| **各模块复位条件** | 3.3.15 | 表 3-3: 不同寄存器受哪些复位源影响 |

## 寄存器速查

> BASE_ADDR: 0x4004CCF0

| 寄存器 | 偏移 | 位宽 | 用途 | 关键位字段 |
|--------|------|------|------|-----------|
| RMU_PRSTCR0 | 0x08 | 8 | 复位控制 | LKUPREN[7]（Lockup 复位使能） |
| RMU_RSTF0 | 0x0C | 32 | 复位标志（只读+清除） | CLRF[31] MULTIRF[30] LKUPRF[14] XTALERF[13] CKFERF[12] RAECRF[11] RAPERF[10] MPUERF[9] SWRF[8] PDRF[7] SWDRF[6] WDRF[5] PVD2RF[4] PVD1RF[3] BORF[2] PINRF[1] PORF[0] |

## 典型初始化流程

```c
/* === 读取并判断复位原因 === */
// 1. 解除写保护（RMU 属于 PWC_CLK_RMU 保护域）
LL_PERIPH_WE(LL_PERIPH_PWC_CLK_RMU);

// 2. 逐个检查复位标志
if (SET == RMU_GetStatus(RMU_FLAG_PWR_ON)) {
    // 上电复位（冷启动）
}
if (SET == RMU_GetStatus(RMU_FLAG_PIN)) {
    // NRST 引脚复位
}
if (SET == RMU_GetStatus(RMU_FLAG_SW)) {
    // 软件复位（NVIC_SystemReset）
}
if (SET == RMU_GetStatus(RMU_FLAG_WDT)) {
    // 看门狗复位
}
// ... 其他标志: RMU_FLAG_BOR, RMU_FLAG_PVD1, RMU_FLAG_PVD2,
//   RMU_FLAG_SWDT, RMU_FLAG_PDR, RMU_FLAG_MPU_ERR,
//   RMU_FLAG_RAM_PARITY_ERR, RMU_FLAG_RAM_ECC,
//   RMU_FLAG_CLK_ERR, RMU_FLAG_XTAL_ERR, RMU_FLAG_LOCKUP,
//   RMU_FLAG_MUL_ERR (多复位同时发生)

// 3. 清除所有标志（读之后才能清）
RMU_ClearStatus();

// 4. 恢复写保护
LL_PERIPH_WP(LL_PERIPH_PWC_CLK_RMU);

/* === 触发软件复位 === */
NVIC_SystemReset();  // 写 AIRCR.SYSRESETREQ
```

## 常见陷阱与注意事项

1. ⚠️ **写保护**：RMU 寄存器属于 `LL_PERIPH_PWC_CLK_RMU` 保护域，操作前必须 `LL_PERIPH_WE`
2. ⚠️ **清除标志顺序**：必须先读 RMU_RSTF0，然后才能写 CLRF=1 清除。清除后需等待 ≥6 CPU 时钟周期才能再次读取
3. ⚠️ **Lockup 复位默认关闭**：Cortex-M4 Lockup 复位需先设置 RMU_PRSTCR0.LKUPREN=1 才会生效
4. ⚠️ **冷启动判断**：仅 PORF=1 且其他标志均为 0 才表示真正的冷启动上电。PINRF/BORF 等在上电时也可能被清零（见表 3-2 交叉关系）
5. ⚠️ **多重复位**：MULTIRF=1 表示两个或以上复位源同时触发，需逐标志位排查
6. ⚠️ **BOR/PVD 复位需额外配置**：BOR 通过 ICG 使能，PVD1/PVD2 需在 PWC 中配置使能并选择复位模式
7. ⚠️ **部分寄存器不受所有复位源影响**：RTC 内部寄存器仅被 RTC_CR0.RESET 重置；VBAT 域寄存器仅被 PWC.VBTRSTR=0xA5 重置

## 官方例程索引

| 例程名 | 绝对路径 | 用途简述 |
|--------|---------|---------|
| rmu_base | `$EXAMPLES\rmu\rmu_base` | 读取复位标志判断复位原因，按键触发 NVIC_SystemReset 软件复位 |

> `$EXAMPLES` = `D:\Dev\SDKs\HC32\HC32F4A0\HC32F4A0_DDL_Rev2.4.0\projects\ev_hc32f4a0_lqfp176\examples`

## 相关应用笔记

| 笔记名 | 路径 | 关键内容 |
|--------|------|----------|
| 冷启动判断方法 | `$MANUAL\AN_HC32F4A0系列冷启动判断方法_Rev1.0` | 区分冷启动与热复位的方法和技巧 |

> `$MANUAL` = `D:\Library\10_Datasheets\11_MCU\HC32系列\HC32F4A0`

## 源文件引用

- **手册 Markdown**: `D:\Library\10_Datasheets\11_MCU\HC32系列\HC32F4A0\2-RMU-复位控制\kuma_HC32F4A0手册_RMU.md`
- **手册 PDF**: `D:\Library\10_Datasheets\11_MCU\HC32系列\HC32F4A0\RM_HC32F4A0系列参考手册_Rev1.40.pdf`
