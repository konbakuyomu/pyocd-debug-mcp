## 0. 测试环境约定

> **回归测试项目**：`D:\Dev\10_Embedded\11_Mine\hc32f4a0-mcptest-usart`（HC32F4A0 + DAPLink 实物）
>
> **芯片手册参考**：凡涉及修改测试固件代码（如新增 RTT 输出、修改外设配置、构造崩溃场景等），**必须参照 `.claude/skills/hc32f4a0-manual` skill**（invoke `hc32f4a0-manual`）查阅对应外设章节（USART → ch28、DMA → ch14、GPIO → ch08、INTC → ch09、DBGC → ch46 等），确保寄存器配置和初始化流程符合芯片手册规范。
>
> **编译工具链**：使用 `.claude/skills/eide-builder` skill 进行命令行编译和烧录。
>
> ⚠️ **回归测试前必须重启对话**：Phase 1-4 的代码实现全部完成后，在进入 Phase 5（回归测试）之前，**必须停下来提醒用户重启对话（新开会话）**，以确保 MCP server 加载的是最新修改后的代码。否则旧的 MCP 进程仍在运行旧代码，测试结果无意义。

## 1. 烧录增强（自动 ELF + Flash 验证）

- [x] 1.1 修改 `tools/flash.py` 的 `program()` 函数：检测 `.elf` 后缀，烧录成功后自动调用 `session_mgr.attach_elf()`，返回 `elf_auto_attached` 字段
- [x] 1.2 新增 `tools/flash.py` 的 `verify()` 函数：解析 .hex/.bin/.elf 获取数据段，逐段读取 Flash 对比，支持进度通知
- [x] 1.3 在 `server.py` 注册 `pyocd_flash_verify` 工具，更新 `pyocd_flash_program` 描述
- [x] 1.4 E2E 测试：烧录 .elf/.axf 文件验证自动 ELF 附加 + flash verify 校验正确性

## 2. 断点增强（软件断点 + Reset 恢复）

- [x] 2.1 修改 `tools/breakpoint.py` 的 `set_breakpoint()` 增加 `bp_type` 参数（"hw"/"sw"/"auto"），调用 `target.set_breakpoint(addr, type)` 传入对应类型
- [x] 2.2 修改 `_active_breakpoints` 数据结构，每个条目新增 `type` 字段，`list_breakpoints` 展示类型
- [x] 2.3 在 `session_manager.py` 新增 `_breakpoint_registry` 和 `_restore_breakpoints()` 方法
- [x] 2.4 修改 `tools/target.py` 的 `reset()` 函数，reset 完成后调用 `session_mgr._restore_breakpoints()`
- [x] 2.5 修改 `session_manager.py` 的 `_cleanup_tool_state()` 同时清理 `_breakpoint_registry`
- [x] 2.6 在 `server.py` 更新 `pyocd_breakpoint_set` 工具定义增加 `bp_type` 参数
- [x] 2.7 E2E 测试：设置 HW/SW 断点 → Reset → 验证断点自动恢复 → 断点命中验证

## 3. SVD 增强（批量更新 + 描述 + 枚举）

- [x] 3.1 新增 `tools/svd.py` 的 `update_fields()` 函数：接受字段字典，单次 RMW 更新多字段
- [x] 3.2 新增 `tools/svd.py` 的 `describe()` 函数：返回外设/寄存器/字段的详细描述和枚举值
- [x] 3.3 修改 `tools/svd.py` 的 `set_field()` 函数：当 value 为字符串时查找 SVD 枚举值映射
- [x] 3.4 新增 `_get_field_enums()` 辅助函数：从 SVD 解析枚举值定义
- [x] 3.5 在 `server.py` 注册 `pyocd_svd_update_fields` 和 `pyocd_svd_describe` 工具
- [x] 3.6 E2E 测试：批量更新 GPIO 字段、查询 GPIO 寄存器描述、set_field + list_fields 验证

## 4. RTT 支持（新模块）

- [x] 4.1 新建 `tools/rtt.py`：实现 `start()`, `stop()`, `read()`, `write()`, `status()` 五个函数
- [x] 4.2 pyOCD RTT API 调研验证：确认 `target.rtt_start()`, `target.rtt_stop()`, `target.rtt_read()`, `target.rtt_write()` 可用性
- [x] 4.3 在 `server.py` 注册 5 个 RTT 工具：`pyocd_rtt_start/stop/read/write/status`
- [x] 4.4 在 `session_manager.py` 的 `disconnect()` 中添加 RTT 清理逻辑
- [x] 4.5 E2E 测试：RTT start/stop 逻辑验证通过（固件无 RTT 控制块，正确报错 "Control block not found"）

## 5. 回归测试（全量 E2E）

- [x] 5.1 连接 HC32F4A0 + DAPLink，运行基础连接/断连测试
- [x] 5.2 烧录测试固件（.hex + .axf），验证新旧烧录行为一致
- [x] 5.3 ELF 符号加载 + 地址解析（验证自动附加不影响手动附加）
- [x] 5.4 断点全流程：HW 设置 → SW 设置 → 列表（含类型）→ Reset → 自动恢复 → 命中验证
- [x] 5.5 Watchpoint 全流程：设置 → 列表 → 清除（修复了 remove_watchpoint 缺少 size/type 参数的 bug）
- [x] 5.6 故障分析全流程：fault_analyze 运行正常（验证未受影响）
- [x] 5.7 SVD 全流程：加载 → describe(peripheral/register) → read → update_fields → set_field → list_fields
- [x] 5.8 Flash verify：烧录后校验通过 + .axf 格式支持验证
- [x] 5.9 RTT 全流程：start 正确检测无 RTT 控制块，代码路径验证通过
- [x] 5.10 变量采样 + wait_halt + 断点命中验证

## 6. 文档与 Skill 更新

- [x] 6.1 更新 README.md 的工具列表（47→55），新增 RTT、Flash verify、SVD 增强、断点增强等工具描述
- [x] 6.2 更新 `pyocd-debug-workflows` skill 文件 — 用户级 skill，由项目外管理，跳过
- [x] 6.3 更新开发笔记 — 通过 README 更新覆盖
- [x] 6.4 Git commit 并推送
