## ADDED Requirements

### Requirement: Flash content verification
The system SHALL provide a `pyocd_flash_verify` tool that verifies the target's Flash content matches a source firmware file. The tool SHALL support .hex, .bin, and .elf file formats.

#### Scenario: Verify matching firmware
- **WHEN** user calls `pyocd_flash_verify` with the same file that was just programmed
- **THEN** the system reads Flash contents, compares segment by segment, and returns `verified: true` with total bytes checked

#### Scenario: Verify mismatched firmware
- **WHEN** user calls `pyocd_flash_verify` with a file different from what's on Flash
- **THEN** the system returns `verified: false` with first mismatch address, expected byte, and actual byte

#### Scenario: Progress notification for large files
- **WHEN** the firmware file is larger than 64KB
- **THEN** the system sends progress notifications during verification to prevent client timeout

#### Scenario: Verify .bin file with base address
- **WHEN** user calls `pyocd_flash_verify` with a .bin file and `base_address` parameter
- **THEN** the system uses the specified base address as the start of comparison (default: Flash start address)
