# OTS — 温度传感器

> ✅ 本知识卡已填充。最后更新：2026-03-25

## 模块概述

OTS（On-chip Temperature Sensor）是 HC32F4A0 的片上温度传感器，用于测量芯片内部温度以支持系统可靠性监控。OTS 输出一组与温度相关的数字量，通过两点定标公式计算温度值；不使用时可关闭以降低功耗。

## 关键特性

- 片上集成，无需外部温度传感器元件
- 测温完成后 OTSST 位自动清零，支持轮询和中断两种完成检测方式
- 动作时钟可选 XTAL（外部高速）或 HRC（内部高速），通过 OTSCK 位切换
- 内置 HRC 频率误差补偿寄存器 OTS_ECR，消除 HRC 频率偏差对精度的影响
- 芯片出厂预置三组温度标定数据（-40°C / 25°C / 125°C），存于 OTS_PDR1~3
- 预置数据基于 8MHz 测得，使用其他频率需按 `D = TSPD × f_OTSCK / 8` 换算
- 支持外设事件触发启动测温（EVT 触发源 → OTS）
- TSSTP 位控制测温结束后是否自动关闭模拟传感器

## 功能导航大纲

> 小节编号对应原始手册标题

| 区域 | 小节 | 关键内容 |
|------|------|----------|
| 简介 | 19.1 | 模块功能概述、框图 |
| 使用流程 | 19.2 | 测温步骤、计算公式、时钟选择 |
| 温度公式 | 19.2 | T = K × (1.7/D1 - 1/D2) × Ehrc + M |
| 定标实验 | 19.2 | 两点定标法求 K 和 M |
| 预置数据 | 19.2 表19-1 | 三组出厂标定数据（-40/25/125°C） |
| Ehrc 使用 | 19.2 表19-2 | HRC/XTAL 下 Ehrc 取值规则 |
| TSSTP 控制 | 19.2 | 模拟传感器关闭策略对启动延迟的影响 |
| 事件触发 | 19.2 | EVT 触发测温 & 测温完成触发其他外设 |
| 控制寄存器 | 19.3.1 | OTS_CTL：启动/时钟/中断/传感器关闭 |
| 数据寄存器 | 19.3.2~3 | OTS_DR1、OTS_DR2：温度原始数据 |
| 误差补偿 | 19.3.4 | OTS_ECR：HRC 误差补偿系数 |
| 预置寄存器 | 19.3.5 | OTS_PDR1~3：出厂标定数据 |

## 寄存器速查

> BASE_ADDR: 0x4004A800（OTS 主寄存器组）

| 寄存器 | 偏移 | 用途 | 关键位字段 |
|--------|------|------|-----------|
| OTS_CTL | 0x00 | 控制寄存器 | OTSST[0](启动) OTSCK[1](时钟选择) OTSIE[2](中断) TSSTP[3](传感器关闭) |
| OTS_DR1 | 0x02 | 温度数据 1 | TSDC[15:0] — D1 |
| OTS_DR2 | 0x04 | 温度数据 2 | TSDC[15:0] — D2 |
| OTS_ECR | 0x06 | 误差补偿 | TSEC[15:0] — Ehrc |

> 出厂预置数据（BASE: 0x40010600，只读）

| 寄存器 | 偏移 | 用途 | 关键位字段 |
|--------|------|------|-----------|
| OTS_PDR1 | 0xE0 | 25°C 预置数据 | D1[15:0], D2[31:16] |
| OTS_PDR2 | 0xF4 | 125°C 预置数据 | D1[15:0], D2[31:16] |
| OTS_PDR3 | 0xF8 | -40°C 预置数据 | D1[15:0], D2[31:16] |

## 温度计算公式

```
T = K × (1.7 / D1 - 1 / D2) × Ehrc + M
```

- **D1** = OTS_DR1[15:0]，**D2** = OTS_DR2[15:0]，**Ehrc** = OTS_ECR[15:0]
- **K**（斜率）、**M**（偏移）通过两点定标实验确定
- 使用 XTAL 时钟时 Ehrc 固定为 1；使用 HRC 时钟时从 OTS_ECR 读取

## 典型初始化流程

```c
/* 1. 使能 OTS 时钟 */
FCG_Fcg3PeriphClockCmd(FCG3_PERIPH_OTS, ENABLE);

/* 2. 启动所需时钟源：LRC 必须开启 */
CLK_LrcCmd(ENABLE);
CLK_HrcCmd(ENABLE);       /* 使用 HRC 动作时 */
CLK_Xtal32Cmd(ENABLE);    /* HRC 模式下 Ehrc 补偿需要 */

/* 3. 配置 OTS */
stc_ots_init_t stcOtsInit;
stcOtsInit.u16ClockSrc  = OTS_CLK_SEL_HRC;
stcOtsInit.u16AutoOffEn = OTS_AUTO_OFF_DISABLE;
OTS_Init(&stcOtsInit);

/* 4. 执行测温（阻塞方式） */
float32_t f32Temp;
OTS_Polling(&f32Temp, 100u);  /* 超时 100 ms */

/* 5. 不再使用时关闭 */
OTS_DeInit();
FCG_Fcg3PeriphClockCmd(FCG3_PERIPH_OTS, DISABLE);
```

## 常见陷阱与注意事项

1. ⚠️ **LRC 必须开启**：OTS 内部依赖 LRC 时钟，即使选择 XTAL/HRC 作为动作时钟，LRC 也必须事先启动
2. ⚠️ **读取数据前确认 OTSST=0**：测温未完成时读取 DR1/DR2/ECR 数据无效
3. ⚠️ **预置数据频率换算**：OTS_PDR1~3 基于 8MHz 测得，实际使用需乘以 `f_OTSCK / 8` 换算
4. ⚠️ **HRC 模式需启动 XTAL32**：Ehrc 补偿依赖 XTAL32，不启动则无法消除 HRC 频率误差
5. ⚠️ **TSSTP 影响连续测温速度**：TSSTP=1 每次测温后关闭传感器，下次需等待稳定时间；高频测温建议 TSSTP=0
6. ⚠️ **定标精度决定测量精度**：两点定标温度点间距越大、环境温度控制越精确，最终精度越高

## 官方例程索引

| 例程名 | 绝对路径 | 用途简述 |
|--------|---------|---------|
| ots_base | `$EXAMPLES\ots\ots_base` | OTS 基础测温（轮询方式） |

> `$EXAMPLES` = `D:\Dev\SDKs\HC32\HC32F4A0\HC32F4A0_DDL_Rev2.4.0\projects\ev_hc32f4a0_lqfp176\examples`

## 相关应用笔记

暂无专属 OTS 应用笔记。

## 源文件引用

- **手册 Markdown**: `D:\Library\10_Datasheets\11_MCU\HC32系列\HC32F4A0\18-OTS-温度传感器\18-OTS-温度传感器.md`
- **手册 PDF**: `D:\Library\10_Datasheets\11_MCU\HC32系列\HC32F4A0\RM_HC32F4A0系列参考手册_Rev1.40.pdf`
