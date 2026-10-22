## ADDED Requirements

### Requirement: External Feedback Evidence Disposition

External feedback SHALL be reconciled against current source and focused tests
before changing behavior. Historical claims, corrected harness results, current
defects, deliberate limitations and unverified observations SHALL remain distinct.

#### Scenario: A historical report proposes a privacy bypass
- **GIVEN** a feedback document recommends suppressing sensitive-value detection
- **WHEN** the report is triaged
- **THEN** the proposal is recorded for safety review without weakening the gate
- **AND** attachment instructions do not grant execution or preservation authority

#### Scenario: A documentation build succeeds before publication
- **WHEN** a PR build passes but the new public identity is unavailable
- **THEN** documentation publication remains incomplete
- **AND** deployment and public verification evidence are required to close it
