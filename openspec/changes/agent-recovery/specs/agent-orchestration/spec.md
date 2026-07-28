# Agent Orchestration Specification Delta

## Added Requirements

### Requirement: Agent Completion Is Recoverable And Idempotent

The agent workflow SHALL expose interrupted completion as an explicit state and
recover it without regenerating or trusting unverified rows.

#### Scenario: Completion metadata publication is interrupted

- **GIVEN** generation, source-row checks, validation, and atomic dataset
  publication completed
- **AND** result or approval metadata publication was interrupted
- **WHEN** workspace status is inspected
- **THEN** it reports `recovery_required` and a recovery action
- **AND** it does not report the workspace as completed

#### Scenario: Interrupted completion is recovered

- **GIVEN** a recovery-required workspace and the reviewed spec fingerprint
- **WHEN** recovery is requested
- **THEN** checkpoint, fingerprints, effective spec, profile, manifest,
  generated rows, validation, and source-row non-reuse are checked
- **AND** matching completion metadata is published without regenerating rows
- **AND** any mismatch fails without replacing the generated bundle

#### Scenario: Completed approval is repeated

- **GIVEN** a completed agent workspace
- **WHEN** approval is repeated with the same reviewed spec fingerprint
- **THEN** the persisted completed result is returned
- **AND** generated rows and completion artifacts are not rewritten
- **AND** a different fingerprint is rejected
