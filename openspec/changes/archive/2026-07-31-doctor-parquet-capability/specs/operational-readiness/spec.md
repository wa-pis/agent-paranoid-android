# Operational Readiness Delta

## Added Requirements

### Requirement: Parquet Doctor Capability Smoke

Doctor SHALL verify the required Parquet capability with local artifact
generation and read-back, not importability alone.

#### Scenario: Parquet capability is healthy

- **GIVEN** the Parquet extra is required and importable
- **WHEN** doctor runs without `--skip-smoke`
- **THEN** it generates and reads a temporary two-entity Parquet bundle
- **AND** row counts, output format, and manifest safety flags are valid
- **AND** no external service or repository fixture is required

#### Scenario: Parquet capability fails

- **GIVEN** Parquet generation or read-back raises an exception
- **WHEN** doctor reports the failure
- **THEN** doctor exits unsuccessfully with exact extra reinstall guidance
- **AND** exception text, temporary paths, and sensitive values are not exposed
