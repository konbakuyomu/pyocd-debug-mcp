# CTC — 内部时钟校准器

> ✅ 本知识卡已填充。最后更新：2026-03-25

## 模块概述

CTC（Clock Trimming Controller）用于自动校准内部高速振荡器（HRC）的频率。由于温度和电压等环境因素导致 HRC 产生频偏，CTC 通过外部高精度参考时钟，以硬件闭环方式自动调节 HRC 的 TRMVAL 校准值，使 HRC 输出达到目标精度。整个校准过程无需 CPU 介入。

## 关键特性

- 三种外部参考时钟源：XTAL（~24 MHz）、XTAL32（32.768 kHz）、CTCREF（外部基准引脚）
- 16 位校准计数器，具备重载功能，计数时钟由 HRC 驱动
- 8 位校准偏差值（OFSVAL）定义可接受频率窗口
- 6 位有符号校准值（TRMVAL），范围 -32 ~ +31，硬件自动递增/递减
- 参考时钟可选 8/32/128/256/512/1024/2048/4096 分频
- 校准上溢（TRMOVF）或下溢（TRMUDF）时自动停止并可触发错误中断
- 校准成功标志 TRIMOK 可供软件轮询

## 功能导航大纲

| 区域 | 小节 | 关键内容 |
|------|------|----------|
| 参考时钟 | 14.3.1 | XTAL/XTAL32/CTCREF 三选一；分频选择与误差估算公式 |
| 频率校准 | 14.3.2 | 计数器从 RLDVAL 向下计数；窗口判定逻辑 |
| 编程指南 | 14.3.3 | XTAL32/8 分频校准 HRC 到 20MHz ±0.5% 的完整步骤 |
| 寄存器 | 14.4 | CTC_CR1 / CTC_CR2 / CTC_STR |

## 寄存器速查

> BASE_ADDR: 0x40049C00

| 寄存器 | 偏移 | 用途 | 关键位字段 |
|--------|------|------|------------|
| CTC_CR1 | 0x00 | 控制寄存器 1 | TRMVAL[5:0](b21-16), CTCEN(b7), ERRIE(b6), REFCKS[1:0](b5-4), REFPSC[2:0](b2-0) |
| CTC_CR2 | 0x04 | 控制寄存器 2 | RLDVAL[15:0](b31-16), OFSVAL[7:0](b7-0) |
| CTC_STR | 0x08 | 状态寄存器 | CTCBSY(b3), TRMUDF(b2), TRMOVF(b1), TRIMOK(b0) |

## 典型初始化流程

```c
/* === 以 XTAL32(32.768kHz)/8 为参考，校准 HRC 到 20MHz ±0.5% === */
/* 1. 确保 CTC 停止 + XTAL32 已起振 */
/* 2. 计算参数 */
// Fref_div = 32768 / 8 = 4096 Hz
// OFSVAL  = (20000000 / 4096) * 0.005 ≈ 24
// RLDVAL  = (20000000 / 4096) + 24   ≈ 4907

/* 3. 初始化 CTC */
stc_ctc_init_t stcCtcInit;
stcCtcInit.u32RefClockFreq  = 32768U;
stcCtcInit.u32RefClockDiv   = CTC_REF_CLK_DIV8;
stcCtcInit.u32RefClockSrc   = CTC_REF_CLK_XTAL32;
stcCtcInit.f32TolerantErr   = 0.005F;  /* ±0.5% */
stcCtcInit.u32HrcFreq       = 20000000U;
(void)CTC_Init(&stcCtcInit);

/* 4. 使能错误中断（可选） */
CTC_IntCmd(ENABLE);

/* 5. 启动校准 */
CTC_Cmd(ENABLE);

/* 6. 等待校准完成 */
while (CTC_GetStatus(CTC_FLAG_TRIM_OK) != SET) {
    if (CTC_GetStatus(CTC_FLAG_TRIM_OVF | CTC_FLAG_TRIM_UDF) != RESET) {
        break;  /* 校准失败 */
    }
}
CTC_Cmd(DISABLE);
```

## 常见陷阱与注意事项

1. ⚠️ **校准期间禁止改寄存器**：CTCEN=1 后 REFCKS/REFPSC/RLDVAL/OFSVAL 均为只读，需先清 CTCEN 并等待 CTCBSY=0
2. ⚠️ **TRMVAL 有符号编码**：最高位为符号位，0x00 是中间值。正方向最大 0x1F(+31)，负方向最小 0x20(-32)
3. ⚠️ **上/下溢自动停止**：TRMVAL 到达边界仍未校准成功时 CTCEN 自动清零
4. ⚠️ **分频选择影响精度**：分频越大测量误差越小但校准时间更长。32.768kHz 参考源仅 8/32 分频可用
5. ⚠️ **参考时钟需先就绪**：使用 XTAL32 前需确保已起振稳定
6. ⚠️ **误差必须小于校准精度**：选择分频前用公式 `误差 = 1 / ((Fhrc / Fref) * PSC)` 验证

## 官方例程索引

| 例程名 | 绝对路径 | 用途简述 |
|--------|----------|----------|
| ctc_xtal32_trimming | `$EXAMPLES\ctc\ctc_xtal32_trimming` | XTAL32 为参考校准 HRC |
| ctc_xtal_trimming | `$EXAMPLES\ctc\ctc_xtal_trimming` | XTAL 为参考校准 HRC |
| ctc_ctcref_trimming | `$EXAMPLES\ctc\ctc_ctcref_trimming` | 外部 CTCREF 引脚为参考校准 HRC |

> `$EXAMPLES` = `D:\Dev\SDKs\HC32\HC32F4A0\HC32F4A0_DDL_Rev2.4.0\projects\ev_hc32f4a0_lqfp176\examples`

## 相关应用笔记

暂无 CTC 专题应用笔记。

## 源文件引用

- **手册 Markdown**: `D:\Library\10_Datasheets\11_MCU\HC32系列\HC32F4A0\13-CTC-内部时钟校准器\13-CTC-内部时钟校准器.md`
- **手册 PDF**: `D:\Library\10_Datasheets\11_MCU\HC32系列\HC32F4A0\RM_HC32F4A0系列参考手册_Rev1.40.pdf`
