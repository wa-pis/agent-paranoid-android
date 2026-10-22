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

### Requirement: Finite CSV Numeric Evidence

CSV numeric inference SHALL admit only finite parsed floating-point values.
The same parser SHALL be used by standalone and streaming profiling routes.

#### Scenario: A CSV numeric column contains a nonfinite or overflowing value
- **GIVEN** a finite numeric value mixed with NaN, infinity or overflowing exponent text
- **WHEN** a CSV profiling route infers the column and its statistics
- **THEN** the column is not represented as a complete numeric distribution
- **AND** nonfinite numeric extrema and percentiles are not published
- **AND** existing sensitivity checks still inspect every admitted value

#### Scenario: A folder has a cache from before finite numeric parsing
- **WHEN** profiling is requested with cache reuse
- **THEN** the older cache format is rejected and the source is profiled again
- **AND** previously approved saved profiles are not silently rewritten
