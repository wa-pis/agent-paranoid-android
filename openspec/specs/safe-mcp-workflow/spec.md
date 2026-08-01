# Safe MCP Workflow Specification

## Purpose

Expose safe, explicit MCP tools for Trino profiling and synthetic generation
without giving an AI client unrestricted database, filesystem, or raw data
access.

## Requirements

### Requirement: Read-Only Trino Surface

The Trino MCP server SHALL expose only safe metadata, profiling, and bounded
read-only query operations.

#### Scenario: Unsafe SQL is submitted

- **GIVEN** a query contains DDL, DML, multiple statements, unrestricted
  `SELECT *`, executable commands, or no literal bounded `LIMIT`
- **WHEN** the Trino MCP server validates the query
- **THEN** the query is rejected before execution

#### Scenario: Safe profiling is requested

- **GIVEN** an allowlisted catalog and schema
- **WHEN** metadata or aggregate profiling is requested
- **THEN** the server returns schema, aggregates, distributions, ranges, and
  masked samples only where allowed

### Requirement: Workspace-Bounded Generator Tools

The generator MCP server SHALL resolve input and output paths inside an
explicit workspace root.

#### Scenario: Path traversal is attempted

- **GIVEN** a client provides `../`, absolute paths outside the workspace, or
  symlink escapes
- **WHEN** a generator MCP tool resolves the path
- **THEN** the operation is rejected

### Requirement: No Dataset Rows In MCP Responses

MCP responses SHALL return summaries and artifact paths instead of dataset rows.

#### Scenario: Dataset is generated through MCP

- **GIVEN** a client invokes generation or export
- **WHEN** the tool succeeds
- **THEN** the response includes row counts, output paths, validation status,
  spec version, and manifest context
- **AND** it does not include generated rows, source rows, or raw PII

### Requirement: Explicit Workflow Steps

Generator MCP tools SHALL keep profiling, spec inference, generation,
validation, and export as explicit operations.

#### Scenario: Export is requested

- **GIVEN** a `DatasetSpec` and requested output format
- **WHEN** `export_dataset` runs
- **THEN** it generates fresh synthetic data from the spec
- **AND** it does not convert arbitrary source rows into exported output

### Requirement: Review-First Trino Planning

The MCP workflow SHALL support planning from an allowlisted Trino table without
granting the planning client raw-SQL access.

#### Scenario: Trino profile is planned

- **GIVEN** `profile_table_safe` returns bounded metadata for an allowlisted
  catalog and schema
- **WHEN** the client passes that payload to `plan_trino_dataset`
- **THEN** the generator writes a safe profile, DatasetSpec, and approval plan
  inside its workspace
- **AND** no source or generated rows are returned
- **AND** generation does not start until `approve_dataset_plan` is called

#### Scenario: Trino plan is inspected and approved

- **GIVEN** a workspace created by `plan_trino_dataset`
- **WHEN** the client calls `inspect_dataset_plan`
- **THEN** it receives the current effective-spec fingerprint without changing
  the workspace
- **AND** `approve_dataset_plan` requires that exact fingerprint as
  `reviewed_spec_sha256`
- **AND** successful approval returns receipt and artifact metadata, not rows

#### Scenario: Default Trino MCP surface is inspected

- **GIVEN** `TRINO_ENABLE_SAFE_SELECT` is unset or false
- **WHEN** the Trino MCP server registers its tools
- **THEN** `run_safe_select` is not exposed
- **AND** fixed metadata and aggregate profiling tools remain available

### Requirement: MCP Agent Recovery Is Explicit

The generator MCP SHALL report recovery-required plans and expose bounded
recovery without regenerating or returning rows.

#### Scenario: Interrupted MCP plan is recovered

- **GIVEN** `inspect_dataset_plan` reports `recovery_required`
- **WHEN** `recover_dataset_plan` receives the reviewed spec fingerprint
- **THEN** it revalidates the existing bundle and publishes completion metadata
- **AND** no generated rows are returned

### Requirement: Workspace Sources Have A High-Level Planning Tool

The generator MCP SHALL expose one review-first planning tool for supported
workspace sources without returning rows.

#### Scenario: Workspace source is planned

- **GIVEN** a CSV file, CSV folder, or safe profile below the workspace root
- **WHEN** `plan_dataset` receives the source and a new workspace path
- **THEN** it writes review artifacts and stops before generation
- **AND** it returns only compact metadata, fingerprints, and artifact paths

### Requirement: Manifest-Gated Validation

MCP validation SHALL verify generated bundles against their manifest and
effective spec.

