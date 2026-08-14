# PostgreSQL SQL Export Delta

## ADDED Requirements

### Requirement: SQL Export Produces One Valid PostgreSQL File

The SQL output adapter SHALL produce one UTF-8 `.sql` file containing
PostgreSQL-compatible schema DDL and INSERT statements for a validated generated
dataset. The file SHALL be executable as one transaction and SHALL NOT require
a source database connection during rendering.

#### Scenario: A related generated dataset is exported

- **GIVEN** a validated generated dataset contains parent and child entities
- **WHEN** PostgreSQL SQL export completes
- **THEN** one `.sql` file contains deterministic CREATE TABLE and INSERT
  statements in a dependency-aware order
- **AND** executing the complete file can preserve the declared relationship

### Requirement: Identifiers And Scalar Values Are Rendered Safely

The exporter SHALL quote PostgreSQL identifiers and SHALL serialize only the
supported typed scalar values using PostgreSQL-compatible literals. String and
identifier delimiters SHALL be escaped, NULL SHALL remain SQL NULL, and output
ordering SHALL be deterministic for the same specification, records, and seed.

#### Scenario: Names and values contain delimiters

- **GIVEN** generated schema metadata contains a reserved identifier or quote
- **AND** a generated string contains an apostrophe
- **WHEN** SQL is rendered
- **THEN** identifiers and values are escaped according to PostgreSQL syntax
- **AND** no generated value can terminate its literal and inject SQL

#### Scenario: Generated values include NULL and typed scalars

- **GIVEN** generated records contain NULL, booleans, numbers, strings, and
  supported date/time values
- **WHEN** SQL is rendered
- **THEN** each value has a PostgreSQL-compatible typed representation
- **AND** NULL is not emitted as a quoted string

### Requirement: SQL Export Is Synthetic-Only

The exporter SHALL accept generated records and reviewed schema metadata only.
It SHALL NOT query a PostgreSQL source, accept source rows, or turn profile query
results into INSERT statements. Exact source-derived values MAY appear only
when they entered generated records through the approved field-scoped local
preservation contract.

#### Scenario: A caller supplies source-profile rows

- **GIVEN** a caller attempts to pass raw source rows or database query results
  directly to SQL export
- **WHEN** the export request is validated
- **THEN** the request is rejected before publication
- **AND** no SQL artifact is created

### Requirement: SQL Publication Is Atomic And Fail-Closed

The exporter SHALL validate identifiers, relationships, type mappings, and
values before replacing the destination. It SHALL write through a sibling
temporary file and atomically publish the completed artifact. Unsupported or
ambiguous input, cancellation, or write failure SHALL leave no partial target
reported as complete.

#### Scenario: A value has no supported PostgreSQL representation

- **GIVEN** a generated value or schema type cannot be represented safely
- **WHEN** export validation runs
- **THEN** export fails with a bounded local error
- **AND** the previous target remains unchanged and temporary output is removed

#### Scenario: Export is interrupted

- **GIVEN** writing stops before the transaction and all statements are complete
- **WHEN** cleanup runs
- **THEN** no partial target is published
- **AND** a later reader cannot mistake the interrupted file for complete output

### Requirement: SQL Validity Is Verifiable Without Live PostgreSQL

The normal test suite SHALL verify generated SQL with deterministic golden
fixtures and a PostgreSQL-aware parser or parse-only check that makes no network
connection. A live disposable PostgreSQL execution check MAY exist only as an
explicitly gated integration test.

#### Scenario: The base test suite validates SQL output

- **GIVEN** no PostgreSQL server or credentials are available
- **WHEN** SQL export tests run
- **THEN** syntax, quoting, ordering, literals, relationships, and determinism
  are still verified
- **AND** no live database connection is attempted
