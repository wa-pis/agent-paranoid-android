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

### Requirement: Relationship discovery is safe, reviewable, and deterministic

The system SHALL support AI-assisted discovery of candidate relationships and
business rules from bounded safe metadata, but SHALL require deterministic
validation and review before a proposal affects generation.

#### Scenario: The profiler finds a likely employee-to-payroll relationship

- **GIVEN** bounded profiles show compatible identifier types, cardinality,
  null/distinct ratios, temporal compatibility, and safe relationship evidence
- **WHEN** the deterministic miner and AI advisor produce a candidate
- **THEN** the proposal SHALL include parent/child fields, relationship type,
  confidence, evidence, assumptions, and a review status
- **AND** it SHALL not include raw source rows or sensitive raw values

#### Scenario: An AI provider proposes an unsupported or contradictory link

- **GIVEN** the provider proposal has low confidence, incompatible types, or
  conflicts with deterministic evidence
- **WHEN** the proposal is normalized
- **THEN** it SHALL remain rejected or require explicit human review
- **AND** it SHALL not silently become an FK or generation constraint

### Requirement: Synthetic output preserves relational and business semantics

For an approved relationship and rule set, generation SHALL preserve the
requested relational graph, distribution/order-of-magnitude shape, temporal
constraints, and executable business invariants without copying source rows.

#### Scenario: Synthetic payroll data is generated from employee metadata

- **GIVEN** approved employee, payroll, department, position, and period
  relationships
- **WHEN** a dataset is generated with a fixed seed
- **THEN** all requested FKs and temporal rules SHALL validate
- **AND** salary values SHALL be synthetic while retaining configured ranges,
  ratios, distributions, and order-of-magnitude characteristics

#### Scenario: A financial summary requires reconciliation

- **GIVEN** approved salary-component, article, period, debit/credit, or
  cross-table aggregate formulas
- **WHEN** synthetic data is generated
- **THEN** deterministic validation SHALL verify every requested formula
- **AND** generation SHALL fail or report the violation rather than publish a
  dataset marked valid

### Requirement: AI providers receive metadata only

AI-assisted discovery SHALL use a bounded provider-neutral contract and SHALL
never send raw source rows, generated rows, secrets, credentials, or sensitive
raw category values.

#### Scenario: An advisor request is built for relationship discovery

- **GIVEN** profiles, candidate links, aggregates, masked patterns, and
  fingerprints are available
- **WHEN** an advisor request is serialized
- **THEN** the payload SHALL contain safe metadata only
- **AND** the response SHALL be schema-validated, bounded, fingerprint-bound,
  and treated as untrusted until reviewed

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
