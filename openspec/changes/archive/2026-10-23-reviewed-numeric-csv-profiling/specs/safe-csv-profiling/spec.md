## ADDED Requirements

### Requirement: Reviewed CSV Numeric Replacement

CSV profiling SHALL retain phone sensitivity, masking and source-free metadata
when numeric text resembles a phone. An optional typed `numeric_storage_type`
SHALL describe integer or finite floating storage only when every inspected
non-null value satisfies it; no majority vote or source extrema SHALL authorize
a synthetic numeric replacement.

`infer-spec --decimal-fields` SHALL accept independently authored synthetic
`numeric_measure` DECIMAL ranges for eligible CSV fields. Protected names,
identifiers, primary-key candidates and relationship endpoints SHALL reject.
The declaration SHALL match the field name and use a validated finite bounded
`decimal_range`; it SHALL NOT alter the source profile or authorize copied rows.
Declared SQL/Parquet DECIMAL precision/scale checks SHALL remain unchanged.

#### Scenario: A reviewed measure resembles a phone
- **GIVEN** numeric phone-like text with complete finite storage evidence
- **WHEN** a matching reviewed synthetic numeric_measure range is supplied
- **THEN** the generated spec uses that range and the source profile stays sensitive
- **AND** the profile, provider request and diagnostics contain no source numeric values

#### Scenario: Late sensitive or malformed content
- **WHEN** an otherwise numeric column includes a formatted phone, secret, nonfinite or nonnumeric outlier
- **THEN** incomplete numeric storage evidence does not permit replacement
- **AND** sensitive names and identifiers cannot be overridden by a declaration

#### Scenario: Old ambiguous profile and saved approval
- **WHEN** an old ambiguous profile lacks numeric storage evidence
- **THEN** replacement requires new profiling and folder cache formats before 8 are recomputed
- **AND** changed evidence or synthetic bounds changes the relevant fingerprint and requires new review
- **AND** absent evidence remains omitted so unaffected old profile fingerprints are stable

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