#### Scenario: Spec does not match generated bundle

- **GIVEN** a generated bundle has a manifest with a spec fingerprint
- **WHEN** validation is requested with a different spec
- **THEN** validation rejects the mismatch instead of silently validating the
  wrong contract

### Requirement: Structured Business Rules

The generator MCP server SHALL accept bounded, structured business rules for
generation and export without granting arbitrary code execution.

#### Scenario: Valid business rules are supplied

- **GIVEN** a reviewed DatasetSpec and exactly one rule file or inline payload
- **WHEN** generation or export runs
- **THEN** deterministic code applies and validates the rules
- **AND** the manifest records their fingerprint and validation summary
- **AND** detailed bounded errors are written to a workspace report

#### Scenario: Unsafe business rules are supplied

- **GIVEN** rules contain unknown keys, dangling references, unsupported
  expressions, excessive input, or raw-looking sensitive literals
- **WHEN** the generator MCP server validates the request
- **THEN** it rejects the request before creating output artifacts
- **AND** no source or generated rows are returned in the error

### Requirement: Authenticated MCP Audit Records

Shared MCP deployments SHALL support opt-in, tamper-evident audit records
without persisting tool inputs or outputs.

#### Scenario: Signed audit logging is enabled

- **GIVEN** an operator configures an audit path and HMAC key
- **WHEN** an MCP tool is invoked
- **THEN** a metadata-only `started` event is authenticated before execution
- **AND** a linked `succeeded` or `failed` event is authenticated afterward
- **AND** arguments, SQL, profiles, rows, return values, and exception messages
  are not recorded

#### Scenario: Audit configuration is invalid

- **GIVEN** audit logging is partially configured, unsafe, or full
- **WHEN** an MCP tool is invoked
- **THEN** the operation fails closed instead of running without an audit event

#### Scenario: Audit key is supplied as a container secret

- **GIVEN** exactly one bounded, regular, non-writable audit key file
- **WHEN** an MCP worker initializes audit logging
- **THEN** it decodes the key without exposing it through process environment
- **AND** symlinks, hard links, oversized files, and conflicting key sources
  are rejected

### Requirement: MCP Transport Cannot Bypass Application Safety

Generator and Trino MCP transports SHALL delegate to application services that
enforce the same validation and safety policy when called directly.

#### Scenario: MCP registration is separated from a service

- **GIVEN** an existing public MCP tool and its golden contract fixture
- **WHEN** transport registration delegates to an extracted application
  service
- **THEN** the tool name, input schema, result schema, and typed errors remain
  compatible
- **AND** workspace limits, row-free responses, audit behavior, and Trino
  allowlists remain enforced
- **AND** direct service calls cannot bypass the safety checks

### Requirement: Bounded Business Validation Response

MCP business-rule responses SHALL remain metadata-only and bounded.

#### Scenario: Business validation contains row-level failures

- **GIVEN** generated synthetic rows violate one or more configured rules
- **WHEN** generation completes
- **THEN** the MCP response contains only aggregate pass/fail counts, validity,
  the rule fingerprint, and artifact paths
- **AND** detailed bounded errors are written to the workspace report
- **AND** generated rows are not returned inline

### Requirement: Safe Trino Surface

The default MCP surface SHALL expose fixed allowlisted metadata and aggregate
profiling tools. The generic `run_safe_select` tool SHALL require explicit
operator opt-in.

#### Scenario: Default safe Trino surface is registered

- **GIVEN** `TRINO_ENABLE_SAFE_SELECT` is unset or false
- **WHEN** the Trino MCP server registers its tools
- **THEN** fixed allowlisted metadata and aggregate profiling tools are exposed
- **AND** the generic `run_safe_select` tool is not exposed

### Requirement: External Trino Execution Is Read-Only And Validated

Every public Trino operation SHALL use a dedicated bounded query builder or
pass the safe SQL policy before DB-API execution.

#### Scenario: A direct caller submits unsafe SQL

- **GIVEN** SQL contains DDL, DML, unrestricted projection, disallowed joins,
  CTEs, subqueries, or an unsafe or missing limit
- **WHEN** a public Trino operation receives it
- **THEN** the operation fails before `cursor.execute()` is called
- **AND** the error returns neither raw SQL nor result rows

#### Scenario: A dedicated profiler needs an aggregate query

- **GIVEN** an internal metadata or aggregate profiler
- **WHEN** it builds a query from validated identifiers and bounded parameters
- **THEN** it may use the private executor
- **AND** only masked or aggregate metadata is returned
