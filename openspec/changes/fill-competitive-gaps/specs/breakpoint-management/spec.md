## ADDED Requirements

### Requirement: Software breakpoint type support
The `pyocd_breakpoint_set` tool SHALL accept an optional `bp_type` parameter to specify the breakpoint type: `"hw"` (hardware), `"sw"` (software), or `"auto"` (automatic selection).

#### Scenario: Set hardware breakpoint (default)
- **WHEN** user calls `pyocd_breakpoint_set` without `bp_type` parameter
- **THEN** the system sets a hardware breakpoint (same as current behavior, backward compatible)

#### Scenario: Set software breakpoint
- **WHEN** user calls `pyocd_breakpoint_set` with `bp_type: "sw"`
- **THEN** the system sets a software breakpoint using BKPT instruction patch, and the response includes `type: "sw"`

#### Scenario: Auto mode with available HW slots
- **WHEN** user calls `pyocd_breakpoint_set` with `bp_type: "auto"` and hardware breakpoint slots are available
- **THEN** the system uses a hardware breakpoint

#### Scenario: Auto mode with HW slots exhausted
- **WHEN** user calls `pyocd_breakpoint_set` with `bp_type: "auto"` and all hardware breakpoint slots are in use
- **THEN** the system falls back to a software breakpoint and the response includes `type: "sw"` with a note about HW slot exhaustion

#### Scenario: Breakpoint type shown in listing
- **WHEN** user calls `pyocd_breakpoint_list` with mixed hw/sw breakpoints active
- **THEN** each breakpoint entry includes a `type` field ("hw" or "sw")
