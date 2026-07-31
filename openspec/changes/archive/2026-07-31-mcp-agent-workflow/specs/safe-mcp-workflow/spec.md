# Safe MCP Workflow Specification Delta

## Added Requirements

### Requirement: Workspace Sources Have A High-Level Planning Tool

The generator MCP SHALL expose one review-first planning tool for supported
workspace sources without returning rows.

#### Scenario: AI client plans from a workspace source

- **GIVEN** a CSV file, CSV folder, or safe profile below the workspace root
- **WHEN** `plan_dataset` receives the source and a new workspace path
- **THEN** it detects or validates the source type and writes review artifacts
- **AND** it stops before generation
- **AND** it returns only compact metadata, fingerprints, and artifact paths

#### Scenario: Planning input crosses a trust boundary

- **GIVEN** a source outside the workspace, a DatasetSpec, or an invalid
  source override
- **WHEN** `plan_dataset` is called
- **THEN** it rejects the request before writing an agent workspace
