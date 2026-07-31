# Operational Readiness Delta

## Added Requirements

### Requirement: Supported Python Wheel Matrix

CI SHALL build and install the base wheel on every supported Python minor
version without replacing the full optional-profile wheel gate.

#### Scenario: Supported wheel is healthy

- **GIVEN** a supported Python version from 3.11 through 3.14
- **WHEN** CI builds and installs the wheel into an isolated environment
- **THEN** installed identity, metadata, dependencies, and size are valid
- **AND** base doctor completes using only local temporary artifacts

#### Scenario: Compatibility regression occurs

- **GIVEN** a wheel cannot build, install, or run on a supported Python version
- **WHEN** the compatibility matrix executes
- **THEN** that interpreter-specific job fails before release
- **AND** the existing full optional-profile wheel check remains independent
