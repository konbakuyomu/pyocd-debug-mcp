# RTC — 实时时钟

> ✅ 本知识卡已填充。最后更新：2026-03-25

## 模块概述

RTC 是一个以 BCD 码格式保存日历时间的计数器，记录 00~99 年间的日历信息（秒/分/时/周/日/月/年）。支持 12/24 小时时制，根据月份和闰年自动计算日数。时钟源可选外部低速振荡器 XTAL32（32.768kHz）或内部低速 RTCLRC（32.768kHz）。提供可编程闹钟（分/时/周匹配）、定周期中断（0.5s~1 月）、1Hz 时钟输出（支持误差补偿）、入侵检测（2 路 RTCIC 引脚）、时间戳记录和 128 字节备份寄存器。RTC 位于 VBAT 备份域，上电复位后需通过 RESET 位初始化所有寄存器，之后外部复位不影响 RTC 运行。

## 关键特性

- 时钟源：XTAL32（32.768kHz）或 RTCLRC（32.768kHz）
- BCD 码日历：秒/分/时/周/日/月/年（00~99 年），闰年自动识别
- 12/24 小时时制可选
- 可编程闹钟：分/时/周匹配，触发闹钟中断
- 定周期中断：0.5s/1s/1min/1h/1day/1month 可选
- 1Hz 时钟输出：普通精度、分布式补偿（每 32s）、均匀式补偿（每秒）三种模式
- 时钟误差补偿：±0.96ppm 分辨率，补偿范围 -275.5ppm~+212.9ppm
- 入侵检测：2 路 RTCIC 引脚（TPCR0/TPCR1），支持边沿选择和滤波
- 时间戳：入侵事件发生时自动记录秒/分/时/日/月
- 备份寄存器复位：入侵事件可触发复位 128 字节备份寄存器
- 中断：闹钟中断（RTC_ALM）、定周期中断（RTC_PRD）、入侵检测中断（RTC_TP）
- VBAT 备份域供电，外部复位不影响 RTC

## 功能导航大纲

> 小节编号对应原始手册 `26-RTC-实时时钟.md` 中的标题。

| 区域 | 小节 | 关键内容 |
|------|------|----------|
| 概述 | 27.1-27.2 | 简介、基本框图、基本规格 |
| **上电设定** | 27.3.1 | PWC_VBATRSTR → RTC_CR0.RESET → 配置 → 启动 |
| **计数操作** | 27.3.2-27.3.5 | 计数开始设定（8 步）、低功耗切换、读/写日历寄存器（RWREQ/RWEN 协议） |
| 闹钟 | 27.3.6 | ALME/ALMIE 使能、分/时/周闹钟寄存器设定 |
| **误差补偿** | 27.3.7 | COMP[8:0] 补偿值计算公式、补偿范围 |
| 1Hz 输出 | 27.3.8 | 普通/分布式/均匀式三种精度输出 |
| **入侵检测** | 27.3.9-27.3.10 | TPEN/TPIE/TPRSTE/TSTPE 配置、时间戳记录、备份寄存器复位 |
| **中断** | 27.4 | 闹钟中断、定周期中断、入侵检测中断 |
| 寄存器 | 27.5 | CR0~CR3/SEC~YEAR/ALM*/ERRCR*/TPCR*/TPSR/时间戳寄存器 |

## 寄存器速查

> 基地址: 0x4004C000

