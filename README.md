# pyocd-debug-mcp

> **让 AI 全自动进行嵌入式单片机仿真调试的 MCP Server**

通过 [pyOCD](https://pyocd.io/) + CMSIS-DAP 探针，为 Claude / GitHub Copilot 等 AI 工具提供 **41 个调试工具**，涵盖从连接探针、烧录固件、打断点、读寄存器到 HardFault 故障分析的完整调试流程。

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

## 🛠️ 工具列表（41 个）

### 探针 & 会话

| 工具名 | 说明 |
|--------|------|
| `pyocd.probe.list` | 列出所有已连接的 CMSIS-DAP 调试探针 |
| `pyocd.probe.info` | 获取指定探针详细信息 |
| `pyocd.session.connect` | 连接探针并打开调试会话 |
| `pyocd.session.disconnect` | 断开调试会话，释放探针 |
| `pyocd.session.status` | 查看当前会话状态 |

### 烧录

| 工具名 | 说明 |
|--------|------|
| `pyocd.flash.program` | 烧录固件（.hex / .bin / .elf） |
| `pyocd.flash.erase` | 擦除 Flash |

### 目标控制

| 工具名 | 说明 |
|--------|------|
| `pyocd.target.halt` | 暂停 CPU |
| `pyocd.target.resume` | 恢复运行 |
| `pyocd.target.step` | 单步执行 |
| `pyocd.target.reset` | 复位 MCU |
| `pyocd.target.status` | 获取目标状态（运行/停止）及关键寄存器 |
| `pyocd.target.wait_halt` | ⏳ **等待目标停止**（断点命中/监视点触发） |
| `pyocd.target.list_supported` | 列出 pyOCD 支持的所有 MCU（206+） |

### 寄存器 & 内存

| 工具名 | 说明 |
|--------|------|
| `pyocd.register.read` | 读取 CPU 寄存器 |
| `pyocd.register.write` | 写入 CPU 寄存器 |
| `pyocd.register.read_all` | 读取全部寄存器（含 FPU） |
| `pyocd.memory.read` | 读内存 |
| `pyocd.memory.write` | 写内存（带 readback 验证） |
| `pyocd.memory.write_block` | 块写入 |
| `pyocd.memory.dump` | Hex dump 格式输出 |

### 断点 & 监视点

| 工具名 | 说明 |
|--------|------|
| `pyocd.breakpoint.set` | 设置硬件断点（地址或符号名） |
| `pyocd.breakpoint.clear` | 清除断点 |
| `pyocd.breakpoint.clear_all` | 清除所有断点 |
| `pyocd.breakpoint.list` | 列出当前断点 |
| `pyocd.watchpoint.set` | 设置数据监视点（读/写/读写触发） |
| `pyocd.watchpoint.clear` | 清除监视点 |
| `pyocd.watchpoint.clear_all` | 清除所有监视点 |
| `pyocd.watchpoint.list` | 列出当前监视点 |

### ELF 符号

| 工具名 | 说明 |
|--------|------|
| `pyocd.elf.attach` | 加载 ELF 文件用于符号解析 |
| `pyocd.elf.lookup` | 按名称查找符号地址 |
| `pyocd.elf.symbols` | 列出 ELF 中的符号（函数/变量） |
| `pyocd.elf.info` | 获取 ELF 文件信息 |

### SVD 外设寄存器

| 工具名 | 说明 |
|--------|------|
| `pyocd.svd.attach` | 加载 SVD 文件 |
| `pyocd.svd.list_peripherals` | 列出所有外设 |
| `pyocd.svd.list_registers` | 列出外设的寄存器 |
| `pyocd.svd.read` | 按名称读外设寄存器（含位域解析） |
| `pyocd.svd.write` | 按名称写外设寄存器 |

### 高级调试

| 工具名 | 说明 |
|--------|------|
| `pyocd.debug.fault_analyze` | 💥 分析 HardFault 崩溃（SCB 寄存器 + 异常栈帧 + EXC_RETURN） |
| `pyocd.debug.stack_overflow_check` | 📏 检查线程栈溢出（RT-Thread / FreeRTOS） |
| `pyocd.debug.sample_variable` | 📊 周期性采样变量（如每 0.5s 采样 200 次） |

## 🚀 典型调试流程

以下是 AI 使用此 MCP Server 进行调试的典型对话流程：

### 1. 连接 → 烧录 → 运行到 main

```
AI: pyocd.probe.list                           → 发现探针
AI: pyocd.session.connect("hc32f460xe")        → 连接
AI: pyocd.flash.program("firmware.hex")        → 烧录
AI: pyocd.elf.attach("firmware.elf")           → 加载符号
AI: pyocd.breakpoint.set(symbol="main")        → 在 main 打断点
AI: pyocd.target.reset(halt=true)              → 复位并停止
AI: pyocd.target.wait_halt(timeout=10)         → 等待命中 main
```

### 2. 串口数据调试（等待断点）

```
AI: pyocd.breakpoint.set(symbol="UART_RxCallback")
AI: pyocd.target.wait_halt(timeout=60)         ← 等待数据到来
    ... 60s 内数据到达，断点命中 ...
AI: pyocd.memory.dump(rx_buffer_addr, 64)      → 查看接收缓冲区
AI: pyocd.register.read_all()                  → 查看寄存器现场
```

### 3. 周期性变量监控

```
AI: pyocd.debug.sample_variable(
      address=0x20001000,   # 全局变量地址
      interval=0.5,          # 每 0.5s
      count=200              # 共 200 次 = 100s
    )
→ 返回所有采样值 + min/max/变化统计
```

### 4. HardFault 崩溃分析

```
AI: pyocd.debug.fault_analyze()
→ 返回:
  - fault_type: "BusFault"
  - fault_address: "0x40012400"
  - active_faults: [PRECISERR, BFARVALID]
  - exception_frame: {PC_fault, LR_saved, R0-R3, ...}
  - exc_return: {stack_used: "PSP", fpu_context: ...}
```

### 5. 野指针/数组越界追踪

```
AI: pyocd.watchpoint.set(
      address=0x20002000,    # 数组末尾地址
      size=4,
      access_type="write"    # 监控越界写入
    )
AI: pyocd.target.wait_halt(timeout=30)
    ... 越界写入发生，DWT 触发停止 ...
AI: pyocd.target.status()                      → 查看 PC 定位到写入指令
```

## 🏗️ 项目结构

```
pyocd-debug-mcp/
├── pyproject.toml              # 项目配置和依赖
├── src/pyocd_debug_mcp/
│   ├── server.py               # MCP Server 入口，41 个工具注册
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
│       └── debug.py            # 高级调试（故障分析、栈检查、采样）
└── tests/
```

## ⚙️ 支持的硬件

- **调试探针**: 所有 CMSIS-DAP 兼容探针（DAPLink、STLINK via pyOCD、J-Link via pyOCD）
- **MCU**: pyOCD 支持的 206+ 种芯片，包括：
  - **HDSC/XHSC**: HC32F460、HC32F4A0 等
  - **STMicroelectronics**: STM32F0/F1/F2/F3/F4/F7/H7/L0/L4/G0/G4 等
  - **Nordic**: nRF52832、nRF52840、nRF9160 等
  - **NXP**: LPC、Kinetis、i.MX RT 等
  - 更多: `pyocd.target.list_supported` 查看完整列表

## 📄 License

MIT