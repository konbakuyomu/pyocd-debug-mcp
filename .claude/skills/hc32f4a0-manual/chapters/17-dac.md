# DAC — 数模转换器

> ✅ 本知识卡已填充。最后更新：2026-03-25

## 模块概述

HC32F4A0 内置 2 个 12 位 DAC 单元（DAC1/DAC2），每单元含 2 个独立转换通道，共 4 路模拟输出。支持独立转换和同步转换（同一单元的两通道同步更新）。每通道配有输出放大器可直接驱动外部负载。可选 DCU 外部数据作为转换数据源（输出三角波/锯齿波）。A/D 转换优先模式可避免 D/A 转换浪涌电流对正在进行的 ADC 采样产生干扰。独立参考电压引脚 VREFH/VREFL 可提高转换精度。输出可供 CMP 作为负端电压。

## 关键特性

- 2 个 DAC 单元（DAC1/DAC2），每单元 2 通道，共 4 路 12 位 D/A 输出
- 12 位转换数据支持左对齐/右对齐格式（DPSEL 选择）
- 同步转换：对同一单元的 DADR 进行 32 位操作可实现双通道同步
- 外部数据转换：DAC1-ch1/ch2 ↔ DCU1/DCU2，DAC2-ch1/ch2 ↔ DCU3/DCU4
- 输出放大器：每通道独立使能（DAAMPy），可直接驱动外部负载
- A/D 转换优先模式：D/A 转换等待 ADC 完成后再启动，避免浪涌干扰
- 模拟输出控制（DAOCR）：可关闭 DACx_OUTy 引脚输出，仅供内部 CMP 使用
- 独立参考电压引脚 VREFH/VREFL
- 输出电压公式：DACoutput = ConversionData / 4096 × VREFH

## 功能导航大纲

> 小节编号对应原始手册 `17-DAC-数模转换器.md` 中的标题。

| 区域 | 小节 | 关键内容 |
|------|------|----------|
| 概述 | 18.1 | 简介、主要特性列表 |
| 框图 | 18.2 | 功能框图、DAC 引脚表 |
| **D/A 转换** | 18.3.1 | 单通道独立转换步骤（4 步）、输出电压公式 |
| **同步转换** | 18.3.2 | DAE 位控制双通道同步、32 位写 DADR |
| 外部数据转换 | 18.3.3 | DCU 数据源选择、EXTDSLy 位、禁止使用放大器和 ADP |
| **A/D 转换优先模式** | 18.3.4 | ADPEN 使能、ADCSL1~3 选择 ADC 单元、DAxSF 状态标志 |
| 注意事项 | 18.4 | 模块停止、停止低功耗、掉电模式下 DAC 行为、放大器初始化 |
| 寄存器 | 18.5 | DADR/DACR/DAOCR/DAADPCR |

## 寄存器速查

> DAC1: 0x40041000, DAC2: 0x40041400

| 寄存器 | 偏移 | 宽度 | 用途 | 关键位字段 |
|--------|------|------|------|-----------|
| DADRx_1 | 0x00 | 16 | 通道 1 数据 | 12 位转换数据（左/右对齐） |
| DADRx_2 | 0x02 | 16 | 通道 2 数据 | 12 位转换数据（左/右对齐） |
| **DACRx** | 0x04 | 16 | 控制寄存器 | DAE[0] 同步使能, DA1E[1]/DA2E[2] 通道使能, DPSEL[8] 对齐, DAAMP1[9]/DAAMP2[10] 放大器, EXTDSL1[11]/EXTDSL2[12] 外部数据 |
| **DAADPCRx** | 0x06 | 16 | A/D 优先控制 | ADPEN[15] 优先模式, ADCSL1~3[2:0] ADC 选择, DA1SF[8]/DA2SF[9] 状态 |
| DAOCRx | 0x1C | 16 | 模拟输出控制 | DAODIS1/DAODIS2 输出禁止（仅供 CMP 内部使用时关闭引脚输出） |

## 典型初始化流程

