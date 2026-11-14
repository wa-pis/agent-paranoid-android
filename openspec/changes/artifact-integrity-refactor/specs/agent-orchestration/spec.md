## ADDED Requirements

### Requirement: Reviewed source and completion integrity

CSV planning SHALL fingerprint the bytes consumed by profiling. The row-reuse
check SHALL compare the bytes it consumes to the reviewed digest.

#### Scenario: Source changes during profiling

- **WHEN** bytes consumed during profiling differ from the source at plan publication
- **THEN** the system SHALL reject the plan before publication

#### Scenario: Completion recovery

- **WHEN** a user recovers an interrupted generated bundle
- **THEN** recovery SHALL verify its checkpoint-bound manifest and complete artifact inventory
- **AND** recovery SHALL reject modified bundles and checkpoints without manifest binding
