# Safe MCP Workflow Specification Delta

## Added Requirements

### Requirement: MCP Agent Recovery Is Explicit

The generator MCP SHALL expose the agent recovery state and a dedicated bounded
recovery operation.

#### Scenario: MCP recovers an interrupted plan

- **GIVEN** `inspect_dataset_plan` reports `recovery_required`
- **WHEN** `recover_dataset_plan` receives the reviewed spec fingerprint
- **THEN** it revalidates the existing bundle and returns completion metadata
- **AND** it does not regenerate or return rows
