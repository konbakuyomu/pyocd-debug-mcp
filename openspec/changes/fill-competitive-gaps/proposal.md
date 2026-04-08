## Why

竞品横评发现 pyocd-debug-mcp 在诊断分析领域（故障分析、栈回溯、Watchpoint）远超所有竞品，但在 **日常调试自动化** 和 **开发体验** 上存在 4 个高优差距和 4 个中优差距。dbgprobe-mcp-server（41 工具）和 embedded-debugger-mcp（22 工具）均已实现 RTT 支持、自动 ELF 附加、断点恢复等关键功能。补齐这些差距后，pyocd-debug-mcp 将成为功能最全面的嵌入式调试 MCP。

## What Changes

### 高优先级（直接影响调试效率）

- **烧录自动附加 ELF** — 当烧录 `.elf` 文件时，自动调用 `elf_attach` 加载符号表，省去手动步骤
- **Reset 后自动恢复断点** — `session_manager` 记录已设置的断点列表，`target_reset` 后自动重新设置所有断点
- **软件断点支持** — 在 `breakpoint_set` 中增加 `bp_type` 参数（"hw"/"sw"/"auto"），突破硬件断点 6-8 个的数量限制
- **RTT (Real-Time Transfer) 支持** — 新增 5 个 RTT 工具，支持目标运行时的日志读取和双向数据通信

### 中优先级（SVD 增强 + Flash 验证）

- **SVD 批量字段更新** — 新增 `pyocd_svd_update_fields` 工具，一次 RMW 操作更新多个字段
- **SVD 描述查询** — 新增 `pyocd_svd_describe` 工具，查看外设/寄存器/字段的详细描述和枚举值
- **SVD 枚举名支持** — `pyocd_svd_set_field` 支持传入枚举名称（如 "Output"）而非原始数字
- **Flash 烧录后验证** — 新增 `pyocd_flash_verify` 工具，校验 Flash 内容与源文件一致

### 回归测试

- 使用 HC32F4A0 + DAPLink 实物对所有新增/修改的工具进行端到端验证
- 确保原有 47 个工具功能不受影响

## Capabilities

### New Capabilities
- `rtt-support`: RTT 实时传输通道管理（start/stop/read/write/status），用于目标运行时日志和通信
- `flash-verify`: Flash 烧录后校验功能，确保写入数据完整性
- `svd-enhanced`: SVD 批量字段更新、描述查询、枚举名支持

### Modified Capabilities
- `breakpoint-management`: 新增软件断点类型支持（bp_type 参数），扩展断点容量
- `flash-programming`: 烧录 .elf 文件时自动附加 ELF 符号表
- `session-lifecycle`: Reset 后自动恢复断点列表，断开时清理断点追踪状态

## Impact

### 代码变更范围
- `tools/breakpoint.py` — 新增 `bp_type` 参数，调整 `set_breakpoint` API
- `tools/flash.py` — 新增 `verify` 函数，修改 `program` 支持自动 ELF 附加
- `tools/svd.py` — 新增 `update_fields`, `describe` 函数，增强 `set_field`
- `tools/rtt.py` — **新建文件**，全部 RTT 工具实现
- `session_manager.py` — 断点恢复机制，reset 后回调
- `server.py` — 注册所有新工具（预计新增 8-10 个工具定义）

### API 变更
- `pyocd_breakpoint_set` — 新增可选参数 `bp_type`（默认 "hw"，向后兼容）
- `pyocd_flash_program` — 返回值新增 `elf_auto_attached` 字段（向后兼容）
- `pyocd_svd_set_field` — 新增可选参数接受枚举名（向后兼容）

### 依赖
- 无新增外部依赖。pyOCD 原生支持 RTT（`target.rtt` 模块）和软件断点。
- cmsis-svd 已提供枚举信息（`SVDEnumeratedValue`）。
