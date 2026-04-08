# MPU — 存储保护单元

> ✅ 本知识卡已填充。最后更新：2026-03-25

## 模块概述

HC32F4A0 内置 7 个 MPU 单元，可对存储器进行访问保护。包括：ARM MPU（CPU，8 区域）、SMPU1/SMPU2（系统 DMA1/DMA2，各 16 区域）、FMPU（USBFS-DMA，8 区域）、HMPU（USBHS-DMA，8 区域）、EMPU（ETH-DMA，8 区域）、IPMPU（IP 访问保护）。对被禁止空间的访问可触发无视/总线错误/NMI/复位四种动作。

## 关键特性

- 6 个针对 DMA 主机的 MPU + 1 个 IP 访问保护单元
- SMPU1/SMPU2 各 16 区域（8 专用 + 8 共用），其余各 8 区域
- 区域大小 32Byte~4GByte（2^n，n=5~32），基地址低 n 位须为 0
- 每区域独立设置读/写权限，背景区域也可独立设权限
- 区域重叠时**禁止优先**
- 违例动作可选：无视 / 总线错误 / NMI / 复位
- IPMPU 控制非特权模式下对系统 IP 和安全 IP 的访问
- 寄存器受写保护（MPU_WP 写 0x96A5 解锁，0x96A4 加锁）

## 功能导航大纲

> 小节编号对应原始手册 `11-MPU-存储保护单元.md`

| 区域 | 小节 | 关键内容 |
|------|------|----------|
| 简介 | 12.1 | 7 个 MPU 单元总览表 |
| 区域范围设置 | 12.2.1 | 基地址 + 大小（2^n），背景区域概念 |
| 权限设置 | 12.2.2 | 每区域独立读/写权限，重叠时禁止优先 |
| **动作选择** | 12.2.3 | 无视/总线错误/NMI/复位 |
| 启动 MPU | 12.2.4 | 建议先配区域再使能 |
| 应用举例 | 12.3 | 只允许部分空间 / 只禁止部分空间 |
| 寄存器-区域描述 | 12.4.1 | MPU_RGD0~15：基地址 + SIZE[4:0] |
| 寄存器-状态/清除 | 12.4.2-12.4.3 | MPU_SR / MPU_ECLR |
| 寄存器-写保护 | 12.4.4 | MPU_WP：0x96A5 解锁 |
| 寄存器-SMPU1 | 12.4.5-12.4.8 | S1RGE/S1RGWP/S1RGRP/S1CR |
| 寄存器-SMPU2 | 12.4.9-12.4.12 | S2RGE/S2RGWP/S2RGRP/S2CR |
| 寄存器-FMPU/HMPU/EMPU | 12.4.13-12.4.20 | FxRGE/FxRGWP/FxRGRP/FxCR 等 |
| 寄存器-IPMPU | 12.4.21 | MPU_IPPR：IP 访问保护 |

## 寄存器速查

> BASE_ADDR: 0x40050000

| 寄存器 | 偏移 | 用途 | 关键位字段 |
|--------|------|------|-----------|
| MPU_RGD0~15 | 0x00~0x3C | 区域范围描述 | MPURGnADDR[31:5], MPURGnSIZE[4:0] |
| MPU_SR | 0x40 | 状态标志（只读） | EMPUEAF/HMPUEAF/FMPUEAF/SMPU2EAF/SMPU1EAF |
| MPU_ECLR | 0x44 | 错误标志清除 | 写1清对应标志 |
| MPU_WP | 0x48 | 写保护 | 写 0x96A5 解锁, 0x96A4 加锁 |
| MPU_IPPR | 0x4C | IP 访问保护 | 各 bit 控制一个 IP |
| MPU_S1RGE | 0x50 | SMPU1 区域使能 | S1RG0E~S1RG15E |
| MPU_S1RGWP | 0x54 | SMPU1 写权限 | S1RG0WP~S1RG15WP |
| MPU_S1RGRP | 0x58 | SMPU1 读权限 | S1RG0RP~S1RG15RP |
| MPU_S1CR | 0x5C | SMPU1 控制 | SMPU1E, SMPU1ACT[1:0], SMPU1BWP, SMPU1BRP |
| MPU_S2xx/Fxx/Hxx/Exx | 0x60~0x9C | SMPU2/FMPU/HMPU/EMPU | 结构同 SMPU1，等 16 个 |

