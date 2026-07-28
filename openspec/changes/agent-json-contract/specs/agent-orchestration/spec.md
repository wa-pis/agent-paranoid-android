# Agent Orchestration Specification Delta

## Added Requirements

### Requirement: Agent CLI Has A Versioned Machine Contract

Agent planning, status, and approval SHALL support stable versioned JSON for
automation and AI clients.

#### Scenario: Agent command succeeds as JSON

- **GIVEN** a valid plan, status, or approval command
- **WHEN** it runs with `--json`
- **THEN** stdout contains one versioned typed result
- **AND** stderr is empty
- **AND** the result contains summaries and artifact paths, not dataset rows

#### Scenario: Agent command fails as JSON

- **GIVEN** invalid arguments, input, or paths
- **WHEN** an agent command runs with `--json`
- **THEN** stdout contains one versioned structured error
- **AND** the error contains a stable code, message, command, exit code, and
  optional recovery command
- **AND** stderr is empty and no traceback or input payload is exposed
