# Agent Orchestration Specification Delta

## Added Requirements

### Requirement: Agent Input Detection Is Narrow And Validated

The CLI SHALL infer supported agent source types when the input shape is
unambiguous and SHALL retain an explicit override.

#### Scenario: CSV folder is planned without an override

- **GIVEN** a directory containing regular CSV files
- **WHEN** `agent-plan` runs without `--source-type`
- **THEN** it treats the source as a CSV folder
- **AND** normal profiling and safety checks still apply

#### Scenario: JSON input is detected

- **GIVEN** a JSON input
- **WHEN** source detection runs
- **THEN** the bounded profile/spec loader validates its content
- **AND** only safe profile metadata is accepted by `agent-plan`

#### Scenario: Detection is ambiguous or unsupported

- **GIVEN** an empty folder, unsupported file, or DatasetSpec
- **WHEN** source detection runs
- **THEN** it fails with an actionable command or override
