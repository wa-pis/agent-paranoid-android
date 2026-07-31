# Operational Readiness Delta

## Added Requirements

### Requirement: Mid-write Disk Exhaustion Cleanup

Staged generation workflows SHALL fail closed when the target filesystem
reports disk exhaustion after partial output has been written.

#### Scenario: A staged write runs out of space

- **GIVEN** folder, review, or single-entity generation has written a partial
  staged file
- **WHEN** the filesystem reports `ENOSPC`
- **THEN** the staging directory is removed
- **AND** the final destination and success metadata are not published
- **AND** the operating-system error is propagated to the caller

#### Scenario: The user retries after freeing space

- **GIVEN** a failed run left no published bundle
- **WHEN** sufficient capacity is restored
- **THEN** the user can retry from the same reviewed spec and seed
- **AND** no partial file is treated as successful input
