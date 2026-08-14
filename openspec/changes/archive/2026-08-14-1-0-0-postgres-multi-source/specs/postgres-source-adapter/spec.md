# PostgreSQL Source Adapter Delta

## ADDED Requirements

### Requirement: PostgreSQL Profiling Is Optional And Driver-Isolated

The PostgreSQL adapter SHALL be available through a separate optional
installation profile and SHALL not be imported or required by the base
installation. Deterministic profile conversion SHALL be testable with an
injected driver or fake connection.

#### Scenario: Base installation has no PostgreSQL driver

- **GIVEN** a user installs the base package without the `postgres` extra
- **WHEN** the user runs the base demo, generation, or validation workflow
- **THEN** the package remains importable and functional
- **AND** no PostgreSQL driver is imported or required

#### Scenario: PostgreSQL adapter uses a fake driver

- **GIVEN** a test supplies an injected driver that returns bounded metadata and
  aggregate results
- **WHEN** the adapter profiles a source
- **THEN** it produces the same typed `DatasetProfile` contract as the real
  driver path
- **AND** the test does not require a live database

### Requirement: PostgreSQL Sessions Are Read-Only And Allowlisted

Every PostgreSQL profile invocation SHALL validate a schema allowlist and an
optional table allowlist before connecting. The session SHALL be configured as
read-only with bounded statement, lock, and invocation timeouts. The adapter
SHALL accept only internally generated metadata and aggregate queries.

#### Scenario: Missing allowlist

- **GIVEN** a PostgreSQL source has no schema allowlist
- **WHEN** a production-like profile invocation starts
- **THEN** it fails closed before opening a profiling operation
- **AND** it does not enumerate unrestricted schemas or tables

#### Scenario: Write or arbitrary SQL is requested

- **GIVEN** a caller or AI request contains DDL, DML, a side-effecting function,
  or arbitrary SQL text
- **WHEN** the PostgreSQL adapter validates the request
- **THEN** it rejects the request before execution
- **AND** no database operation is opened for the rejected statement

#### Scenario: Profile deadline expires

- **GIVEN** an aggregate query or metadata operation exceeds the remaining
  invocation deadline
- **WHEN** the deadline is reached
- **THEN** the adapter cancels or closes the active operation and connection
- **AND** it publishes no complete profile

### Requirement: PostgreSQL Profiles Contain Safe Metadata And Aggregates

The adapter SHALL extract bounded table and column metadata, row counts,
nullability, approximate cardinality, ranges, safe distributions, declared
primary/foreign keys, and supported constraint evidence. Default profiling
SHALL NOT return source rows or exact sensitive numeric values.

#### Scenario: Relational PostgreSQL schema is profiled

- **GIVEN** an allowlisted PostgreSQL schema contains tables with PKs, FKs,
  nullable fields, checks, numeric fields, dates, and low-cardinality strings
- **WHEN** the adapter profiles it
- **THEN** it returns a valid `DatasetProfile(source_type="postgres")`
- **AND** declared relationships and supported constraints are represented
- **AND** distributions are bounded and safe for the existing review pipeline

#### Scenario: Sensitive singleton numeric field is profiled

- **GIVEN** a sensitive numeric field has one distinct non-null source value
- **WHEN** its aggregate profile is created
- **THEN** exact extrema, percentiles, and the singleton value are absent
- **AND** only non-reversible shape metadata is retained

#### Scenario: Profile query would return rows

- **GIVEN** a proposed profiling operation uses row-shaped projection or
  unbounded result materialization
- **WHEN** the adapter validates the operation
- **THEN** it rejects the operation before query execution

### Requirement: PostgreSQL Failures Are Bounded And Source-Free

Connection failures, backend errors, DSNs, credentials, hostnames, raw CHECK
expressions, and provider-controlled text SHALL NOT appear in public errors,
profiles, manifests, logs, or advisor requests. A failed requested source SHALL
fail the bundle rather than produce a silently partial accepted profile.

#### Scenario: Backend error contains a secret marker

- **GIVEN** a PostgreSQL driver raises an error containing a password, DSN, or
  source-derived value
- **WHEN** the adapter handles the error
- **THEN** the public result contains only a fixed local reason and safe source
  alias metadata
- **AND** the marker is absent from errors, logs, traces, and artifacts

#### Scenario: Required table cannot be profiled

- **GIVEN** a requested table is missing, disallowed, or cannot be profiled
- **WHEN** a source bundle is assembled
- **THEN** the bundle fails closed
- **AND** no partial profile is accepted as a complete input to generation
