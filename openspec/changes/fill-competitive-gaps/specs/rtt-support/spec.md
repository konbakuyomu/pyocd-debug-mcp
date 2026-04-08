## ADDED Requirements

### Requirement: RTT channel start
The system SHALL provide a `pyocd_rtt_start` tool that starts RTT on the target, searching for the SEGGER RTT control block in RAM. The target MUST be running (not halted) when RTT is started. The tool SHALL accept optional parameters for control block address and search range.

#### Scenario: Start RTT with auto-discovery
- **WHEN** user calls `pyocd_rtt_start` without specifying a control block address
- **THEN** the system searches the target's entire RAM for the SEGGER RTT control block and returns the found address, number of up/down channels, and their buffer sizes

#### Scenario: Start RTT with explicit address
- **WHEN** user calls `pyocd_rtt_start` with `control_block_address` parameter
- **THEN** the system uses the provided address directly without searching

#### Scenario: RTT start fails when target halted
- **WHEN** user calls `pyocd_rtt_start` while target is halted
- **THEN** the system returns an error message suggesting to resume the target first

### Requirement: RTT channel stop
The system SHALL provide a `pyocd_rtt_stop` tool that stops RTT and releases associated resources.

#### Scenario: Stop active RTT
- **WHEN** user calls `pyocd_rtt_stop` while RTT is active
- **THEN** RTT is stopped and status shows "stopped"

#### Scenario: Stop when not started
- **WHEN** user calls `pyocd_rtt_stop` when RTT is not active
- **THEN** the system returns a warning "RTT not active" without error

### Requirement: RTT read from up channel
The system SHALL provide a `pyocd_rtt_read` tool that reads data from an RTT up channel (target→host). The read MUST be non-blocking and return whatever data is available in the buffer.

#### Scenario: Read available data
- **WHEN** user calls `pyocd_rtt_read` on channel 0 and data is available
- **THEN** the system returns the data as UTF-8 text with byte count and channel number

#### Scenario: Read empty buffer
- **WHEN** user calls `pyocd_rtt_read` on channel 0 and no data is available
- **THEN** the system returns empty data with byte count 0

#### Scenario: Read with encoding option
- **WHEN** user calls `pyocd_rtt_read` with `encoding: "hex"`
- **THEN** the system returns data as hex-encoded string instead of UTF-8

### Requirement: RTT write to down channel
The system SHALL provide a `pyocd_rtt_write` tool that writes data to an RTT down channel (host→target) for bidirectional communication.

#### Scenario: Write text data
- **WHEN** user calls `pyocd_rtt_write` with text data on channel 0
- **THEN** the system writes the UTF-8 encoded data to the specified down channel and returns bytes written

#### Scenario: Write to invalid channel
- **WHEN** user calls `pyocd_rtt_write` on a channel index that doesn't exist
- **THEN** the system returns an error with available channel indices

### Requirement: RTT status query
The system SHALL provide a `pyocd_rtt_status` tool that returns the current RTT state including active/inactive, control block address, and channel information.

#### Scenario: Query status when active
- **WHEN** user calls `pyocd_rtt_status` while RTT is active
- **THEN** the system returns status "active", control block address, and list of all up/down channels with their names and buffer sizes

#### Scenario: Query status when inactive
- **WHEN** user calls `pyocd_rtt_status` while RTT is not started
- **THEN** the system returns status "inactive"
