# DVP — 数字视频接口

> ✅ 本知识卡已填充。最后更新：2026-03-25

## 模块概述

DVP（Digital Video Port）是一个同步并行接口，用于采集外部 CMOS 摄像头模块传入的 8/10/12/14 位高速数据流。支持硬件同步（VSYNC/HSYNC）和软件同步（嵌入式同步码）两种方式，支持单色/拜尔格式、YCbCr4:2:2、RGB565、JPEG 等数据格式。内置 8 字深度 FIFO，支持窗口裁剪和帧采集频率控制。

## 关键特性

- **数据宽度**：8/10/12/14 位并行接口（BITSEL 选择）
- **数据格式**：单色、YCbCr4:2:2、RGB565、JPEG 压缩数据
- **采集模式**：单帧模式（自动停止）+ 连续模式
- **帧频控制**：全帧 / 隔 1 帧 / 隔 3 帧采集（降低带宽 50%/75%）
- **同步方式**：硬件同步（VSYNC/HSYNC 引脚）+ 软件同步（0xFF0000XY 嵌入式同步码）
- **窗口裁剪**：可指定起始行/列偏移和窗口尺寸（14 位精度）
- **FIFO**：8 字深度，溢出时产生错误中断
- **DMA**：每收到完整 32 位数据块触发 DMA 请求（事件号 90）
- **中断**：帧开始/结束、行开始/结束、软件同步错误、FIFO 溢出错误
- **引脚**：DVP_PIXCLK、DVP_VSYNC、DVP_HSYNC、DVP_DATA[13:0]
- **时钟极性可配**：PIXCLK 上升沿/下降沿采集，VSYNC/HSYNC 高/低电平有效

## 功能导航大纲

> 小节编号对应原始手册标题

| 区域 | 小节 | 关键内容 |
|------|------|----------|
| 简介 | 41.1 | DVP 功能和特性总览 |
| 系统框图 | 41.2 | 端口列表、基本框图 |
| 视频数据格式 | 41.3.1 | 单色/YCbCr/RGB565/JPEG 存储方式 |
| 并口存储格式 | 41.3.2 | 8/10/12/14 位数据排布和 32 位字对齐 |
| 模式选择 | 41.3.3 | 单帧模式、连续模式、帧采集频率控制 |
| 同步控制 | 41.3.4 | 软件同步码机制、硬件同步 |
| 窗口裁剪 | 41.3.5 | 起始坐标 + 尺寸配置 |
| FIFO/DMA | 41.3.6~7 | 8 字 FIFO、DMA 传输触发 |
| 中断 | 41.4 | 帧传送中断、同步错误、FIFO 溢出 |
| 寄存器 | 41.5 | 9 个寄存器详述 |

## 寄存器速查

> 基址: 0x40055800

| 寄存器 | 偏移 | 用途 | 关键位字段 |
|--------|------|------|-----------:|
| DVP_CTR | 0x0000 | 控制寄存器 | DVPEN, BITSEL[1:0], CAPFRC[1:0], VSYNCSEL, HSYNCSEL, PIXCKSEL, SWSYNC, JPEGEN, CROPEN, CAPMD, CAPEN |
| DVP_DTR | 0x0004 | 数据寄存器 | DTR[31:0]（只读） |
| DVP_STR | 0x0008 | 状态寄存器 | FIFOERF, SQUERF, FEF, LEF, LSF, FSF |
| DVP_IER | 0x000C | 中断使能 | FIFOERIEN, SQUERIEN, FEIEN, LEIEN, LSIEN, FSIEN |
| DVP_DMR | 0x0010 | DMA 数据传输 | DMR[31:0]（DMA 读 FIFO） |
| DVP_SSYNDR | 0x0020 | 软件同步数据 | FEDAT/LEDAT/LSDAT/FSDAT 各 8 位 |
| DVP_SSYNMR | 0x0024 | 软件同步屏蔽 | FEMSK/LEMSK/LSMSK/FSMSK 各 8 位 |
| DVP_CPSFTR | 0x0028 | 窗口裁剪偏移 | CSHIFT[13:0]（行偏移）, RSHIFT[13:0]（列偏移） |
| DVP_CPSZER | 0x002C | 窗口裁剪尺寸 | CSIZE[13:0]（行数）, RSIZE[13:0]（列数） |

