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
