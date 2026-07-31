# Safe MCP Workflow Specification Delta

## Modified Requirements

### Requirement: Review-First Trino Planning

The MCP workflow SHALL expose read-only plan inspection and require the exact
reviewed effective-spec fingerprint before approval.

#### Scenario: Trino plan is inspected and approved

- **GIVEN** a workspace created by `plan_trino_dataset`
- **WHEN** the client calls `inspect_dataset_plan`
- **THEN** it receives the current effective-spec fingerprint without changing
  the workspace
- **AND** `approve_dataset_plan` generates only when
  `reviewed_spec_sha256` matches that fingerprint
- **AND** the response contains an approval receipt and artifact paths, not
  rows
