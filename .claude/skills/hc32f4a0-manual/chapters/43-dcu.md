# DCU — 数据计算单元

> ✅ 本知识卡已填充。最后更新：2026-03-26

## 模块概述

DCU（Data Computing Unit）是不借助 CPU 的简单数据处理模块。每个 DCU 单元具有 3 个数据寄存器，可进行加法、减法、比较大小和窗口比较。支持硬件事件触发运算，DCU1~4 还可配合定时器+DAC 输出三角波和锯齿波。HC32F4A0 搭载 8 个独立 DCU 单元（DCU1~DCU8）。

## 关键特性

- **8 个独立 DCU 单元**（DCU1~DCU8），每个具有 DATA0/DATA1/DATA2 三个数据寄存器
- **数据宽度**：8/16/32 位可配置
- **运算模式**：加法、减法、触发加、触发减、比较、三角波、递增锯齿波、递减锯齿波
- **加法/减法**：DATA0±DATA1 → DATA0，同时自动计算半值 → DATA2
- **比较模式**：DATA0 vs DATA1 + DATA0 vs DATA2，支持窗口比较
- **硬件触发**：可由其他外设事件触发运算（通过 DCU_TRGSEL 选择触发源）
- **波形输出**（仅 DCU1~4）：三角波/锯齿波，DATA1 设振幅上下限，DATA2 设步长
- **事件/中断输出**：溢出/借位/比较结果可产生中断和事件信号，可触发其他外设
- **FCG0 触发使能**：使用硬件触发前须使能 FCG0 的外围触发功能

## 功能导航大纲

> 小节编号对应原始手册标题

| 区域 | 小节 | 关键内容 |
|------|------|----------|
| 概要 | 44.1 | 功能总览，8 个独立单元 |
| 加法模式 | 44.2.1 | DATA0+DATA1→DATA0，(DATA0+DATA1)/2→DATA2 |
| 减法模式 | 44.2.2 | DATA0-DATA1→DATA0，(DATA0-DATA1)/2→DATA2 |
| 硬件触发 | 44.2.3 | 触发加/触发减模式，DCU_TRGSEL 选择事件源 |
| 比较模式 | 44.2.4 | DATA0 vs DATA1/DATA2，窗口比较 |
| 中断/事件 | 44.2.5 | DCU_INTEVT 控制，每单元 1 个中断 + 1 个事件 |
| 三角波 | 44.2.6 | MODE=1000b，DATA1 振幅上下限，DATA2 步长 |
| 递增锯齿波 | 44.2.7 | MODE=1001b |
| 递减锯齿波 | 44.2.8 | MODE=1010b |
| 寄存器 | 44.3 | 每单元 7 个寄存器 |

## 寄存器速查

> DCU1: 0x40056000 | DCU2: 0x40056400 | ... | DCU8: 0x40057C00（间距 0x400）

| 寄存器 | 偏移 | 用途 |
|--------|------|------|
| DCU_CTL | 0x00 | 控制（MODE[3:0]/DATASIZE[1:0]/INTEN） |
| DCU_FLAG | 0x04 | 标志（溢出/借位/比较结果） |
| DCU_DATA0 | 0x08 | 数据寄存器 0（被加数/被减数/比较数/波形输出值） |
| DCU_DATA1 | 0x0C | 数据寄存器 1（加数/减数/比较参考/振幅上下限） |
| DCU_DATA2 | 0x10 | 数据寄存器 2（半值结果/比较参考 2/步长） |
| DCU_FLAGCLR | 0x14 | 标志清除 |
| DCU_INTEVT | 0x18 | 中断和事件条件选择 |

## 典型初始化流程

```c
/* 以 DCU1 加法模式为例 */

/* 1. 使能时钟 */
FCG_Fcg0PeriphClockCmd(FCG0_PERIPH_DCU1, ENABLE);

/* 2. DCU 初始化 */
stc_dcu_init_t stcDcuInit;
DCU_StructInit(&stcDcuInit);
stcDcuInit.u32Mode     = DCU_MD_ADD;        /* 加法模式 */
stcDcuInit.u32DataSize = DCU_DATA_SIZE_16BIT; /* 16 位数据宽度 */
DCU_Init(CM_DCU1, &stcDcuInit);

/* 3. 写入初始数据 */
DCU_WriteData0(CM_DCU1, 0xFF00U);

/* 4. 写 DATA1 触发加法运算 */
DCU_WriteData1(CM_DCU1, 0x55U);
/* DATA0 = 0xFF55, DATA2 = (DATA0+DATA1)/2 */
```

## 常见陷阱与注意事项

1. **写 DATA1 触发运算**：加法/减法模式下，写 DATA1 即触发一次运算
2. **硬件触发须使能 FCG0**：使用触发模式前必须在 FCG0 中使能外围触发功能
3. **波形模式仅 DCU1~4**：三角波和锯齿波输出模式只有 DCU1~DCU4 支持
4. **波形模式数据寄存器含义改变**：进入波形模式后 DATA0/1/2 变为输出值/振幅/步长
5. **波形中断启用顺序**：须先关 INTEN → 设 DATA0~2 → 清标志 → 开 INTEN → 启动定时器
6. **比较模式触发条件**：可选写 DATA0 后比较或写任何数据寄存器后比较
7. **溢出/借位标志须手动清除**：通过写 DCU_FLAGCLR 清除

## 官方例程索引

| 例程名 | 绝对路径 | 用途简述 |
|--------|---------|--------:|
| dcu_add | `$EXAMPLES\dcu\dcu_add` | 加法模式 |
| dcu_sub | `$EXAMPLES\dcu\dcu_sub` | 减法模式 |
| dcu_compare | `$EXAMPLES\dcu\dcu_compare` | 比较模式 |
| dcu_hw_trigger_add | `$EXAMPLES\dcu\dcu_hw_trigger_add` | 硬件触发加法 |
| dcu_hw_trigger_sub | `$EXAMPLES\dcu\dcu_hw_trigger_sub` | 硬件触发减法 |
| dcu_triangle_wave_mode | `$EXAMPLES\dcu\dcu_triangle_wave_mode` | 三角波输出 |
| dcu_sawtooth_wave_mode | `$EXAMPLES\dcu\dcu_sawtooth_wave_mode` | 锯齿波输出 |

> `$EXAMPLES` = `D:\Dev\SDKs\HC32\HC32F4A0\HC32F4A0_DDL_Rev2.4.0\projects\ev_hc32f4a0_lqfp176\examples`

## 相关应用笔记

暂无专属 DCU 应用笔记。

## 源文件引用

- **手册 Markdown**: `D:\Library\10_Datasheets\11_MCU\HC32系列\HC32F4A0\43-DCU-数据计算单元\43-DCU-数据计算单元.md`
- **手册 PDF**: `D:\Library\10_Datasheets\11_MCU\HC32系列\HC32F4A0\RM_HC32F4A0系列参考手册_Rev1.40.pdf`
