## Context

pyocd-debug-mcp 当前有 47 个工具，通过 pyOCD + CMSIS-DAP 探针实现嵌入式 MCU 调试。竞品横评显示：
- dbgprobe-mcp-server（41 工具）拥有 RTT 支持、自动 ELF、断点恢复、软件断点
- embedded-debugger-mcp（22 工具）拥有 RTT 和 Flash 验证
- 我们在诊断分析领域（故障分析、栈回溯、Watchpoint）远超竞品，但日常效率功能有差距

当前架构：
- `server.py` — FastMCP 工具注册层（~850 行）
- `session_manager.py` — 单例会话管理（连接/断连/ELF/SVD 生命周期）
- `tools/` — 13 个模块（probe, target, register, memory, breakpoint, flash, elf, svd, watchpoint, debug, unwinder）
- `breakpoint.py` 使用 `_active_breakpoints: dict[int, dict]` 模块级变量追踪断点

## Goals / Non-Goals

**Goals:**
- 补齐 4 个高优差距：自动 ELF 附加、断点恢复、软件断点、RTT
- 补齐 4 个中优差距：SVD 批量更新/描述/枚举、Flash 验证
- 保持向后兼容（所有现有工具 API 不变）
- 全部新增功能通过 HC32F4A0 + DAPLink 实物回归测试
- 新增工具总数预计 8-10 个，工具总数达到 55-57 个

**Non-Goals:**
- 插件系统（复杂度高，收益不够明确）
- GDB 直通（与 pyOCD 原生 API 冲突，属于另一种范式）
- 串口通信（应作为独立 MCP 实现）
- RISC-V 支持（pyOCD 主要面向 ARM Cortex-M）
- Session-less 烧录（便利性收益低，增加复杂度）

## Decisions

### D1: RTT 实现方式 — 使用 pyOCD 原生 `target.rtt` API

**选择**：直接调用 `pyOCD.core.soc_target.SoCTarget` 的 RTT 相关方法。

**理由**：
- pyOCD 从 v0.36+ 内置 RTT 支持，通过 CMSIS-DAP 的 SWD 接口实现
- 不需要额外的 GDB server 或 telnet 端口
- API：`target.rtt_start()`, `target.rtt_stop()`, `target.rtt_read()`, `target.rtt_write()`

**备选方案**：
- ❌ J-Link RTT Viewer 进程（需要 J-Link 探针，不通用）
- ❌ OpenOCD RTT（需要 OpenOCD 后台进程）

**风险**：pyOCD RTT 可能在某些探针上不稳定。需要 E2E 测试验证。

### D2: 软件断点 — 在 `set_breakpoint` 增加 `bp_type` 可选参数

**选择**：`bp_type` 参数：`"hw"`（默认，硬件断点）、`"sw"`（软件断点）、`"auto"`（自动选择）。

**理由**：
- pyOCD `target.set_breakpoint(addr, type)` 已支持 `Target.BreakpointType.HW` 和 `Target.BreakpointType.SW`
- 默认 `"hw"` 保持向后兼容
- `"auto"` 模式：先尝试 HW，HW 用完后自动切换 SW

**备选方案**：
- ❌ 全部改为 auto（可能引发 Flash 写入风险，SW BP 需要写入 Flash 区域的 BKPT 指令）

### D3: 断点恢复 — 在 `session_manager` 层实现，`target_reset` 后自动回调

**选择**：
1. `session_manager` 新增 `_breakpoint_registry: list[dict]` 追踪所有活跃断点的参数
2. `target_reset` 完成后调用 `_restore_breakpoints()` 重新设置所有断点
3. 现有 `breakpoint.py` 的 `_active_breakpoints` 同步更新

**理由**：
- 将持久化逻辑放在 session 层，breakpoint 模块保持简洁
- Reset 清空 FPB 硬件，但软件层面的注册表不受影响

**备选方案**：
- ❌ 在 breakpoint.py 层做恢复（需要跨模块调用 target_reset，耦合度高）

### D4: 自动 ELF 附加 — 在 `flash_program` 内部检测 `.elf` 后缀

**选择**：
- `flash.program()` 检测文件扩展名为 `.elf` 时，烧录后自动调用 `session_mgr.attach_elf(file_path)`
- 返回值新增 `elf_auto_attached: true` 字段

**理由**：
- 最小变更，只改 `flash.py` 的 `program()` 函数
- 向后兼容（非 .elf 文件行为完全不变）

### D5: SVD 增强 — 3 个新功能在 `svd.py` 内新增函数

- **`update_fields`**：接受 `{field_name: value}` 字典，一次 read32 → 修改所有字段 → 一次 write32
- **`describe`**：返回外设/寄存器/字段的完整描述文本、访问类型、枚举值
- **`set_field` 枚举增强**：检查 `SVDEnumeratedValue`，接受枚举名称或数值

### D6: Flash 验证 — 读取 Flash 并与源文件逐段比较

**选择**：
- 新增 `flash.verify(file_path)` 函数
- 解析 .hex/.bin/.elf 获取数据段，逐段读取 Flash 对比
- 使用 pyOCD 的 `target.read_memory_block8()` 批量读取

**风险**：大固件验证耗时较长（需要进度通知）。

## Risks / Trade-offs

| 风险 | 缓解措施 |
|------|---------|
| pyOCD RTT API 不稳定或某些探针不支持 | E2E 测试验证；RTT 工具标注为 experimental；错误消息引导用户检查探针 |
| 软件断点写入 Flash 区域可能导致 Flash 损耗 | 默认使用 HW；SW BP 的描述中明确警告 Flash 写入 |
| 断点恢复在 reset 类型为 SW_SYSRESET 时可能失效 | 恢复逻辑统一在 reset 完成后执行，不依赖 reset 类型 |
| SVD 枚举名在不同 SVD 文件中格式不一致 | case-insensitive 匹配，回退到数值模式 |
| Flash verify 大固件耗时长 | 使用 ctx.report_progress 报告进度 |
