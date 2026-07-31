# Release Candidate Hardening Requirements

## Added Requirements

### Requirement: All generation entry points enforce the spec safety boundary

Every supported generation entry point SHALL validate the complete
`DatasetSpec` before generating rows or publishing artifacts.

#### Scenario: A manually constructed spec contains a raw sensitive category

- **GIVEN** a `DatasetSpec` contains a categorical value that is sensitive by
  explicit metadata, semantic type, field name, value detection, or default
  unknown-field policy
- **WHEN** the caller invokes the Python, CLI, agent, or generator MCP API
- **THEN** generation SHALL fail before writing generated rows or artifacts
- **AND** the error SHALL identify the entity and field without exposing the
  sensitive value

#### Scenario: A valid reviewed spec is generated through multiple adapters

- **GIVEN** the same reviewed safe spec, seed, and supported runtime
- **WHEN** it is generated through Python, CLI, and MCP adapters
- **THEN** all adapters SHALL apply the same safety policy
- **AND** valid synthetic output SHALL remain compatible with the existing
  artifact contracts

### Requirement: External Trino execution is read-only and validated

The public Trino service SHALL expose only dedicated bounded operations or
queries that pass the safe SQL policy before DB-API execution.

#### Scenario: A caller submits unsafe SQL through a direct Python import

- **GIVEN** SQL contains DDL, DML, unrestricted projection, disallowed joins,
  CTEs, subqueries, or an unsafe/missing limit
- **WHEN** a caller invokes any public Trino operation
- **THEN** the operation SHALL fail before `cursor.execute()` is called
- **AND** no raw SQL text or result rows SHALL be returned in the error

#### Scenario: A dedicated profiler needs an aggregate query

- **GIVEN** the operation is an internal, tested metadata or aggregate profiler
- **WHEN** it builds a query from validated identifiers and bounded parameters
- **THEN** it MAY use the private internal executor
- **AND** the resulting metadata SHALL remain masked or aggregate-only

### Requirement: Supported validation settings have executable semantics

Every documented validation setting SHALL affect validation behavior, or it
SHALL be removed from the supported `DatasetSpec` contract before the RC.

#### Scenario: A caller disables a validation section

- **GIVEN** a valid `DatasetSpec` explicitly disables one supported validation
  section
- **WHEN** validation runs
- **THEN** that section SHALL be omitted according to the documented behavior
- **AND** the manifest/report SHALL identify the effective validation settings

### Requirement: Reproducibility claims are bounded and evidenced

The project SHALL distinguish logical reproducibility from byte-for-byte
reproducibility and record the identity of components that affect output.

#### Scenario: A generated bundle is accepted as reproducible

- **GIVEN** a fixed spec, seed, locale, runtime, dependency set, serializer,
  and generator algorithm version
- **WHEN** generation completes
- **THEN** the manifest SHALL record the effective reproducibility inputs
- **AND** the release tests SHALL verify the documented reproducibility level

### Requirement: The release candidate has auditable hardening evidence

`1.0.0rc1` SHALL be blocked by unresolved P0 findings and SHALL record an
owner, rationale, and revisit date for every accepted P1 or lower risk.

#### Scenario: A P0 boundary test fails

- **GIVEN** a direct API can emit raw sensitive values or execute unsafe SQL
- **WHEN** the RC release gate runs
- **THEN** the release gate SHALL fail
- **AND** the candidate SHALL not be published

#### Scenario: Only non-blocking findings remain

- **GIVEN** P0 tests and required release gates pass
- **WHEN** the security review is finalized
- **THEN** accepted remaining findings SHALL include evidence, owner,
  disposition, and revisit trigger
- **AND** the RC may proceed without adding new product features
