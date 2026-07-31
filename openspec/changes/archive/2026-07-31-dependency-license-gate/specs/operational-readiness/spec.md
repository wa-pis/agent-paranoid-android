# Operational Readiness Delta

## Added Requirements

### Requirement: Dependency License Gate

CI SHALL verify the declared license of every package installed in locked
application, optional, development, and documentation environments.

#### Scenario: Dependency license is approved

- **GIVEN** an installed dependency declares an allowlisted SPDX expression,
  legacy license value, or OSI classifier
- **WHEN** the license gate evaluates the locked environment
- **THEN** the package and resolved declaration are reported
- **AND** validation continues without an external license service

#### Scenario: Dependency license is not approved

- **GIVEN** a dependency has unknown, proprietary, or non-allowlisted metadata
- **WHEN** the license gate evaluates the locked environment
- **THEN** validation fails with the package name and declaration
- **AND** release checks cannot silently bypass the policy
