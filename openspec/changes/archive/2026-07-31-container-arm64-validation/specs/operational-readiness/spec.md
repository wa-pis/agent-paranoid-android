# Operational Readiness Delta

## Added Requirements

### Requirement: ARM64 Container Validation

CI SHALL build and execute every published container target for Linux ARM64
before multi-platform publication.

#### Scenario: ARM64 target is healthy

- **GIVEN** a CLI, generator MCP, or Trino MCP container target
- **WHEN** pull-request CI builds and loads it for Linux ARM64
- **THEN** the image reports the ARM64 architecture
- **AND** the existing non-root, read-only, no-capability health contract passes
- **AND** no production service or credential is required

#### Scenario: ARM64 target regresses

- **GIVEN** a target cannot build or execute safely on ARM64
- **WHEN** validation runs through registered emulation
- **THEN** the target-specific job fails before merge
- **AND** tagged multi-platform publication depends on the failed validation