| 寄存器 | 偏移 | 宽度 | 用途 | 关键位字段 |
|--------|------|------|------|-----------|
| RTC_CR0 | 0x00 | 8 | 控制 0 | RESET[0] 日历计数器复位 |
| **RTC_CR1** | 0x04 | 8 | 控制 1 | START[7] 计数开始, ONEHZSEL[6] 1Hz 选择, ONEHZOE[5] 1Hz 输出, AMPM[3] 时制, PRDS[2:0] 周期 |
| **RTC_CR2** | 0x08 | 8 | 控制 2 | ALME[7] 闹钟使能, ALMIE[6] 闹钟中断, PRDIE[5] 周期中断, ALMF[3] 闹钟标志, PRDF[2] 周期标志, RWEN[1] 读写允许, RWREQ[0] 读写请求 |
| RTC_CR3 | 0x0C | 8 | 控制 3 | RCKSEL[7] 时钟源选择（0=XTAL32/1=RTCLRC）, LRCEN[4] 内部 LRC 使能 |
| RTC_SEC | 0x10 | 8 | 秒 | BCD 码 0~59 |
| RTC_MIN | 0x14 | 8 | 分 | BCD 码 0~59 |
| RTC_HOUR | 0x18 | 8 | 时 | BCD 码（24H: 0~23; 12H: AM 01~12 / PM 21~32） |
| RTC_WEEK | 0x1C | 8 | 周 | 0~6（周日~周六） |
| RTC_DAY | 0x20 | 8 | 日 | BCD 码 1~31 |
| RTC_MON | 0x24 | 8 | 月 | BCD 码 1~12 |
| RTC_YEAR | 0x28 | 8 | 年 | BCD 码 0~99 |
| RTC_ALMMIN | 0x2C | 8 | 分闹钟 | BCD 码 0~59 |
| RTC_ALMHOUR | 0x30 | 8 | 时闹钟 | BCD 码 |
| RTC_ALMWEEK | 0x34 | 8 | 周闹钟 | bit[6:0] 对应周六~周日 |
| RTC_ERRCRH | 0x38 | 8 | 误差补偿高 | COMPEN[7] 补偿使能, COMP[8] 补偿值高位 |
| RTC_ERRCRL | 0x3C | 8 | 误差补偿低 | COMP[7:0] 补偿值低 8 位 |
| RTC_TPCR0 | 0x40 | 8 | 入侵控制 0 | TPEN0[7], TSTPE0[6], TPIE0[5], TPRSTE0[4], TPNF0[3:2] 滤波, TPCT0[1:0] 边沿 |
| RTC_TPCR1 | 0x44 | 8 | 入侵控制 1 | 同 TPCR0 结构 |
| RTC_TPSR | 0x48 | 8 | 入侵状态 | TPOVF[2] 上溢, TPF1[1] 入侵 1, TPF0[0] 入侵 0 |
| RTC_SECTP~MONTP | 0x4C~0x5C | 8×5 | 时间戳 | 秒/分/时/日/月（只读） |

## 典型初始化流程

```c
/* === RTC 日历初始化 === */
// 1. 解锁 + 复位 VBAT 域
LL_PERIPH_WE(LL_PERIPH_GPIO | LL_PERIPH_FCG | LL_PERIPH_PWC_CLK_RMU);
PWC_VBAT_Reset();

// 2. 初始化时钟源（使用 XTAL32 时需先初始化）
BSP_XTAL32_Init();   // 或使用 LRC 则跳过

// 3. 复位 RTC 寄存器
(void)RTC_DeInit();   // 内部执行 CR0.RESET=0→1 序列

// 4. 停止 RTC + 初始化结构体
RTC_Cmd(DISABLE);
stc_rtc_init_t stcRtcInit;
(void)RTC_StructInit(&stcRtcInit);
stcRtcInit.u8ClockSrc   = RTC_CLK_SRC_XTAL32;  // 或 RTC_CLK_SRC_LRC
stcRtcInit.u8HourFormat = RTC_HOUR_FMT_24H;
stcRtcInit.u8IntPeriod  = RTC_INT_PERIOD_PER_SEC;
(void)RTC_Init(&stcRtcInit);

// 5. 设定日历
stc_rtc_date_t stcDate = {.u8Year=24, .u8Month=3, .u8Day=25, .u8Weekday=RTC_WEEKDAY_TUESDAY};
stc_rtc_time_t stcTime = {.u8Hour=12, .u8Minute=0, .u8Second=0};
(void)RTC_SetDate(RTC_DATA_FMT_DEC, &stcDate);
(void)RTC_SetTime(RTC_DATA_FMT_DEC, &stcTime);

// 6. 使能中断 + 启动
RTC_ClearStatus(RTC_FLAG_CLR_ALL);
RTC_IntCmd(RTC_INT_PERIOD, ENABLE);
// NVIC: INT_SRC_RTC_PRD
RTC_Cmd(ENABLE);
```