## 典型初始化流程

```c
/* 以 OV5640 摄像头 8 位硬件同步连续采集为例 */

/* 1. 使能时钟 */
FCG_Fcg3PeriphClockCmd(FCG3_PERIPH_DVP, ENABLE);

/* 2. GPIO 配置：DVP 引脚复用 */
/* DVP_PIXCLK, DVP_VSYNC, DVP_HSYNC, DVP_DATA[7:0] 设为对应复用功能 */

/* 3. DVP 初始化 */
stc_dvp_init_t stcDvpInit;
DVP_StructInit(&stcDvpInit);
stcDvpInit.u32CaptureMode  = DVP_CAPT_MD_CONTINUE;   /* 连续模式 */
stcDvpInit.u32CaptureFreq  = DVP_CAPT_FREQ_ALL;       /* 全帧采集 */
stcDvpInit.u32DataWidth    = DVP_DATA_WIDTH_8BIT;      /* 8 位 */
stcDvpInit.u32PixClkPolarity = DVP_PIXCLK_FALLING;    /* 下降沿采集 */
stcDvpInit.u32HSyncPolarity  = DVP_HSYNC_HIGH;
stcDvpInit.u32VSyncPolarity  = DVP_VSYNC_HIGH;
DVP_Init(&stcDvpInit);

/* 4. 配置 DMA（事件号 90）传输 DVP_DMR → 目标缓冲区 */

/* 5. 使能 DVP + 开始采集 */
DVP_Cmd(ENABLE);
DVP_CaptureCmd(ENABLE);
```

## 常见陷阱与注意事项

1. **软件同步仅支持 8 位**：软件同步模式只能用于 8 位数据接口 + 全帧采集，其他宽度或隔帧采集会产生不可预知结果
2. **JPEG 不支持窗口裁剪**：JPEG 模式下必须禁用窗口裁剪功能
3. **窗口尺寸列数须为 4 的倍数**：RSIZE[1:0] 固定为 0；软件同步时行偏移也以 4 的倍数偏移
4. **FIFO 溢出**：写入速度超过 AHB 承受速率时数据被覆盖，需配合 DMA 及时搬运
5. **连续模式停止**：CAPEN 写 0 后需等到当前帧结束才真正清零
6. **单帧模式**：一帧完成后 CAPEN 自动清零，无需手动清
7. **10/12/14 位格式**：数据存储为 16 位字，高位补零，每 2 个像素时钟生成一个 32 位字
8. **DMA 事件号 90**：需在 INTC/DMA 模块中正确映射此事件
9. **JPEG 行尾填充**：字节数非 4 倍数时自动用 0 填充至 32 位对齐

## 官方例程索引

| 例程名 | 绝对路径 | 用途简述 |
|--------|---------|--------:|
| dvp_camera_display | `$EXAMPLES\dvp\dvp_camera_display` | OV5640 摄像头采集 + LCD 显示 |

> `$EXAMPLES` = `D:\Dev\SDKs\HC32\HC32F4A0\HC32F4A0_DDL_Rev2.4.0\projects\ev_hc32f4a0_lqfp176\examples`

## 相关应用笔记

暂无专属 DVP 应用笔记。

## 源文件引用

- **手册 Markdown**: `D:\Library\10_Datasheets\11_MCU\HC32系列\HC32F4A0\40-DVP-数字视频接口\40-DVP-数字视频接口.md`
- **手册 PDF**: `D:\Library\10_Datasheets\11_MCU\HC32系列\HC32F4A0\RM_HC32F4A0系列参考手册_Rev1.40.pdf`