```c
/* === 单通道 D/A 转换 === */
// 1. 使能 DAC 时钟
LL_PERIPH_WE(LL_PERIPH_GPIO | LL_PERIPH_FCG);
FCG_Fcg3PeriphClockCmd(FCG3_PERIPH_DAC1, ENABLE);  // 或 FCG3_PERIPH_DAC2

// 2. 配置输出引脚为模拟属性
stc_gpio_init_t stcGpioInit;
(void)GPIO_StructInit(&stcGpioInit);
stcGpioInit.u16PinAttr = PIN_ATTR_ANALOG;
(void)GPIO_Init(DAC1_OUT1_PORT, DAC1_OUT1_PIN, &stcGpioInit);

// 3. 初始化 DAC
stc_dac_init_t stcDacInit;
DAC_DeInit(CM_DAC1);
(void)DAC_StructInit(&stcDacInit);
stcDacInit.u16Align = DAC_DATA_ALIGN_R;  // 右对齐
(void)DAC_Init(CM_DAC1, DAC_CH1, &stcDacInit);

// 4. 启动转换 + 写数据
DAC_Start(CM_DAC1, DAC_CH1);
DAC_SetChData(CM_DAC1, DAC_CH1, 2048U);  // 输出 VREFH/2

/* === 使用输出放大器 === */
DAC_SetChData(CM_DAC1, DAC_CH1, 0U);     // 先写 0
DAC_AMPCmd(CM_DAC1, DAC_CH1, ENABLE);     // 使能放大器
DAC_Start(CM_DAC1, DAC_CH1);              // 启动转换
DDL_DelayUS(3U);                          // 等待 3μs
DAC_SetChData(CM_DAC1, DAC_CH1, data);    // 写实际数据

/* === A/D 转换优先模式 === */
// 确认 ADC 停止后：
DAC_ADCPrioConfig(CM_DAC1, DAC_ADP_SEL_ADC1, ENABLE);
DAC_ADCPrioCmd(CM_DAC1, ENABLE);
```

## 常见陷阱与注意事项

1. ⚠️ **模块停止后需解除才能访问寄存器**：系统复位后 DAC 处于模块停止状态，必须先通过 FCG3 使能时钟
2. ⚠️ **放大器必须按固定顺序初始化**：先写 DADR=0 → 使能 DAAMP → 使能 DAE/DAyE → 等 3μs → 再写实际数据。关闭后重用须重复全流程
3. ⚠️ **外部数据模式禁止使用放大器和 ADP**：EXTDSLy=1 时 DAAMP 和 ADPEN 均无效
4. ⚠️ **ADP 模式下数据可能丢失**：ADC 运行时写 DADR 不会立即转换，若在转换前再次写入则前一次数据丢失。应先查 DAxSF 确认更新完成
5. ⚠️ **ADP 模式设置须在 ADC 停止时进行**：设定 DA1E/DA2E/DAE 和 ADPEN 时确保 ADST=0，且 ADC 触发设为软件触发
6. ⚠️ **模块停止/停止低功耗时模拟输出保持**：DAC 进入停止状态后输出保持，电流不降低，需 DAyE=0 + DAE=0 才能真正省电
7. ⚠️ **掉电低功耗模式输出变高阻**：进入掉电模式后 DAC 输出自动变为高阻态

## 官方例程索引

| 例程名 | 绝对路径 | 用途简述 |
|--------|---------|---------|
| dac_base | `$EXAMPLES\dac\dac_base` | 单通道转换：MAU 生成正弦表 → DAC 输出正弦波，支持 ADP 模式可选 |
| dac_sync_mode | `$EXAMPLES\dac\dac_sync_mode` | 同步转换：双通道同步输出正弦波 |

> `$EXAMPLES` = `D:\Dev\SDKs\HC32\HC32F4A0\HC32F4A0_DDL_Rev2.4.0\projects\ev_hc32f4a0_lqfp176\examples`

## 相关应用笔记

（未找到独立的 DAC 应用笔记）

## 源文件引用

- **手册 Markdown**: `D:\Library\10_Datasheets\11_MCU\HC32系列\HC32F4A0\17-DAC-数模转换器\17-DAC-数模转换器.md`
- **手册 PDF**: `D:\Library\10_Datasheets\11_MCU\HC32系列\HC32F4A0\RM_HC32F4A0系列参考手册_Rev1.40.pdf`
