# Operational Readiness Delta

## Added Requirements

### Requirement: Auditable Security Review Disposition

Before operational readiness is declared, maintainers SHALL record the result
and disposition of dependency, license, source, secret, container, and
supply-chain checks against an identified commit.

#### Scenario: Release-blocking finding exists

- **GIVEN** a Critical or High runtime, code, dependency, secret, license, or
  fixable container finding
- **WHEN** the readiness review is performed
- **THEN** the review remains incomplete until the finding is fixed
- **AND** the release candidate cannot treat an undocumented exception as safe

#### Scenario: Governance or maturity finding is accepted or deferred

- **GIVEN** a scanner finding does not identify an exploitable product defect
- **WHEN** maintainers determine it is not release-blocking
- **THEN** the review records its rationale, mitigation, owner, and revisit
  trigger
- **AND** the automated scanner remains enabled to detect changed conditions
