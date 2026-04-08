# pyocd-debug-mcp

> **让 AI 全自动进行嵌入式单片机仿真调试的 MCP Server**

通过 [pyOCD](https://pyocd.io/) + CMSIS-DAP 探针，为 Claude / GitHub Copilot 等 AI 工具提供 **45 个调试工具**，涵盖从连接探针、烧录固件、打断点、读寄存器到 HardFault 故障分析的完整调试流程。

## ✨ 核心能力

| 能力 | 说明 |
|------|------|
| 🔌 探针管理 | 自动发现 CMSIS-DAP 探针，连接/断开 |
| ⚡ 烧录 | 支持 `.hex` / `.bin` / `.elf` 固件烧录 |
| 🎯 断点 & 监视点 | 硬件断点（地址/符号名）、数据监视点（读/写/读写） |
| ⏳ 等待机制 | `wait_halt` — AI 打断点 → 运行 → 等待命中 → 分析 |
| 📊 变量采样 | 周期性采样全局变量，返回统计数据 |
| 💥 故障分析 | HardFault/BusFault/UsageFault 全自动解析 |
| 📏 栈溢出检测 | 支持 RT-Thread / FreeRTOS TCB 栈边界检查 |
| 🔍 栈回溯 | 启发式扫描 + BL 验证 + FDE 函数边界增强 |
| 🔧 寄存器 & 内存 | 读/写 CPU 寄存器、内存、外设寄存器（SVD） |
| 📋 符号解析 | 通过 ELF 文件将地址映射到函数名/变量名 |

## 📦 安装

### 前置条件

- Python ≥ 3.10
- [uv](https://docs.astral.sh/uv/) 包管理器（推荐）
- CMSIS-DAP 兼容调试探针（DAPLink / STLINK 等）

### 方式一：从 GitHub 安装（推荐）

```bash
# 使用 uv
uv pip install git+https://github.com/konbakuyomu/pyocd-debug-mcp.git

# 使用 pip
pip install git+https://github.com/konbakuyomu/pyocd-debug-mcp.git

# 如需 SVD 字段级解析（可选）
uv pip install "pyocd-debug-mcp[svd] @ git+https://github.com/konbakuyomu/pyocd-debug-mcp.git"
```

### 方式二：本地开发安装

```bash
git clone https://github.com/konbakuyomu/pyocd-debug-mcp.git
cd pyocd-debug-mcp
uv sync          # 创建虚拟环境并安装依赖
```

### HC32 系列芯片支持

HC32 芯片需要安装 CMSIS-Pack：

```bash
uv run pyocd pack install hc32f460
uv run pyocd pack install hc32f4a0
```

## 🔧 注册到 AI 工具

### Claude Desktop

在 `claude_desktop_config.json` 中添加：

```json
{
  "mcpServers": {
    "pyocd-debug": {
      "command": "uv",
      "args": [
        "--directory", "/path/to/pyocd-debug-mcp",
        "run", "pyocd-debug-mcp"
      ]
    }
  }
}
```

### Claude Code (CLI)

```bash
claude mcp add pyocd-debug -- uv --directory /path/to/pyocd-debug-mcp run pyocd-debug-mcp
```

### GitHub Copilot (VS Code)

在 `.vscode/mcp.json` 中添加：

```json
{
  "servers": {
    "pyocd-debug": {
      "command": "uv",
      "args": [
        "--directory", "/path/to/pyocd-debug-mcp",
        "run", "pyocd-debug-mcp"
      ]
    }
  }
}
```

> 💡 将 `/path/to/pyocd-debug-mcp` 替换为你的实际路径。Windows 下使用 `\\` 或 `/` 均可。

## 🛠️ 工具列表（45 个）

### 探针 & 会话

| 工具名 | 说明 |
|--------|------|
| `pyocd_probe_list` | 列出所有已连接的 CMSIS-DAP 调试探针 |
| `pyocd_probe_info` | 获取指定探针详细信息 |
| `pyocd_session_connect` | 连接探针并打开调试会话 |
| `pyocd_session_disconnect` | 断开调试会话，释放探针 |
| `pyocd_session_status` | 查看当前会话状态 |

### 烧录

| 工具名 | 说明 |
|--------|------|
| `pyocd_flash_program` | 烧录固件（.hex / .bin / .elf） |
| `pyocd_flash_erase` | 擦除 Flash |

### 目标控制

| 工具名 | 说明 |
|--------|------|
| `pyocd_target_halt` | 暂停 CPU |
| `pyocd_target_resume` | 恢复运行 |
| `pyocd_target_step` | 单步执行 |
| `pyocd_target_reset` | 复位 MCU |
| `pyocd_target_status` | 获取目标状态（运行/停止）及关键寄存器 |
| `pyocd_target_wait_halt` | ⏳ **等待目标停止**（断点命中/监视点触发） |
| `pyocd_target_list_supported` | 列出 pyOCD 支持的所有 MCU（206+） |

### 寄存器 & 内存

| 工具名 | 说明 |
|--------|------|
| `pyocd_register_read` | 读取 CPU 寄存器 |
| `pyocd_register_write` | 写入 CPU 寄存器 |
| `pyocd_register_read_all` | 读取全部寄存器（含 FPU） |
| `pyocd_memory_read` | 读内存 |
| `pyocd_memory_write` | 写内存（带 readback 验证） |
| `pyocd_memory_write_block` | 块写入 |
| `pyocd_memory_dump` | Hex dump 格式输出 |

### 断点 & 监视点

| 工具名 | 说明 |
|--------|------|
| `pyocd_breakpoint_set` | 设置硬件断点（地址或符号名） |
| `pyocd_breakpoint_clear` | 清除断点 |
| `pyocd_breakpoint_clear_all` | 清除所有断点 |
| `pyocd_breakpoint_list` | 列出当前断点 |
| `pyocd_watchpoint_set` | 设置数据监视点（读/写/读写触发） |
| `pyocd_watchpoint_clear` | 清除监视点 |
| `pyocd_watchpoint_clear_all` | 清除所有监视点 |
| `pyocd_watchpoint_list` | 列出当前监视点 |

### ELF 符号

| 工具名 | 说明 |
|--------|------|
| `pyocd_elf_attach` | 加载 ELF 文件用于符号解析 |
| `pyocd_elf_lookup` | 按名称查找符号地址 |
| `pyocd_elf_symbols` | 列出 ELF 中的符号（函数/变量） |
| `pyocd_elf_info` | 获取 ELF 文件信息 |
| `pyocd_elf_address_to_symbol` | 地址→符号反查（PC/LR→函数名+偏移） |

### SVD 外设寄存器

| 工具名 | 说明 |
|--------|------|
| `pyocd_svd_attach` | 加载 SVD 文件 |
| `pyocd_svd_list_peripherals` | 列出所有外设 |
| `pyocd_svd_list_registers` | 列出外设的寄存器 |
| `pyocd_svd_read` | 按名称读外设寄存器（含位域解析） |
| `pyocd_svd_write` | 按名称写外设寄存器 |
| `pyocd_svd_list_fields` | 列出寄存器的所有位域（名称、位范围、宽度） |
| `pyocd_svd_set_field` | 设置单个位域值（read-modify-write，不影响其他位域） |

### 高级调试

| 工具名 | 说明 |
|--------|------|
| `pyocd_debug_fault_analyze` | 💥 分析 HardFault 崩溃（SCB 寄存器 + 异常栈帧 + EXC_RETURN + backtrace） |
| `pyocd_debug_stack_overflow_check` | 📏 检查线程栈溢出（RT-Thread / FreeRTOS） |
| `pyocd_debug_sample_variable` | 📊 周期性采样变量（如每 0.5s 采样 200 次） |
| `pyocd_debug_backtrace` | 🔍 栈回溯 — 显示完整调用链（启发式 + BL 验证 + FDE 增强） |

## 🚀 典型调试流程

以下是 AI 使用此 MCP Server 进行调试的典型对话流程：

### 1. 连接 → 烧录 → 运行到 main

```
AI: pyocd_probe_list                           → 发现探针
AI: pyocd_session_connect("hc32f460xe")        → 连接
AI: pyocd_flash_program("firmware.hex")        → 烧录
AI: pyocd_elf_attach("firmware.elf")           → 加载符号
AI: pyocd_breakpoint_set(symbol="main")        → 在 main 打断点
AI: pyocd_target_reset(halt=true)              → 复位并停止
AI: pyocd_target_wait_halt(timeout=10)         → 等待命中 main
```

### 2. 串口数据调试（等待断点）

```
AI: pyocd_breakpoint_set(symbol="UART_RxCallback")
AI: pyocd_target_wait_halt(timeout=60)         ← 等待数据到来
    ... 60s 内数据到达，断点命中 ...
AI: pyocd_memory_dump(rx_buffer_addr, 64)      → 查看接收缓冲区
AI: pyocd_register_read_all()                  → 查看寄存器现场
```

### 3. 周期性变量监控

```
AI: pyocd_debug_sample_variable(
      address=0x20001000,   # 全局变量地址
      interval=0.5,          # 每 0.5s
      count=200              # 共 200 次 = 100s
    )
→ 返回所有采样值 + min/max/变化统计
```

### 4. HardFault 崩溃分析

```
AI: pyocd_debug_fault_analyze()
→ 返回:
  - fault_type: "BusFault"
  - fault_address: "0x40012400"
  - active_faults: [PRECISERR, BFARVALID]
  - exception_frame: {PC_fault, LR_saved, R0-R3, ...}
  - exc_return: {stack_used: "PSP", fpu_context: ...}
```

### 5. 野指针/数组越界追踪

```
AI: pyocd_watchpoint_set(
      address=0x20002000,    # 数组末尾地址
      size=4,
      access_type="write"    # 监控越界写入
    )
AI: pyocd_target_wait_halt(timeout=30)
    ... 越界写入发生，DWT 触发停止 ...
AI: pyocd_target_status()                      → 查看 PC 定位到写入指令
AI: pyocd_debug_backtrace()                    → 查看完整调用链
```

### 6. 栈回溯（查看完整调用链）

```
AI: pyocd_debug_backtrace(scan_depth=512, max_frames=16)
→ 返回:
  frames:
    [0] main+0x1A                    (current_pc)
    [1] USART_Receive_DMA+0x42       (lr_register)
    [2] DMA_IrqHandler+0x18          (stack_scan, SP+0x24)
    [3] SystemInit                    (stack_scan, SP+0x48)
  method: "fde_enhanced_heuristic"     ← ELF 提供 282 函数边界增强
  function_map_entries: 282

# wait_halt 断点命中时自动附带简短 backtrace:
AI: pyocd_target_wait_halt(timeout=30)
→ { ..., "backtrace": ["UART_RxCallback", "DMA_IrqHandler+0x18", "main+0x1A"] }

# fault_analyze 崩溃时自动附带 backtrace:
AI: pyocd_debug_fault_analyze()
→ { ..., "backtrace": ["HardFault_Handler", "memcpy+0x12", "cJSON_Parse+0x8A", ...] }
```

## 🏗️ 项目结构

```
pyocd-debug-mcp/
├── pyproject.toml              # 项目配置和依赖
├── src/pyocd_debug_mcp/
│   ├── server.py               # MCP Server 入口，45 个工具注册
│   ├── session_manager.py      # 会话生命周期管理（单例）
│   └── tools/
│       ├── probe.py            # 探针发现
│       ├── target.py           # 目标控制
│       ├── flash.py            # Flash 烧录
│       ├── register.py         # 寄存器读写
│       ├── memory.py           # 内存读写
│       ├── breakpoint.py       # 断点管理
│       ├── watchpoint.py       # 监视点管理
│       ├── elf.py              # ELF 符号解析
│       ├── svd.py              # SVD 外设寄存器
│       └── debug.py            # 高级调试（故障分析、栈回溯、栈检查、采样）
└── tests/
```

## ⚙️ 支持的硬件

- **调试探针**: 所有 CMSIS-DAP 兼容探针（DAPLink、STLINK via pyOCD、J-Link via pyOCD）
- **MCU**: pyOCD 支持的 206+ 种芯片，包括：
  - **HDSC/XHSC**: HC32F460、HC32F4A0 等
  - **STMicroelectronics**: STM32F0/F1/F2/F3/F4/F7/H7/L0/L4/G0/G4 等
  - **Nordic**: nRF52832、nRF52840、nRF9160 等
  - **NXP**: LPC、Kinetis、i.MX RT 等
  - 更多: `pyocd_target_list_supported` 查看完整列表

## 📄 License

MIT