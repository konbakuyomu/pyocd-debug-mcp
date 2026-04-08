## ADDED Requirements

### Requirement: Breakpoint auto-restore after target reset
When the target is reset via `pyocd_target_reset`, the system SHALL automatically re-arm all previously set breakpoints that were active before the reset.

#### Scenario: Reset preserves breakpoints
- **WHEN** user has 3 breakpoints set and calls `pyocd_target_reset`
- **THEN** after reset completes, all 3 breakpoints are re-armed at their original addresses, and the response includes `breakpoints_restored: 3`

#### Scenario: Reset with partial restore failure
- **WHEN** user has breakpoints set and one fails to re-arm after reset (e.g., address no longer in Flash)
- **THEN** the reset succeeds, successfully restored breakpoints are reported, and failed ones are listed with error details

#### Scenario: Breakpoint registry survives reset
- **WHEN** `pyocd_breakpoint_list` is called after a target reset
- **THEN** the list shows all originally set breakpoints (including type and symbol info)

#### Scenario: Disconnect clears registry
- **WHEN** user calls `pyocd_session_disconnect`
- **THEN** the breakpoint registry is fully cleared (no stale state on next connect)
