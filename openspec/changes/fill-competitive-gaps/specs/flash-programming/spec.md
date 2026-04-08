## ADDED Requirements

### Requirement: Auto-attach ELF on flash programming
When the `pyocd_flash_program` tool is called with a `.elf` file, the system SHALL automatically attach the ELF file for symbol resolution after successful programming.

#### Scenario: Flash .elf file auto-attaches symbols
- **WHEN** user calls `pyocd_flash_program` with `file_path` ending in `.elf`
- **THEN** the system programs the Flash, then automatically calls ELF attach, and returns `elf_auto_attached: true` in the response

#### Scenario: Flash .hex file does not auto-attach
- **WHEN** user calls `pyocd_flash_program` with `file_path` ending in `.hex`
- **THEN** the system programs the Flash normally without ELF attachment (backward compatible)

#### Scenario: Auto-attach fails gracefully
- **WHEN** user calls `pyocd_flash_program` with a `.elf` file that has corrupt/missing debug info
- **THEN** the Flash programming succeeds but ELF attachment is skipped with a warning `elf_auto_attached: false` and `elf_attach_error` in the response