## 典型初始化流程

```c
/* === DMA 写保护示例 (保护 DMA2 对某区域的写访问) === */
stc_mpu_init_t stcMpuInit;
stc_mpu_region_init_t stcRegionInit;

// 1. 解除写保护（LL_PERIPH_MPU）
LL_PERIPH_WE(LL_PERIPH_MPU);

// 2. 配置 MPU 全局：DMA2 违例产生 NMI，背景区域允许读写
(void)MPU_StructInit(&stcMpuInit);
stcMpuInit.stcDma2.u32ExceptionType  = MPU_EXP_TYPE_NMI;
stcMpuInit.stcDma2.u32BackgroundWrite = MPU_BACKGROUND_WR_ENABLE;
stcMpuInit.stcDma2.u32BackgroundRead  = MPU_BACKGROUND_RD_ENABLE;
(void)MPU_Init(&stcMpuInit);

// 3. 配置保护区域：禁止 DMA2 写，允许读
(void)MPU_RegionStructInit(&stcRegionInit);
stcRegionInit.u32BaseAddr            = (uint32_t)protectedBuf;  // 对齐到区域大小
stcRegionInit.u32Size                = MPU_REGION_SIZE_1KBYTE;
stcRegionInit.stcDma2.u32RegionWrite = MPU_REGION_WR_DISABLE;
stcRegionInit.stcDma2.u32RegionRead  = MPU_REGION_RD_ENABLE;
(void)MPU_RegionInit(MPU_REGION_NUM2, &stcRegionInit);
MPU_RegionCmd(MPU_REGION_NUM2, MPU_UNIT_DMA2, ENABLE);
```

## 常见陷阱与注意事项

1. ⚠️ **区域基地址对齐**：基地址低 (SIZE+1) 位必须为 0，否则保护范围不正确。缓冲区需用 `__align(n)` 对齐
2. ⚠️ **写保护解锁**：MPU 寄存器受写保护，操作前必须 `LL_PERIPH_WE(LL_PERIPH_MPU)`（或写 MPU_WP=0x96A5）
3. ⚠️ **重叠区域禁止优先**：多区域重叠时禁止权限优先于允许权限
4. ⚠️ **先配置再使能**：应在设好区域范围/权限/动作后再使能对应 MPU 单元
5. ⚠️ **NMI 处理需检查具体标志**：NMI_SRC_BUS_ERR 触发后需通过 MPU_GetStatus() 判断是哪个 DMA 违例
6. ⚠️ **ARM MPU 独立于片上 MPU**：CPU 的 ARM MPU（8 区域）使用 Cortex-M4 标准接口配置，与片上 SMPU/FMPU/HMPU/EMPU 无关
7. ⚠️ **IPMPU 仅非特权模式有效**：特权模式下 IPMPU 不阻止访问

## 官方例程索引

| 例程名 | 绝对路径 | 用途简述 |
|--------|---------|---------|
| mpu_core_write_protect | `$EXAMPLES\mpu\mpu_core_write_protect` | ARM MPU：保护 CPU 对指定区域的写访问 |
| mpu_dma_write_protect | `$EXAMPLES\mpu\mpu_dma_write_protect` | SMPU：保护 DMA2 对缓冲区的写访问，违例触发 NMI |
| mpu_ip_read_protect | `$EXAMPLES\mpu\mpu_ip_read_protect` | IPMPU：保护非特权模式下对 IP 的读访问 |

> `$EXAMPLES` = `D:\Dev\SDKs\HC32\HC32F4A0\HC32F4A0_DDL_Rev2.4.0\projects\ev_hc32f4a0_lqfp176\examples`

## 相关应用笔记

暂无匹配的应用笔记。

## 源文件引用

- **手册 Markdown**: `D:\Library\10_Datasheets\11_MCU\HC32系列\HC32F4A0\11-MPU-存储保护单元\11-MPU-存储保护单元.md`
- **手册 PDF**: `D:\Library\10_Datasheets\11_MCU\HC32系列\HC32F4A0\RM_HC32F4A0系列参考手册_Rev1.40.pdf`
