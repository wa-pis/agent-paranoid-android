# Operational Readiness Delta

## Added Requirements

### Requirement: Trino Doctor Capability Smoke

Doctor SHALL verify the required Trino capability with local safe-query
validation and client construction, not importability alone.

#### Scenario: Trino capability is healthy

- **GIVEN** the Trino extra is required and importable
- **WHEN** doctor runs without `--skip-smoke`
- **THEN** it validates a bounded allowlisted query with no sensitive fields
- **AND** it constructs and closes a DBAPI client without opening a cursor
- **AND** no credentials, external service, or repository fixture is required

#### Scenario: Trino capability fails

- **GIVEN** safe-query validation or client construction raises an exception
- **WHEN** doctor reports the failure
- **THEN** doctor exits unsuccessfully with exact extra reinstall guidance
- **AND** exception text, configuration values, and sensitive data are not exposed
