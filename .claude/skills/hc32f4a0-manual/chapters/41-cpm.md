# CPM — 加密协处理模块

> ✅ 本知识卡已填充。最后更新：2026-03-26

## 模块概述

CPM（Cryptographic Processing Module）加密协处理模块包含三个子模块：AES 加解密算法处理器（128/192/256 位密钥）、HASH 安全散列算法（SHA-256 + HMAC）、TRNG 真随机数发生器（64 位随机数）。三个子模块各自独立，拥有独立的寄存器基址。

## 关键特性

### AES 子模块
- **算法**：FIPS PUB 197 标准 AES 加解密
- **密钥长度**：128/192/256 位
- **分组长度**：固定 128 位
- **运算周期**：加密 220~300 cycles，解密 290~398 cycles（按密钥长度递增）
- **操作**：写数据→写密钥→设模式→START=1→等 START 清零→读结果

### HASH 子模块
- **算法**：SHA-256（FIPS PUB 180-3），256 位摘要输出
- **消息长度**：最大 2^64 位
- **HMAC**：硬件支持，可选长密钥/短密钥模式
- **DMA 联动**：支持 DMA 传输数据 + 硬件触发事件自动启动运算
- **中断**：每组运算完成中断（HEIE）+ 全部运算完成中断（HCIE）

### TRNG 子模块
- **输出**：64 位真随机数
- **原理**：连续模拟噪声 → 算法捕捉 → 数据输出
- **移位次数**：32/64/128/256 次可配置
- **要求**：PCLK4 频率须 ≤ 1MHz 以获得好的随机数

## 功能导航大纲

> 小节编号对应原始手册标题

| 区域 | 小节 | 关键内容 |
|------|------|----------|
| AES 简介 | 42.2.1 | AES 算法原理（SubBytes/ShiftRows/MixColumns/AddRoundKey） |
| AES 加密流程 | 42.2.3 | 写数据→写密钥→设 KEYSIZE/MODE→START |
| AES 解密流程 | 42.2.4 | 与加密类似，MODE=1 |
| AES 运行时间 | 42.2.6 | 128位:220/290, 192位:260/332, 256位:300/398 cycles |
| HASH 操作 | 42.3.2 | 软件流程/DMA 流程，512 位分组 |
| HASH 消息填充 | 42.3.3 | 1+0s+64bit长度 填充至 512 位倍数 |
| HMAC | 42.3.4 | 密钥+消息两阶段，LKEY 长密钥选择 |
| TRNG 操作 | 42.4.2 | EN→配置 MR→RUN→读 DR→关 EN |
| AES 寄存器 | 42.2.8 | AES_CR/DR/KR |
| HASH 寄存器 | 42.3.7 | HASH_CR/HR/DR |
| TRNG 寄存器 | 42.4.5 | TRNG_CR/MR/DR |

## 寄存器速查

> AES: 0x40008000 | HASH: 0x40008400 | TRNG: 0x40042000

| 寄存器 | 偏移 | 用途 |
|--------|------|------|
| AES_CR | AES+0x00 | 控制（START/MODE/KEYSIZE） |
| AES_DR0~3 | AES+0x10~0x1C | 128 位数据（加密前明文/后密文） |
| AES_KR0~7 | AES+0x20~0x3C | 128/192/256 位密钥 |
| HASH_CR | HASH+0x00 | 控制（START/FST_GRP/KMSG_END/MODE/LKEY/BUSY/HEIE/HCIE） |
| HASH_HR0~7 | HASH+0x10~0x2C | 256 位摘要输出 |
| HASH_DR0~15 | HASH+0x40~0x7C | 512 位数据输入 |
| TRNG_CR | TRNG+0x00 | 控制（EN/RUN） |
| TRNG_MR | TRNG+0x04 | 模式（LOAD/CNT 移位次数） |
| TRNG_DR0~1 | TRNG+0x0C~0x10 | 64 位随机数输出 |

## 典型初始化流程

```c
/* AES-128 加密示例 */

/* 1. 使能时钟 */
FCG_Fcg0PeriphClockCmd(FCG0_PERIPH_AES, ENABLE);

/* 2. 写入 128 位明文 */
uint32_t au32Data[4] = {0x33221100, 0x77665544, 0xBBAA9988, 0xFFEEDDCC};
AES_WriteData(au32Data);

/* 3. 写入 128 位密钥 */
uint32_t au32Key[4] = {0x03020100, 0x07060504, 0x0B0A0908, 0x0F0E0D0C};
AES_WriteKey(au32Key);

/* 4. 启动加密 */
AES_Encrypt(au32Data, 4U, au32Key, 4U, au32Result);
/* 等待 START 自动清零后读取结果 */

/* TRNG 示例 */
FCG_Fcg0PeriphClockCmd(FCG0_PERIPH_TRNG, ENABLE);
uint32_t au32Random[2];
TRNG_Generate(au32Random, 2U);
```

## 常见陷阱与注意事项

1. **运算中不可写寄存器**：AES/HASH 在 START=1（运算中）时，写操作会被硬件忽略
2. **运算中读数据得全 0**：运算过程中读 AES_DR/HASH_HR 将得到全 0
3. **AES 数据寄存器复用**：加密后数据寄存器内容变为密文，若下次运算数据即为本次结果则无需重写
4. **HASH 消息须预填充**：软件必须按 SHA-256 规则将消息填充到 512 位的整数倍
5. **HASH 第一组须设 FST_GRP**：每次新运算的第一个 512 位数据块须置 FST_GRP=1
6. **HMAC 长密钥**：密钥超过 64 字节时须设 LKEY=1，硬件自动用 SHA-256 压缩密钥
7. **TRNG 需低频 PCLK4**：PCLK4 须 ≤ 1MHz 才能获得好的随机数质量
8. **TRNG 首次需 LOAD**：首次生成使用 LOAD=1 装载新初始值
9. **密钥寄存器按长度写入**：128 位写 KR0~3，192 位写 KR0~5，256 位写 KR0~7

## 官方例程索引

| 例程名 | 绝对路径 | 用途简述 |
|--------|---------|--------:|
| aes_base | `$EXAMPLES\aes\aes_base` | AES 加解密基础演示 |
| hash_base | `$EXAMPLES\hash\hash_base` | SHA-256 哈希运算 |
| hash_hmac | `$EXAMPLES\hash\hash_hmac` | HMAC 消息认证 |
| trng_base | `$EXAMPLES\trng\trng_base` | 真随机数生成 |

> `$EXAMPLES` = `D:\Dev\SDKs\HC32\HC32F4A0\HC32F4A0_DDL_Rev2.4.0\projects\ev_hc32f4a0_lqfp176\examples`

## 相关应用笔记

暂无专属 CPM 应用笔记。

## 源文件引用

- **手册 Markdown**: `D:\Library\10_Datasheets\11_MCU\HC32系列\HC32F4A0\41-CPM-加密协处理模块\41-CPM-加密协处理模块.md`
- **手册 PDF**: `D:\Library\10_Datasheets\11_MCU\HC32系列\HC32F4A0\RM_HC32F4A0系列参考手册_Rev1.40.pdf`