## 常见陷阱与注意事项

1. ⚠️ **上电后必须复位 VBAT + RTC**：上电复位后 RTC 寄存器值不定，须先调 `PWC_VBAT_Reset()`，再通过 `RTC_DeInit()` 执行 CR0.RESET=0→1 复位序列
2. ⚠️ **读写日历须走 RWREQ/RWEN 协议**：START=1 后读写日历寄存器必须先设 RWREQ=1 等待 RWEN=1，完成后设 RWREQ=0 等待 RWEN=0；DDL 已封装为 `RTC_EnterRwMode()`/`RTC_ExitRwMode()`
3. ⚠️ **写操作须在 1 秒内完成**：设 RWREQ=1 后，所有日历寄存器写操作须在 1 秒内完成并清 RWREQ
4. ⚠️ **启动后切低功耗须等 2 个计数时钟**：RTC_CR1.START=1 后至少等 2 个 RTC 计数时钟（~61μs@32.768kHz）再进入低功耗模式
5. ⚠️ **入侵标志清除须先关边沿检测**：清除 TPFn 前须先将 TPCTn[1:0]=00（边沿无效），否则可能误动作
6. ⚠️ **VBAT 电压异常后须全部重新初始化**：备份域电压超出规定范围后，XTAL32/RTC/WKTM/备份寄存器全部不定，须重新初始化
7. ⚠️ **备份寄存器可用于断电判断**：例程中利用备份寄存器写入校验值，上电时检查以判断是否需要重新初始化 RTC
8. ⚠️ **运行中修改周期选择须先关中断**：START=1 时写入 PRDS 前应先关闭 PRDIE，写入后清除 PRDF 标志

## 官方例程索引

| 例程名 | 绝对路径 | 用途简述 |
|--------|---------|---------|
| rtc_calendar | `$EXAMPLES\rtc\rtc_calendar` | 日历功能：初始化 + 定周期中断读取日历 + 备份寄存器掉电判断 |
| rtc_alarm | `$EXAMPLES\rtc\rtc_alarm` | 闹钟功能：分/时/周闹钟匹配中断 |
| rtc_calibration_output | `$EXAMPLES\rtc\rtc_calibration_output` | 1Hz 校准输出：误差补偿 + 1Hz 时钟输出 |
| rtc_intrusion_detect | `$EXAMPLES\rtc\rtc_intrusion_detect` | 入侵检测：RTCIC 引脚入侵事件 + 时间戳 + 备份寄存器复位 |
| rtc_low_power | `$EXAMPLES\rtc\rtc_low_power` | 低功耗：RTC 定周期中断唤醒低功耗模式 |

> `$EXAMPLES` = `D:\Dev\SDKs\HC32\HC32F4A0\HC32F4A0_DDL_Rev2.4.0\projects\ev_hc32f4a0_lqfp176\examples`

## 相关应用笔记

| 笔记名 | 路径 | 关键内容 |
|--------|------|----------|
| RTC 补偿功能和实时时钟补偿方法 | `$MANUAL\AN_HC32系列RTC补偿功能和实时时钟补偿方法_Rev1.04\AN_HC32系列RTC补偿功能和实时时钟补偿方法_Rev1.04.md` | RTC 补偿原理、晶体温漂曲线获取和软件补偿方法 |

> `$MANUAL` = `D:\Library\10_Datasheets\11_MCU\HC32系列\HC32F4A0`

## 源文件引用

- **手册 Markdown**: `D:\Library\10_Datasheets\11_MCU\HC32系列\HC32F4A0\26-RTC-实时时钟\26-RTC-实时时钟.md`
- **手册 PDF**: `D:\Library\10_Datasheets\11_MCU\HC32系列\HC32F4A0\RM_HC32F4A0系列参考手册_Rev1.40.pdf`
