# Agent Orchestration Specification Delta

## Added Requirements

### Requirement: Agent Workspace Status Is Observable

The agent workflow SHALL expose read-only status for planned and completed
workspaces without returning dataset rows.

#### Scenario: Planned workspace is inspected

- **GIVEN** a valid workspace awaiting review
- **WHEN** `agent-status` runs
- **THEN** it reports the awaiting-approval phase and review action
- **AND** it does not generate data or modify the workspace

#### Scenario: Completed workspace is inspected as JSON

- **GIVEN** a valid completed workspace
- **WHEN** `agent-status --json` runs
- **THEN** it returns a versioned typed status with artifact paths and summary
- **AND** it does not include source or generated rows

#### Scenario: Incomplete workspace is inspected

- **GIVEN** a partial or contradictory workspace
- **WHEN** status inspection runs
- **THEN** it fails with the missing or inconsistent state
