# pyocd-debug-mcp

> **让 AI 全自动进行嵌入式单片机仿真调试的 MCP Server**

通过 [pyOCD](https://pyocd.io/) + CMSIS-DAP 探针，为 Claude / GitHub Copilot 等 AI 工具提供 **57 个调试工具**，涵盖从连接探针、烧录固件、打断点、读寄存器到 HardFault 故障分析的完整调试流程。

## ✨ 核心能力

| 能力 | 说明 |
|------|------|
| 🔌 探针管理 | 自动发现 CMSIS-DAP 探针，连接/断开 |
| ⚡ 烧录 | 支持 `.hex` / `.bin` / `.elf` / `.axf` 固件烧录，烧录 ELF 自动附加符号 |
| ✅ Flash 校验 | 烧录后逐段对比验证，检测 Flash 损坏或烧录异常 |
| 🎯 断点 & 监视点 | 硬件断点 / 软件断点 / 自动选择（地址或符号名），数据监视点（读/写/读写） |
| 🔄 断点恢复 | Reset 后自动恢复所有断点（软件断点 Reset 后丢失，自动重设） |
| ⏳ 等待机制 | `wait_halt` — AI 打断点 → 运行 → 等待命中 → 分析 |
| 📊 变量采样 | 周期性采样全局变量，返回统计数据 |
| 💥 故障分析 | HardFault/BusFault/UsageFault 全自动解析 |
| 📏 栈溢出检测 | 支持 RT-Thread / FreeRTOS TCB 栈边界检查 |
| 🔍 栈回溯 | DWARF CFI / EHABI / 启发式三级容错，覆盖 AC5/AC6/GCC |
| 🔧 寄存器 & 内存 | 读/写 CPU 寄存器、内存、外设寄存器（SVD），支持批量位域更新和枚举值 |
| 📋 符号解析 | 通过 ELF 文件将地址映射到函数名/变量名 |
| 📡 RTT 实时传输 | SEGGER RTT 通道读写，免 UART 打印调试 |
| 🆕 地址格式 | 所有地址参数同时接受整数和十六进制字符串（如 `"0x1FFE000E"`） |
| 🆕 组合工具 | `read_symbol` 一步读取变量值、`step_out` 执行到函数返回 |

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

## 🛠️ 工具列表（57 个）

### 项目配置

| 工具名 | 说明 |
|--------|------|
| `pyocd_project_load` | 🆕 加载项目配置（`.pyocd-debug.json`），或自动发现固件/ELF/SVD 文件 |
| `pyocd_project_init` | 🆕 创建 `.pyocd-debug.json` 配置文件（路径自动转相对路径） |

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
| `pyocd_flash_program` | 烧录固件（.hex / .bin / .elf / .axf），烧录 ELF/AXF 自动附加符号 |
| `pyocd_flash_erase` | 擦除 Flash |
| `pyocd_flash_verify` | 🆕 校验 Flash 内容是否与固件文件一致（逐段对比） |

### 目标控制

| 工具名 | 说明 |
|--------|------|
| `pyocd_target_halt` | 暂停 CPU |
| `pyocd_target_resume` | 恢复运行 |
| `pyocd_target_step` | 单步执行 |
| `pyocd_target_reset` | 复位 MCU（自动恢复所有断点） |
| `pyocd_target_status` | 获取目标状态（运行/停止）及关键寄存器 |
| `pyocd_target_wait_halt` | ⏳ **等待目标停止**（断点命中/监视点触发），支持 `user_hint` 提示 |
| `pyocd_target_step_out` | 🆕 执行到当前函数返回（自动设临时断点在 LR） |
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
| `pyocd_breakpoint_set` | 设置断点（地址或符号名），支持 hw/sw/auto 三种类型 |
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
| `pyocd_read_symbol` | 🆕 **一步读取变量**：符号查找 + 内存读取组合工具 |
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
| `pyocd_svd_set_field` | 设置单个位域值（RMW，支持枚举名或整数） |
| `pyocd_svd_update_fields` | 🆕 批量设置多个位域（单次 RMW，原子操作） |
| `pyocd_svd_describe` | 🆕 查看外设/寄存器详细描述（含枚举值定义） |

### 高级调试

| 工具名 | 说明 |
|--------|------|
| `pyocd_debug_fault_analyze` | 💥 分析 HardFault 崩溃（SCB 寄存器 + 异常栈帧 + EXC_RETURN + backtrace） |
| `pyocd_debug_stack_overflow_check` | 📏 检查线程栈溢出（RT-Thread / FreeRTOS） |
| `pyocd_debug_sample_variable` | 📊 周期性采样变量（如每 0.5s 采样 200 次） |
| `pyocd_debug_backtrace` | 🔍 **精确栈回溯** — DWARF CFI / EHABI / 启发式三级容错，覆盖 AC5/AC6/GCC |

### RTT 实时传输

| 工具名 | 说明 |
|--------|------|
| `pyocd_rtt_start` | 🆕 启动 RTT 并发现通道（自动搜索 SEGGER RTT 控制块） |
| `pyocd_rtt_stop` | 🆕 停止 RTT 并释放资源 |
| `pyocd_rtt_read` | 🆕 从 RTT 上行通道读取数据（非阻塞） |
| `pyocd_rtt_write` | 🆕 向 RTT 下行通道写入数据 |
| `pyocd_rtt_status` | 🆕 查看 RTT 状态和通道信息 |

## 📋 项目配置（推荐）

在项目根目录创建 `.pyocd-debug.json`，AI 即可自动获取所有调试文件路径：

```json
{
  "target": "hc32f4a0xi",
  "firmware": "build/usart_uart_dma_Debug/usart_uart_dma.hex",
  "elf": "build/usart_uart_dma_Debug/usart_uart_dma.axf",
  "svd": "HC32F4A0PIHB.svd"
}
```

也可让 AI 自动创建：

```
AI: pyocd_project_load("/path/to/project")    → 自动扫描发现文件
AI: pyocd_project_init("/path/to/project",    → 创建配置
      target="hc32f4a0xi",
      firmware="build/xxx.hex",
      elf="build/xxx.axf",
      svd="HC32F4A0PIHB.svd")
```

> 💡 配置中的路径会自动转为项目根目录的相对路径，方便版本控制。

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

### 6. 精确栈回溯（三级容错，全工具链覆盖）

```
AI: pyocd_debug_backtrace(max_frames=16)
→ 返回:
  frames:
    [0] USART_RxCallback+0x1A          (pc=0x0800135C)
    [1] DMA_IrqHandler+0x18            (unwound via DWARF CFI)
    [2] main+0x42                      (unwound via DWARF CFI)
  method: "dwarf_cfi"                   ← AC6/GCC: .debug_frame 精确展开
  method: "ehabi"                       ← AC5: .ARM.exidx 精确展开
  method: "heuristic"                   ← 无调试信息时: 栈扫描 + BL 验证

# wait_halt 断点命中时自动附带简短 backtrace:
AI: pyocd_target_wait_halt(timeout=30)
→ { ..., "backtrace": ["UART_RxCallback", "DMA_IrqHandler+0x18", "main+0x1A"] }

# fault_analyze 崩溃时自动附带 backtrace:
AI: pyocd_debug_fault_analyze()
→ { ..., "backtrace": ["HardFault_Handler", "memcpy+0x12", "cJSON_Parse+0x8A", ...] }
```

### 🆕 地址格式灵活性

所有接受地址参数的工具（共 11 个）同时支持整数和十六进制字符串：

```python
# 两种格式等价
AI: pyocd_memory_read(address=0x20000000, size=16)
AI: pyocd_memory_read(address="0x20000000", size=16)

# 断点也支持
AI: pyocd_breakpoint_set(address="0x0800135C")

# 监视点同理
AI: pyocd_watchpoint_set(address="0x20001000", access_type="write")
```

### 🆕 组合工具

```python
# read_symbol: 一步读取变量（自动查找地址 + 读取内存 + 类型推断）
AI: pyocd_read_symbol(name="g_rxBuffer")
→ { "name": "g_rxBuffer", "address": "0x20000100", "size": 64,
     "hex_dump": "48 65 6C 6C 6F ...", "as_string": "Hello..." }

# step_out: 执行到当前函数返回
AI: pyocd_target_step_out(timeout=5.0)
→ { "status": "returned", "from_function": "UART_RxCallback",
     "returned_to": "DMA_IrqHandler+0x18" }
```

## 🏗️ 项目结构

```
pyocd-debug-mcp/
├── pyproject.toml              # 项目配置和依赖
├── src/pyocd_debug_mcp/
│   ├── server.py               # MCP Server 入口，57 个工具注册
│   ├── session_manager.py      # 会话生命周期管理（单例）
│   └── tools/
│       ├── probe.py            # 探针发现
│       ├── target.py           # 目标控制
│       ├── flash.py            # Flash 烧录 + 校验
│       ├── register.py         # 寄存器读写
│       ├── memory.py           # 内存读写
│       ├── breakpoint.py       # 断点管理（HW/SW/AUTO + Reset 恢复）
│       ├── watchpoint.py       # 监视点管理
│       ├── elf.py              # ELF 符号解析
│       ├── svd.py              # SVD 外设寄存器（含批量更新、枚举、描述）
│       ├── rtt.py              # RTT 实时传输（SEGGER RTT 通道读写）
│       ├── debug.py            # 高级调试（故障分析、栈回溯、栈检查、采样）
│       └── project.py          # 项目配置（.pyocd-debug.json 管理）
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