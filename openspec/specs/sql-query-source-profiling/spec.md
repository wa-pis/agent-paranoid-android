# SQL Query Source Profiling Specification

## Purpose

Define the bounded aggregate-only SQL query source and its no-copy boundary.

## Requirements

### Requirement: SQL Query Is A Virtual Aggregate-Only Source

The application SHALL accept one bounded local SQL `SELECT` as a virtual
database source only after strict dialect parsing, source authorization, and
AST validation. It SHALL profile the relation through trusted schema and
aggregate operations and SHALL NOT fetch or return its result rows.

#### Scenario: Explicit single-table query is accepted

- **GIVEN** one bounded query file containing an allowed `SELECT` with explicit
  projections over one authorized physical table
- **WHEN** query-source profiling runs
- **THEN** the adapter produces one virtual-entity `DatasetProfile` containing
  safe schema metadata, aggregates, and a query fingerprint
- **AND** query text, query literals, backend messages, and source rows are
  absent from the profile and every external boundary

#### Scenario: Query contains forbidden SQL

- **GIVEN** DDL, DML, a command, multiple statements, a join, CTE, subquery,
  set operation, window, table function, volatile function, or unauthorized
  reference
- **WHEN** query-source profiling is requested
- **THEN** the request fails before database execution
- **AND** the error does not echo SQL text or literals

#### Scenario: Query requests an authorized wildcard

- **GIVEN** `SELECT *` or `SELECT alias.*`
- **WHEN** the qualified-column-wildcards contract authorizes the physical
  table and bounded metadata discovery succeeds
- **THEN** the star is expanded to sorted explicit authorized columns
- **AND** the adapter never executes a projection star

### Requirement: Query Profiles Feed Synthetic Generation Without Rows

A successful query-source profile SHALL enter the existing reviewed
`DatasetProfile` to `DatasetSpec` to deterministic generation pipeline, and no
query result row SHALL be available to generation, providers, default MCP,
logs, errors, manifests, or output adapters.

#### Scenario: Generate twice from the same reviewed profile

- **GIVEN** one reviewed query-source profile, the same resulting spec, and the
  same explicit seed
- **WHEN** synthetic generation runs twice
- **THEN** both generated datasets are deterministic under the existing
  reproducibility contract
- **AND** neither dataset copies source rows or query result ordering

#### Scenario: Profiling exceeds a resource budget

- **GIVEN** a validated query whose schema or aggregate work exceeds a
  statement, scan, result, response, column, AST, or wall-clock budget
- **WHEN** query-source profiling runs
- **THEN** the whole operation fails closed and cleans up resources
- **AND** no partial profile or successful-looking artifact is published

### Requirement: Runnable SQL Query Source Examples

The repository SHALL provide PostgreSQL and Trino query-source launchers with
checked-in safe SQL over disposable synthetic sources and SHALL verify the
complete profile-to-generation workflow from an installed package.

#### Scenario: PostgreSQL query-source example runs

- **GIVEN** the checked-in PostgreSQL query, synthetic source, exact allowlists,
  and bounded local connection
- **WHEN** `examples/local_postgres/run-query.sh` runs
- **THEN** it produces a virtual-entity safe profile, reviewed spec,
  deterministic generated dataset, and successful validation
- **AND** artifacts contain a query fingerprint but no query text, query
  literal, backend error, endpoint, or source row

#### Scenario: Trino query-source example runs

- **GIVEN** the checked-in Trino query, pinned synthetic catalog, exact
  allowlists, and bounded local connection
- **WHEN** `examples/local_trino/run-query.sh` runs
- **THEN** it produces a virtual-entity safe profile, reviewed spec,
  deterministic generated dataset, and successful validation
- **AND** artifacts report synthetic output with no copied source rows
