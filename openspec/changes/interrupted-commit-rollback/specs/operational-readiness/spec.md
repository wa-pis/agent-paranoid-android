# Operational Readiness Delta

## Added Requirements

### Requirement: Interrupted Publication Rollback

Generation workflows SHALL roll back output when publication is interrupted
after commit has begun but before success returns to the caller.

#### Scenario: Folder rename completes before interruption

- **GIVEN** a folder or review staging directory has been atomically renamed
- **WHEN** publication is interrupted before success returns
- **THEN** the renamed destination is removed
- **AND** no manifest or output is reported as successful

#### Scenario: Single-entity commit is partially complete

- **GIVEN** some staged files have moved into an existing output directory
- **WHEN** publication is interrupted
- **THEN** new files are removed and replaced files are restored
- **AND** unrelated files remain unchanged
- **AND** the original interruption error is propagated
