## ADDED Requirements

### Requirement: SVD batch field update
The system SHALL provide a `pyocd_svd_update_fields` tool that updates multiple bit fields of a peripheral register in a single read-modify-write operation.

#### Scenario: Update multiple GPIO fields at once
- **WHEN** user calls `pyocd_svd_update_fields` with peripheral "GPIOA", register "MODER", and fields `{"MODER0": 1, "MODER1": 2, "MODER5": 1}`
- **THEN** the system reads the register once, modifies all three fields, writes once, and returns old value, new value, readback, and per-field verification

#### Scenario: One field value out of range
- **WHEN** user provides a field value exceeding the field's bit width
- **THEN** the system returns an error identifying the invalid field and its maximum allowed value, without writing anything

### Requirement: SVD describe peripheral/register/field
The system SHALL provide a `pyocd_svd_describe` tool that returns detailed description information about a peripheral, register, or field, including access type, reset value, and enumerated values.

#### Scenario: Describe a peripheral
- **WHEN** user calls `pyocd_svd_describe` with only `peripheral` parameter
- **THEN** the system returns the peripheral's name, description, base address, and list of all register names with brief descriptions

#### Scenario: Describe a register
- **WHEN** user calls `pyocd_svd_describe` with `peripheral` and `register` parameters
- **THEN** the system returns the register's description, address, size, reset value, access type, and all field names with bit ranges

#### Scenario: Describe a field with enumerated values
- **WHEN** user calls `pyocd_svd_describe` with `peripheral`, `register`, and `field` parameters and the field has enumerated values defined in SVD
- **THEN** the system returns the field's description, bit range, width, and all enumerated values with their names, numeric values, and descriptions

### Requirement: SVD set_field supports enum names
The existing `pyocd_svd_set_field` tool SHALL accept an enumerated value name as an alternative to a numeric value, when the field has enumerated values defined in the SVD file.

#### Scenario: Set field using enum name
- **WHEN** user calls `pyocd_svd_set_field` with value "Output" for a field that has an enumeration mapping "Output" → 1
- **THEN** the system resolves "Output" to numeric value 1 and performs the standard read-modify-write operation

#### Scenario: Enum name not found
- **WHEN** user calls `pyocd_svd_set_field` with a string value that doesn't match any enumerated value
- **THEN** the system returns an error listing all available enum names for that field

#### Scenario: Numeric value still works
- **WHEN** user calls `pyocd_svd_set_field` with a numeric value (integer)
- **THEN** the system behaves exactly as before (backward compatible)
