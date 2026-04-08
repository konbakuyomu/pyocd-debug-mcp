# SWDT — 看门狗计数器

> ✅ 本知识卡已填充。最后更新：2026-03-25

## 模块概述

HC32F4A0 内置两个看门狗：专用看门狗（SWDT）和通用看门狗（WDT）。SWDT 使用独立内部 RC 时钟 SWDTLRC（10kHz），16 位递减计数，最长溢出时间 3.72 小时。支持窗口刷新功能，可在下溢或窗口外刷新时产生中断或复位。支持硬件启动（ICG0 配置）和软件启动两种模式，可在 Sleep/Stop 模式下继续计数。

## 关键特性

- 时钟源：SWDTLRC（10kHz），分频 /1~/2048
- 16 位递减计数，周期可选 256/4096/16384/65536 cycle
- 最长溢出 3.72 小时（/2048 + 65536 周期）
- 窗口刷新：16 种窗口区间组合，窗口外刷新触发错误
- 启动方式：硬件（ICG0.SWDTAUTS=0）或软件（SWDTAUTS=1）
- 刷新：依次向 SWDT_RR 写 0x0123 + 0x3210
- 异常响应：中断或复位可选
- Sleep/Stop 模式下可继续计数（SLPOFF=0）

## 功能导航大纲

| 区域 | 小节 | 关键内容 |
|------|------|----------|
| 简介 | 28.1 | WDT/SWDT 双看门狗概述 |
| **启动方式** | 28.2.1-28.2.3 | 硬件启动（ICG0）vs 软件启动（写 CR 后刷新） |
| **刷新动作** | 28.2.4 | 先写 0x0123 再写 0x3210，需 4 个计数周期完成 |
| 标志位 | 28.2.5 | UDF/REF 标志，先读 1 再写 0 清零 |
| **中断/复位** | 28.2.6 | ITS 位选择中断或复位 |
| 计数下溢 | 28.2.7 | 递减至零产生下溢事件 |
| **刷新错误** | 28.2.8 | 窗口外刷新→产生刷新错误 |
| 寄存器 | 28.3 | SWDT_CR / SWDT_SR / SWDT_RR |
| 注意事项 | 28.4 | PCLK3 >= 4x SWDT 计数时钟频率 |

## 寄存器速查

> SWDT BASE: 0x40049400 | WDT BASE: 0x40049000

| 寄存器 | 偏移 | 用途 | 关键位字段 |
|--------|------|------|-----------|
| **SWDT_CR** | 0x00 | 控制 | ITS[31] SLPOFF[16] WDPT[11:8] CKS[7:4] PERI[1:0] |
| **SWDT_SR** | 0x04 | 状态 | REF[17] UDF[16] CNT[15:0] |
| **SWDT_RR** | 0x08 | 刷新 | RF[15:0] 依次写 0x0123/0x3210 |

## 典型初始化流程

```c
/* === SWDT 软件启动模式 === */
// 1. 配置（CR 仅可写一次）
stc_swdt_init_t stcSwdtInit;
stcSwdtInit.u32CountPeriod   = SWDT_CNT_PERIOD65536;
stcSwdtInit.u32ClockDiv      = SWDT_CLK_DIV128;
stcSwdtInit.u32RefreshRange  = SWDT_RANGE_0TO100PCT;
stcSwdtInit.u32LPMCount      = SWDT_LPM_CNT_CONTINUE;
stcSwdtInit.u32ExceptionType = SWDT_EXP_TYPE_INT;
(void)SWDT_Init(&stcSwdtInit);

// 2. 注册中断
stc_irq_signin_config_t stcIrq;
stcIrq.enIntSrc    = INT_SRC_SWDT_REFUDF;
stcIrq.pfnCallback = SWDT_IrqCallback;
(void)INTC_IrqSignIn(&stcIrq);
NVIC_EnableIRQ(stcIrq.enIRQn);

// 3. 首次刷新 → 启动计数
SWDT_FeedDog();

// 4. 主循环定期喂狗
while (1) {
    SWDT_FeedDog();  // 必须在允许窗口内
}
```

## 常见陷阱与注意事项

1. ⚠️ **PCLK3 >= 4x SWDT 计数时钟**：否则行为不可预期
2. ⚠️ **CR 仅可写一次**：软件启动模式下 SWDT_CR 配置一次后再写无效
3. ⚠️ **刷新需 4 个计数周期生效**：喂狗时机须提前
4. ⚠️ **标志位清零有延迟**：最多 3 SWDTLRC + 2 PCLK3 周期
5. ⚠️ **SWDTAUTS=0 是自动启动**：ICG0 中逻辑反直觉，0=硬件自动启动
6. ⚠️ **窗口外喂狗即触发异常**：不仅溢出，窗口外刷新也立即触发错误
7. ⚠️ **中断源共用**：下溢和刷新错误共用 INT_SRC_SWDT_REFUDF，需查标志区分

## 官方例程索引

| 例程名 | 绝对路径 | 用途简述 |
|--------|---------|---------|
| swdt_interrupt_sw_startup | `$EXAMPLES\swdt\swdt_interrupt_sw_startup` | 软件启动 + 中断模式 |
| swdt_reset_sw_startup | `$EXAMPLES\swdt\swdt_reset_sw_startup` | 软件启动 + 复位模式 |

> `$EXAMPLES` = `D:\Dev\SDKs\HC32\HC32F4A0\HC32F4A0_DDL_Rev2.4.0\projects\ev_hc32f4a0_lqfp176\examples`

## 相关应用笔记

暂无专属 SWDT 应用笔记。硬件启动配置见 ICG 章节。

## 源文件引用

- **手册 Markdown**: `D:\Library\10_Datasheets\11_MCU\HC32系列\HC32F4A0\27-SWDT-看门狗计数器\kuma_HC32F4A0手册_SWDT.md`
- **手册 PDF**: `D:\Library\10_Datasheets\11_MCU\HC32系列\HC32F4A0\RM_HC32F4A0系列参考手册_Rev1.40.pdf`
