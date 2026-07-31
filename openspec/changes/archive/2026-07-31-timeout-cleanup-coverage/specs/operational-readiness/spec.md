# Operational Readiness Delta

## Added Requirements

### Requirement: Staged Timeout Cleanup

Every staged generation output shape SHALL fail closed when its deterministic
generation deadline expires before publication.

#### Scenario: A workflow deadline expires after staging

- **GIVEN** folder, review, or single-entity generation has staged output
- **WHEN** a workflow boundary detects the expired generation deadline
- **THEN** the entire staging directory is removed
- **AND** the final destination and success metadata are not published
- **AND** the timeout error is propagated to the caller

#### Scenario: A user retries a timed-out run

- **GIVEN** a timeout left no published partial bundle
- **WHEN** the user retries with an appropriate deadline
- **THEN** the same reviewed spec and seed produce deterministic output
- **AND** the abandoned attempt is not treated as successful
