# ICG — 初始化配置

> ✅ 本知识卡已填充。最后更新：2026-03-25

## 模块概述

HC32F4A0 的初始化配置 (ICG) 是存储在 FLASH 地址 0x0000_0400~0x0000_045F 的硬件配置区。芯片复位解除后，硬件电路自动将该区域数据加载到 ICG 寄存器，完成 WDT/SWDT/BOR/HRC 等模块的初始参数配置。ICG 寄存器运行时只读，用户通过编程/擦除 FLASH 扇区 0 修改配置。SDK 通过在 `hc32f4xx_conf.h` 中定义 `ICG_REG_CFGn_CONST` 宏，由启动代码写入 FLASH 对应地址。

## 关键特性

- **硬件自动加载**：复位后由硬件从 FLASH 0x400~0x45F 读取, 无需软件初始化
- **ICG0**（WDT + SWDT 配置）：
  - WDT: 自动启动(WDTAUTS) / 中断或复位(WDTITS) / 溢出周期(WDTPERI) / 时钟分频(WDTCKS) / 刷新窗口(WDTWDPT) / Sleep 停止(WDTSLPOFF)
  - SWDT: 自动启动(SWDTAUTS) / 中断或复位(SWDTITS) / 溢出周期(SWDTPERI) / 时钟分频(SWDTCKS) / 刷新窗口(SWDTWDPT) / Sleep+Stop 停止(SWDTSLPOFF)
- **ICG1**（BOR + HRC 配置）：
  - BOR: 使能/禁止(BORDIS) + 4 级阈值选择(BOR_LEV: 2.0V/2.1V/2.2V/2.4V)
  - HRC: 频率选择(HRCFREQSEL: 20MHz/16MHz) + 振荡停止(HRCSTOP)
- **ICG3**（D-Bus 读保护）：DBUSPRT=0x4450 时使能 0x00000000~0x0001FFFF 的 D-Bus 读保护
- 地址 0x420~0x437 为数据安全保护区（详见 EFM 章节）
- 预留区域须写全 1 保证芯片正常动作

## 功能导航大纲

> 小节编号对应原始手册 `5-ICG-初始化配置.md`。

| 区域 | 小节 | 关键内容 |
|------|------|----------|
| 简介 | 6.1 | FLASH 0x400~0x45F 自动加载, 预留区写全 1 |
| 寄存器一览 | 6.1(表 6-1) | ICG0/ICG1/ICG3 三个寄存器 |
| **ICG0 — WDT/SWDT** | 6.2.1 | 看门狗全部参数配置（上半 WDT, 下半 SWDT） |
| **ICG1 — BOR/HRC** | 6.2.2 | BOR 使能+阈值, HRC 频率+停止 |
| ICG3 — D-Bus 保护 | 6.2.3 | DBUSPRT=0x4450 使能读保护 |

## 寄存器速查

> BASE_ADDR: 0x0000_0400 (FLASH 中的硬件配置区, 只读)

| 寄存器 | 偏移 | 位宽 | 用途 | 关键位字段 |
|--------|------|------|------|-----------|
| ICG0 | 0x000 | 32 | WDT+SWDT 配置 | [28]WDTSLPOFF [27:24]WDTWDPT [23:20]WDTCKS [19:18]WDTPERI [17]WDTITS [16]WDTAUTS / [12]SWDTSLPOFF [11:8]SWDTWDPT [7:4]SWDTCKS [3:2]SWDTPERI [1]SWDTITS [0]SWDTAUTS |
| ICG1 | 0x004 | 32 | BOR+HRC 配置 | [18]BORDIS [17:16]BOR_LEV [8]HRCSTOP [0]HRCFREQSEL |
| ICG3 | 0x00C | 32 | D-Bus 读保护 | [15:0]DBUSPRT (=0x4450 启用保护) |

## 典型初始化流程

