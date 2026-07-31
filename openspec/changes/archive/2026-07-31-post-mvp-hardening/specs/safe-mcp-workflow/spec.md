# Safe MCP Workflow Specification Delta

## ADDED Requirements

### Requirement: Review-First Trino Planning

The MCP workflow SHALL turn safe metadata from an allowlisted Trino table into
a reviewable DatasetSpec and SHALL stop before generation.

#### Scenario: Safe Trino plan is approved

- **GIVEN** `profile_table_safe` returned bounded metadata
- **WHEN** `plan_trino_dataset` writes a plan and a reviewer calls
  `approve_dataset_plan`
- **THEN** deterministic generation uses the reviewed DatasetSpec
- **AND** MCP responses contain summaries and paths, not rows

### Requirement: Authenticated MCP Audit Records

Shared MCP deployments SHALL support metadata-only, sequence-linked,
HMAC-authenticated audit events.

#### Scenario: Tool invocation is audited

- **GIVEN** a valid audit path and key
- **WHEN** an MCP tool runs
- **THEN** authenticated start and completion events are appended
- **AND** tool inputs, outputs, SQL, rows, and error messages are excluded

## MODIFIED Requirements

### Requirement: Safe Trino Surface

The default MCP surface SHALL expose fixed allowlisted metadata and aggregate
profiling tools. The generic `run_safe_select` tool SHALL require explicit
operator opt-in.
