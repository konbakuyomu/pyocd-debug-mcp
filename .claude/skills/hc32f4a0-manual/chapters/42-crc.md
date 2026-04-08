# CRC — CRC 运算单元

> ✅ 本知识卡已填充。最后更新：2026-03-25

## 模块概述

CRC（Cyclic Redundancy Check）运算单元用于对数据进行硬件 CRC 校验。支持 CRC-16（X25 多项式）和 CRC-32（IEEE 802.3 多项式）两种算法，支持 8/16/32 位数据写入，内置初始化寄存器和结果寄存器，可用于数据完整性检测。

## 关键特性

- **CRC-16**：多项式 X^16+X^12+X^5+1（即 0x1021），初始值 0xFFFF，结果与 X25 算法一致
- **CRC-32**：多项式 0x04C11DB7，初始值 0xFFFFFFFF
- **数据宽度**：支持 8 位、16 位、32 位三种写入宽度
- **累加计算**：连续写入数据自动累加 CRC 结果，无需软件干预
- **初始化**：通过 CR 寄存器的 CR 位清除当前结果，恢复初始值
- **结果可读**：CRC_RESLT 寄存器直接读取当前运算结果
- **数据端口**：CRC_DAT（0x80~0xFF 地址段）支持不同宽度写入

## 功能导航大纲

> 小节编号对应原始手册标题

| 区域 | 小节 | 关键内容 |
|------|------|----------|
| 简介 | 43.1 | CRC 模块功能总览 |
| 系统框图 | 43.2 | CRC 运算核心结构 |
| CRC16 运算 | 43.3.1 | X25 多项式 0x1021，初始值 0xFFFF |
| CRC32 运算 | 43.3.2 | IEEE 802.3 多项式 0x04C11DB7，初始值 0xFFFFFFFF |
| 寄存器 | 43.4 | 3 个寄存器详述 |

## 寄存器速查

> 基址: 0x40008C00

| 寄存器 | 偏移 | 用途 | 关键位字段 |
|--------|------|------|-----------:|
| CRC_CR | 0x00 | 控制寄存器 | CR（初始化标志位，写 1 复位 CRC 结果）, FLAG（校验结果标志位） |
| CRC_RESLT | 0x04 | 结果寄存器 | CRC16 时低 16 位有效，CRC32 时全 32 位有效 |
| CRC_DAT | 0x80~0xFF | 数据寄存器 | 支持 8/16/32 位写入（地址段映射） |

## 典型初始化流程

```c
/* 以 CRC-32 硬件编码为例 */

/* 1. 使能时钟 */
FCG_Fcg0PeriphClockCmd(FCG0_PERIPH_CRC, ENABLE);

/* 2. 初始化 CRC（复位结果寄存器） */
CRC_CRC32Init();  /* 或 CRC_CRC16Init() */

/* 3. 写入数据进行累加运算 */
uint32_t au32Data[] = {0x12345678UL, 0x9ABCDEF0UL};
uint32_t u32Crc = CRC_CRC32Calculate(au32Data, ARRAY_SZ(au32Data));

/* 4. 校验（硬件比对） */
en_flag_status_t enFlag = CRC_CRC32Check(au32Data, ARRAY_SZ(au32Data), u32Crc);
/* enFlag == SET 表示校验通过 */
```

## 常见陷阱与注意事项

1. **数据写入宽度影响结果**：同一组数据以 8/16/32 位宽度写入 CRC_DAT 的运算结果不同，需保持编码和校验时宽度一致
2. **累加特性**：不调用初始化则后续写入会在上次结果基础上继续累加，可用于分段计算
3. **FLAG 位含义**：CRC_CR.FLAG 只在校验模式下才有意义（将 CRC 值追加到数据尾部后重新计算，结果为固定值时 FLAG 置位）
4. **CRC16 读取**：CRC_RESLT 为 32 位寄存器，CRC16 结果只占低 16 位
5. **字节序**：硬件按写入顺序（MSB first）处理，与某些软件库（LSB first）可能不一致

## 官方例程索引

| 例程名 | 绝对路径 | 用途简述 |
|--------|---------|--------:|
| crc_hw_accumulate_check | `$EXAMPLES\crc\crc_hw_accumulate_check` | 硬件累加校验演示 |
| crc_hw_encode_hw_check | `$EXAMPLES\crc\crc_hw_encode_hw_check` | 硬件编码 + 硬件校验 |
| crc_hw_encode_sw_check | `$EXAMPLES\crc\crc_hw_encode_sw_check` | 硬件编码 + 软件校验 |

> `$EXAMPLES` = `D:\Dev\SDKs\HC32\HC32F4A0\HC32F4A0_DDL_Rev2.4.0\projects\ev_hc32f4a0_lqfp176\examples`

## 相关应用笔记

暂无专属 CRC 应用笔记。

## 源文件引用

- **手册 Markdown**: `D:\Library\10_Datasheets\11_MCU\HC32系列\HC32F4A0\42-CRC-CRC运算\42-CRC-CRC运算.md`
- **手册 PDF**: `D:\Library\10_Datasheets\11_MCU\HC32系列\HC32F4A0\RM_HC32F4A0系列参考手册_Rev1.40.pdf`
