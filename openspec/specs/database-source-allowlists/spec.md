# Database Source Allowlists Specification

## Purpose

Define exact and table-qualified wildcard authorization for database profiling.

## Requirements

### Requirement: Table-Qualified Column Wildcard

Database source configuration SHALL accept a wildcard only when it identifies
all columns of one exact table. PostgreSQL requires the parent table in its
table allowlist. Trino requires unrestricted mode to be disabled and the exact
catalog and schema to be allowlisted; the selector names the exact table.

#### Scenario: PostgreSQL wildcard is authorized

- **GIVEN** `schema.table.*` and an exact matching PostgreSQL schema/table
  allowlist
- **WHEN** profiling starts
- **THEN** bounded metadata discovery expands the selector into an immutable,
  sorted list of explicit qualified columns
- **AND** all profiling queries enumerate quoted columns rather than `*`

#### Scenario: Trino wildcard is authorized

- **GIVEN** `catalog.schema.table.*`, exact matching Trino catalog/schema
  allowlists, and unrestricted mode disabled
- **WHEN** profiling starts
- **THEN** bounded metadata discovery expands the selector into an immutable,
  sorted list of explicit qualified columns
- **AND** all existing invocation and scan budgets remain in force

#### Scenario: Wildcard is not table-qualified

- **GIVEN** `*`, `schema.*`, `catalog.schema.*`, or a wildcard table name
- **WHEN** configuration is validated
- **THEN** validation fails before metadata or source access

### Requirement: Wildcard Scope Does Not Authorize Values

A qualified column wildcard SHALL authorize aggregate profiling scope only and
SHALL NOT authorize source-row return, caller SQL projection stars,
preserve-as-is, external provider literals, default MCP literals, logs, or
errors.

#### Scenario: Preserve-as-is is requested through wildcard scope

- **GIVEN** a table-qualified wildcard and no exact field preservation policy
- **WHEN** local preservation is evaluated
- **THEN** every expanded field remains masked or replaced by default
- **AND** no source literal is retained or disclosed

#### Scenario: Expansion exceeds a budget

- **GIVEN** a qualified wildcard whose metadata expands beyond a configured
  column or invocation budget
- **WHEN** expansion is evaluated
- **THEN** the whole profiling request fails closed
- **AND** no partial profile is published

### Requirement: Runnable Qualified Wildcard Examples

The repository SHALL provide separate PostgreSQL and Trino launchers that use
table-qualified wildcard allowlists against disposable synthetic sources and
exercise the complete safe profile-to-generation workflow.

#### Scenario: PostgreSQL wildcard example runs

- **GIVEN** exact PostgreSQL schema/table allowlists and qualified column
  wildcards for the checked-in synthetic tables
- **WHEN** `examples/local_postgres/run-wildcard.sh` runs
- **THEN** the safe profile contains the deterministic expected explicit field
  set and generated output validates
- **AND** no field is preserved as-is without a separate exact field policy

#### Scenario: Trino wildcard example runs

- **GIVEN** exact Trino catalog/schema allowlists, unrestricted mode disabled,
  and a qualified wildcard for one synthetic table
- **WHEN** `examples/local_trino/run-wildcard.sh` runs
- **THEN** the safe profile contains the deterministic expected explicit field
  set and generated output validates
- **AND** captured executed SQL contains no projection star
