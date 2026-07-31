# Public Contracts Delta

## Added Requirements

### Requirement: Runtime And Integration Support Policy

The project SHALL document the release-gated Python versions, optional extras,
and provider-adapter maturity independently from internal implementation
details.

#### Scenario: A user selects an installation profile

- **GIVEN** a user needs the base package or an optional capability
- **WHEN** the user consults the support policy
- **THEN** each extra's capability and release gate are identifiable
- **AND** the `all` extra is not presented as the normal user installation

#### Scenario: A maintainer changes runtime support

- **GIVEN** a proposed change drops a Python version, removes an extra, or
  changes a supported provider adapter
- **WHEN** the compatibility impact is reviewed
- **THEN** the change is classified as breaking
- **AND** notice, migration, and security-exception rules are explicit

#### Scenario: A provider adapter is evaluated

- **GIVEN** a provider-specific adapter before the 1.0 baseline
- **WHEN** its support status is reviewed
- **THEN** it is distinguished from the versioned provider-neutral contract
- **AND** metadata-only, validation, dependency, fake-test, and redaction
  requirements remain mandatory
