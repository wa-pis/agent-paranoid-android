## ADDED Requirements

### Requirement: Reviewed Numeric Measure Profiling

A numeric-measure declaration SHALL be field-scoped and enforced by deterministic
code. It SHALL NOT authorize raw sensitive values or automatic declassification.

#### Scenario: A numeric measure resembles a phone
- **GIVEN** a newly constructed numeric measure and a reviewed declaration
- **WHEN** either CSV profiling path processes it
- **THEN** both paths agree on the permitted numeric type and safe metadata
- **AND** no source row is used as generated output

#### Scenario: A numeric sample contains a rare secret
- **WHEN** a sample contains a recognizable secret or protected identifier
- **THEN** majority numeric values do not suppress the privacy gate
- **AND** the value is absent from diagnostics, artifacts and provider requests
