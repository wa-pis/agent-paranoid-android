# Agent Orchestration Specification Delta

## ADDED Requirements

### Requirement: Agent Planning Stops Before Generation

The agent orchestration layer SHALL create review artifacts and stop before
writing generated datasets unless an explicit approval step is invoked.

#### Scenario: CSV folder is planned

- **GIVEN** a folder of source CSV files
- **WHEN** `agent-plan` runs
- **THEN** it writes review artifacts
- **AND** it does not write generated dataset rows

### Requirement: Approval Uses Reviewed DatasetSpec

The approval step SHALL load the prepared workspace and generate from the
reviewed `dataset_spec.yaml`.

#### Scenario: Workspace is approved

- **GIVEN** an agent workspace created by `agent-plan`
- **WHEN** `agent-approve` runs
- **THEN** generation uses the workspace spec and writes a synthetic bundle
