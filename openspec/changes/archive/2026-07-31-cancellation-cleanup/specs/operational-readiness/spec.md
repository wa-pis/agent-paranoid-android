# Operational Readiness Delta

## Added Requirements

### Requirement: Cooperative Cancellation Cleanup

Generation workflows SHALL remove their staging directory when cooperative
process cancellation interrupts staged writing or validation.

#### Scenario: Cancellation interrupts staged publication

- **GIVEN** folder, review, or single-entity generation has created a staging
  directory
- **WHEN** interactive cancellation interrupts writing or validation
- **THEN** the staging directory is removed
- **AND** the final destination and success metadata are not published
- **AND** the cancellation is re-raised to the caller

#### Scenario: The process cannot run cleanup

- **GIVEN** hard termination or host failure prevents in-process cleanup
- **WHEN** the process stops
- **THEN** cooperative cleanup is not claimed
- **AND** abandoned-staging recovery remains a separate operational concern