```c
/* ICG 不需要运行时初始化代码。配置方式：
   在 hc32f4xx_conf.h 中定义宏，由 DDL 启动代码写入 FLASH ICG 区域 */

/* === 例: 使能 WDT 硬件自动启动（复位模式，16384 周期，PCLK3/512，0~25%窗口） === */
// hc32f4xx_conf.h:
#define LL_ICG_ENABLE                  DDL_ON
#define ICG_REG_CFG0_CONST            (0xF19AFFBFUL)
// 等效语义宏：
//   ICG_WDT_RST_START       — 复位后自动启动
//   ICG_WDT_EXP_TYPE_RST    — 溢出产生复位
//   ICG_WDT_CNT_PERIOD16384 — 计数周期 16384
//   ICG_WDT_CLK_DIV512      — PCLK3/512 分频
//   ICG_WDT_RANGE_0TO25PCT  — 0%~25% 刷新窗口
//   ICG_WDT_LPM_CNT_STOP   — 睡眠模式停止计数

/* === 例: 使能 BOR（阈值 Level3 ≈ 2.4V） === */
#define ICG_REG_CFG1_CONST            (0xFFFBFFFFUL)
// BORDIS=0 → BOR 使能, BOR_LEV=11 → 阈值3

/* === 运行时查询 WDT/SWDT 复位 === */
if (SET == RMU_GetStatus(RMU_FLAG_WDT)) {
    // WDT 复位发生
}
RMU_ClearStatus();

/* === 运行时喂狗 === */
WDT_FeedDog();     // 在允许窗口内调用
SWDT_FeedDog();
```

## 常见陷阱与注意事项

1. ⚠️ **ICG 是只读的**：ICG0/ICG1/ICG3 在运行时只读，修改须通过擦写 FLASH 扇区 0（EFM 操作）
2. ⚠️ **预留区写全 1**：0x408~0x40B, 0x410~0x41F, 0x438~0x45F 为预留区, 必须写全 1 否则可能导致芯片异常
3. ⚠️ **FLASH 引导交换影响 ICG 位置**：启用 FLASH 引导交换(Boot Swap)且 OTP 不使能时, ICG 区位于 FLASH 块 1 扇区 0 而非块 0 扇区 0
4. ⚠️ **WDTAUTS=0 表示自动启动**：注意 ICG 位逻辑! 0=自动启动(硬件启动), 1=停止状态(需软件启动)。BORDIS 同理, 0=使能 BOR
5. ⚠️ **WDT 刷新窗口**：WDT/SWDT 在允许窗口外喂狗会触发复位（而非仅溢出时复位）
6. ⚠️ **SWDT 影响掉电模式**：SWDTSLPOFF=0（Stop 下不停止计数）会阻止芯片进入掉电模式（退化为停止模式）
7. ⚠️ **HRC 频率二选一**：HRCFREQSEL=0 为 20MHz, =1 为 16MHz, 影响使用 HRC 作为 PLL 源时的频率计算

## 官方例程索引

| 例程名 | 绝对路径 | 用途简述 |
|--------|---------|---------|
| icg_bor_reset_hw_startup | `$EXAMPLES\icg\icg_bor_reset_hw_startup` | ICG 硬件配置 BOR 使能+阈值，上电后查 RMU_FLAG_BROWN_OUT |
| icg_hrc_osc_hw_startup | `$EXAMPLES\icg\icg_hrc_osc_hw_startup` | ICG 硬件配置 HRC 频率选择（20MHz/16MHz） |
| icg_swdt_interrupt_hw_startup | `$EXAMPLES\icg\icg_swdt_interrupt_hw_startup` | SWDT 自动启动+中断模式，验证 Sleep/Stop 下 SWDT 唤醒能力 |
| icg_swdt_reset_hw_startup | `$EXAMPLES\icg\icg_swdt_reset_hw_startup` | SWDT 自动启动+复位模式，超窗喂狗触发复位 |
| icg_wdt_interrupt_hw_startup | `$EXAMPLES\icg\icg_wdt_interrupt_hw_startup` | WDT 自动启动+中断模式，下溢中断中翻转 LED |
| icg_wdt_reset_hw_startup | `$EXAMPLES\icg\icg_wdt_reset_hw_startup` | WDT 自动启动+复位模式，允许窗口内喂狗+按键触发超窗复位 |

> `$EXAMPLES` = `D:\Dev\SDKs\HC32\HC32F4A0\HC32F4A0_DDL_Rev2.4.0\projects\ev_hc32f4a0_lqfp176\examples`

## 相关应用笔记

| 笔记名 | 路径 | 关键内容 |
|--------|------|----------|
| （无专属 AN） | — | WDT/SWDT 配置细节可参考 PWC/RMU 章节 |

> `$MANUAL` = `D:\Library\10_Datasheets\11_MCU\HC32系列\HC32F4A0`

## 源文件引用

- **手册 Markdown**: `D:\Library\10_Datasheets\11_MCU\HC32系列\HC32F4A0\5-ICG-初始化配置\5-ICG-初始化配置.md`
- **手册 PDF**: `D:\Library\10_Datasheets\11_MCU\HC32系列\HC32F4A0\RM_HC32F4A0系列参考手册_Rev1.40.pdf`
