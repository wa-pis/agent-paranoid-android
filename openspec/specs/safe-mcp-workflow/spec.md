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
  source-literal-free summaries

### Requirement: Workspace-Bounded Generator Tools

The generator MCP server SHALL resolve input and output paths inside an
explicit workspace root.

The reviewed, registered selective-transformation consumer SHALL NOT authorize
preservation through ordinary generator tools. Workspace execution SHALL only
consume matching local controlling-terminal receipts, never issue them.
New or changed public activation SHALL require matching policy amendments,
executable interface evidence and exact-SHA independent safety review.

The separately selected transformation names the workspace consumer
`execute_transformation`, local CLI consumer `transform-execute` and local
controlling-terminal issuer `transform-approve`. Execution SHALL require the
reviewed exact snapshot digest and a matching receipt for preservation. A fresh
review digest SHALL NOT make an earlier receipt valid after source, policy or
referenced input mutations. MCP SHALL register no receipt issuer. Unreviewed
extensions MAY be exercised in isolated fictional acceptance and SHALL remain
unavailable on public surfaces until the activation gates above complete.
Ordinary generator tools remain source-free.

The owner-approved explicit replacement contract SHALL apply uniformly to all
fields: mapped source membership or sensitive-value permutations alone SHALL
NOT reject a separately reviewed transformation. Effective sensitivity SHALL
remain a bounded value-free field note. This SHALL NOT broaden direct preserve,
preserve fallback, receipt issuance, source-free tools, or MCP row disclosure.
Only deterministic evidence of actually applied mappings may select the local
artifact replacement path; no client approval flag SHALL substitute for it.

#### Scenario: Sensitive mapping has a value-free response

- **GIVEN** fictional explicit mappings between sensitive source values
- **WHEN** the separately gated workspace transformation executes after review
- **THEN** local mixed-origin artifact values follow the selected mapping.
- **AND** MCP returns bounded summaries/paths, never either mapping literal.
- **AND** ordinary generator tools retain their synthetic-only contract.

#### Scenario: Path traversal is attempted

- **GIVEN** a client provides `../`, absolute paths outside the workspace, or
  symlink escapes
- **WHEN** a generator MCP tool resolves the path
- **THEN** the operation is rejected

### Requirement: No Dataset Rows In Default MCP Responses

Default generator and default aggregate-only Trino MCP responses SHALL return
summaries and artifact paths instead of dataset rows. Explicit opt-in
row-returning tools are outside this guarantee.

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

#### Scenario: Default aggregate-only Trino surface is inspected

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

### Requirement: Default Aggregate-Only And Explicit Opt-In Trino Surfaces

The default aggregate-only tools SHALL expose fixed allowlisted metadata and
aggregate profiling. The explicit opt-in row-returning tools, including
`run_safe_select`, SHALL require operator opt-in.

#### Scenario: Default aggregate-only Trino surface is registered

- **GIVEN** `TRINO_ENABLE_SAFE_SELECT` is unset or false
- **WHEN** the Trino MCP server registers its tools
- **THEN** fixed allowlisted metadata and aggregate profiling tools are exposed
- **AND** the explicit opt-in row-returning tool `run_safe_select` is not exposed

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

### Requirement: Default Aggregate-Only Responses Are Source-Literal-Free

The default aggregate-only tools SHALL expose only metadata and bounded
aggregate profiling responses. Successful responses, typed errors, and
metadata-only audit records SHALL NOT contain literal values copied from source
cells.

#### Scenario: A profile contains distinct values in every source column

- **GIVEN** a source fixture whose every column contains a distinct literal,
  including non-PII-looking identifiers, statuses, dates, and free text
- **WHEN** a default aggregate-only Trino tool is invoked
- **THEN** no source literal is present in the response, error, or audit payload

### Requirement: Default Toolset Has No Row-Sampling Diagnostic

The default public MCP and Python compatibility surfaces SHALL NOT expose
`sample_rows_masked` or another masked-row sampling diagnostic. A future
row-returning diagnostic SHALL require a separate OpenSpec change with an
independent configuration flag, catalog/schema/table/column allowlists, no
wildcard projection, strict row and column limits, metadata-only audit
logging, and visible capability status.

#### Scenario: Default tool surfaces are registered

- **GIVEN** the Trino MCP server and its public compatibility module are
  loaded
- **WHEN** the Trino MCP server registers its tools
- **THEN** `sample_rows_masked` is not registered or exported as a supported
  tool
- **AND** `run_safe_select` is registered only when its independent explicit
  opt-in is enabled

### Requirement: Explicit Opt-In Row-Returning Tools Are Not Source-Free

The explicit opt-in row-returning tools SHALL remain disabled by default and
separate from the default aggregate-only tools. A bounded `run_safe_select`
result MAY contain allowed non-PII source values and SHALL NOT be described as
source-free, anonymous, PII-free, or privacy-safe solely because heuristic
masking is applied. Its errors and metadata-only audit records SHALL NOT
contain returned values or source literals.

#### Scenario: Safe select is explicitly enabled

- **GIVEN** `TRINO_ENABLE_SAFE_SELECT=true` and valid catalog/schema allowlists
- **WHEN** a bounded read-only query is executed
- **THEN** the query is handled under the independent safe-select policy
- **AND** the result is not covered by the default aggregate-only
  source-literal-free response guarantee
- **AND** audit records contain operation status and error type only

### Requirement: Default Toolset Is Tested As A Whole

The source-literal-free guarantee SHALL be tested against the actual default
tool list returned by the same composition root used in production, not only
against individual profiling functions.

#### Scenario: Every default Trino tool is exercised

- **GIVEN** a fixture with distinct source literals in every supported type
- **WHEN** each registered default Trino tool is invoked through its direct
  service and MCP transport boundaries
- **THEN** successful responses, validation/database errors, and nested JSON
  values contain none of the source-cell literals
- **AND** metadata-only audit records contain no arguments, results, or source
  literals

### Requirement: Trino Work Is Bounded Per Invocation

Each Trino MCP invocation SHALL use one shared typed work budget across nested
profiling and query operations. The budget SHALL bound request size,
SQL/formula size, AST complexity and depth, projected columns, statements, and
response bytes, and SHALL fail closed before the corresponding limit is
consumed. A raw transport payload limit SHALL be enforced before MCP argument
parsing, and a canonical argument limit SHALL be enforced after schema
validation.

The budget SHALL be fresh per invocation, isolated between concurrent
invocations, shared with nested helpers, monotonic, and non-resettable.
Response bytes SHALL be consumed incrementally before a complete oversized
response is materialized.

#### Scenario: Nested profiling exceeds the shared budget

- **GIVEN** table profiling starts with a bounded invocation budget
- **WHEN** nested column profiling exhausts any shared allowance
- **THEN** the invocation stops with a bounded typed error and performs no later
  query or column operation

#### Scenario: Preflight work exceeds its budget

- **GIVEN** request, SQL, or AST validation can determine that a limit is
  exceeded before database access
- **WHEN** the Trino MCP operation is submitted
- **THEN** it fails before opening a connection or cursor

### Requirement: Rejected MCP Arguments Are Not Reflected

Generator and Trino MCP transports SHALL replace typed argument-validation
failures with a fixed local error before returning a tool result.

#### Scenario: A typed tool argument is rejected

- **GIVEN** a caller supplies a bounded value that fails FastMCP/Pydantic
  argument validation
- **WHEN** either MCP server dispatches the tool call
- **THEN** the tool is not executed
- **AND** the response contains the fixed `Tool arguments failed validation`
  error
- **AND** the rejected value and nested validation exception are not returned

### Requirement: Malformed MCP Values Do Not Reach SDK Logs

Generator and Trino MCP transports SHALL reject malformed typed client
messages before passing them to the MCP SDK.

#### Scenario: A typed MCP request contains a malformed value

- **GIVEN** a byte- and structure-bounded JSON-RPC request with a valid request
  ID and a caller-controlled value that fails typed MCP validation
- **WHEN** either MCP server receives the request
- **THEN** the request is not dispatched to the SDK or a tool
- **AND** the response contains code `-32602` and fixed
  `Invalid request parameters` text
- **AND** the caller-controlled value is absent from the response, local logs,
  and retained exception state

#### Scenario: A typed MCP notification contains a malformed value

- **GIVEN** a byte- and structure-bounded JSON-RPC notification that fails
  typed MCP validation
- **WHEN** either MCP server receives the notification
- **THEN** it is not dispatched to the SDK or a tool
- **AND** no response is written
- **AND** the caller-controlled value is absent from local logs and retained
  exception state

### Requirement: Documented Local Assistant Workflow

The project SHALL provide a generator-only local MCP quickstart that uses
fictional inputs, explicit seeds, existing tools, and human-reviewed approval.

#### Scenario: A client follows the quickstart

- **GIVEN** an installed MCP extra and a dedicated local workspace
- **WHEN** the client follows the documented configuration and tool calls
- **THEN** it can discover tools, plan, inspect, approve after human review,
  and inspect completed validated artifacts
- **AND** no live database or external AI provider is required
- **AND** responses contain summaries and paths rather than dataset rows

### Requirement: Actionable Existing Tool Descriptions

Planning, inspection, approval, and recovery tool descriptions SHALL identify
when to use each operation and its review or state prerequisites without
changing tool names or input/output schemas.

#### Scenario: An assistant selects approval

- **GIVEN** a planned workspace with an inspectable specification
- **WHEN** the assistant reads the approval tool description
- **THEN** it is instructed to require human review of the exact specification
  and pass its current fingerprint
- **AND** inspection alone is not represented as human approval

### Requirement: Real Client Workflow Acceptance

The release candidate SHALL verify the documented local workflow through an
actual MCP SDK client and stdio generator subprocess using fictional fixtures.

#### Scenario: A reviewed synthetic plan completes

- **GIVEN** a fictional workspace input, explicit seed, and requested count
- **WHEN** the client plans, inspects, and approves the reviewed fingerprint
- **THEN** no dataset exists before approval
- **AND** completed artifacts have the expected counts and successful validation
- **AND** provenance confirms synthetic generation without source-row copying
- **AND** repeating the input specification and seed reproduces dataset values
- **AND** source-cell sentinels do not appear in MCP responses or captured logs

#### Scenario: Review becomes stale

- **GIVEN** the specification changed after its fingerprint was reviewed
- **WHEN** the client submits approval using the old fingerprint
- **THEN** approval is rejected without generating output
- **AND** the documented next step requires renewed human review

#### Scenario: Approval is interrupted

- **GIVEN** an interrupted approval and a recoverable workspace state
- **WHEN** the client inspects and invokes the permitted recovery operation
  using the reviewed fingerprint
- **THEN** recovery preserves published generated artifacts without regeneration
- **AND** completion remains inspectable through summary-only responses
- **AND** session and subprocess cleanup completes within bounded deadlines

### Requirement: RC2 Acceptance Is Commit Bound

MCP workflow improvements SHALL target `1.6.0rc2` with acceptance evidence bound
 to its exact reviewed commit and the existing release procedure.

#### Scenario: RC2 is prepared

- **GIVEN** the actual RC1 baseline and its outstanding acceptance state
- **WHEN** maintainers prepare RC2
- **THEN** prior policy and release blockers are resolved rather than bypassed
- **AND** focused tests, full gates, independent review, manual client evidence,
  and artifact checks identify the exact candidate
- **AND** this planning change alone does not authorize publication

### Requirement: Interrupted Runtime Failures Are Redacted Across SDK Majors

The MCP transport SHALL detach unexpected native exception causes before responses
or SDK logging on both supported SDK major versions, retaining only reconstructed
safe cleanup and resource-budget diagnostics.

#### Scenario: Synthetic publication is interrupted by an unexpected failure

- **GIVEN** an unexpected runtime failure contains a fictional private sentinel
- **WHEN** an SDK 1 or SDK 2 client invokes approval
- **THEN** the failure response contains only fixed safe error text
- **AND** responses and logs omit the sentinel
- **AND** the workspace remains inspectable for permitted recovery

### Requirement: Transformation stages retain the shared request deadline

Generator MCP SHALL capture a finite positive
`TEST_DATA_AGENT_MCP_MAX_INVOCATION_SECONDS` at startup (default 120 seconds)
and share it between transport and service budgets. Tool arguments SHALL NOT
override it. Independent generation, profiling, transformation and payload
limits SHALL remain enforced. Invalid values SHALL fail startup with a
value-free error before tool registration or audit setup.

MCP single and common transformation consumers SHALL enforce the active shared
request invocation deadline at their existing work checkpoints, including the
last checkpoint before publication and the checkpoint after rename/fsync.
The generation deadline and byte ceilings SHALL also apply. Expiry SHALL stop work without a new retained publication and
return a typed value-free invocation deadline error.

#### Scenario: Deadline expires during capture or execution
- **GIVEN** an admitted MCP request and fictional bound local input
- **WHEN** its shared deadline expires during transformation work
- **THEN** review, validation or execution rejects at the next checkpoint
- **AND** original artifacts remain intact and no retained destination is published.

#### Scenario: Deadline expires before directory rename
- **WHEN** the request deadline expires while staging the validated bundle
- **THEN** the pre-publication checkpoint rejects and removes only owned staging
- **AND** unverifiable cleanup keeps its distinct cleanup-incomplete error.

#### Scenario: Legitimate caller has no shared MCP context
- **WHEN** direct local execution runs without an active MCP request budget
- **THEN** the existing generation and byte ceilings apply without inventing
  a new MCP timeout or changing local receipt authority.

#### Scenario: Deadline expires during directory publication
- **WHEN** the shared deadline expires during rename or directory fsync
- **THEN** the completion checkpoint rejects within the cleanup-protected block
- **AND** identity-confirmed retained output is removed before returning the error.

### Requirement: Common saved-profile consumers preserve local authority

The common CLI and generator MCP SHALL consume the same saved profile and exact
reviewed identity. Generator MCP SHALL take its root from trusted server workspace
configuration, require explicit positive input/review/output byte budgets, retain
existing transport/work ceilings and reject unknown caller arguments without
reflecting their values. MCP SHALL NOT create preservation receipts. Public
registration SHALL remain gated by finished-candidate independent safety review.

#### Scenario: Installed common workflow consumes a local receipt
- **GIVEN** a fictional saved profile reviewed and confirmed through local controlling-TTY CLI
- **WHEN** CLI or MCP validates or executes the exact reviewed snapshot
- **THEN** preservation requires the existing bound receipt
- **AND** missing or stale authority is rejected without exposing source values
- **AND** MCP returns bounded review/summary metadata rather than output rows

#### Scenario: Common output retention is explicit and bounded
- **GIVEN** an execute request with a configured workspace and explicit byte budgets
- **WHEN** destination names a new direct-child bundle
- **THEN** validated output may be retained using the existing safe publication mechanism
- **AND** review/validate destinations, unsafe paths and existing destinations are rejected
- **AND** omission of destination retains no output bundle

### Requirement: Transformation Authority Is Separate From Generation

Workspace transformation execution SHALL be a separately selected mixed-origin
operation. It SHALL NOT reuse source-free generation approval or permit an
agent/MCP client to issue or broaden a preservation receipt. New or changed public
activation SHALL remain unavailable until matching policy amendments, executable
interface evidence and independent safety review of the precise activation SHA complete.
Existing default profiling/generation tools and disclosure budgets SHALL remain
unchanged.

The registered separate workspace tool SHALL be named
`execute_transformation`. It SHALL require the reviewed `snapshot_sha256`,
resolve source/policy/receipt/output paths through the existing workspace
boundary, share the bounded transport request budget and publish only a new
validated local bundle. Success SHALL return `transformation_completed`,
digest, provenance counts and output-budget metadata, never rows or mapping
literals. Local controlling-TTY `transform-approve` SHALL be the only supported
receipt issuer for the single-source workflow; `transform-execute` and MCP
SHALL consume, not create, preservation authority.
These registered names SHALL NOT grant authority to activate further extensions.

Explicit `substitute` and `replace_text` SHALL use the same replacement contract
for sensitive, unknown and non-sensitive fields. Actual mapped output cells MAY
equal other source values, including sensitive permutations, in the selected
local mixed-origin artifact. Review SHALL retain a value-free sensitivity note.
This exception SHALL NOT broaden direct preservation, unmatched-preserve
fallback, receipt issuance, source-free generation, or transport disclosure.
Deterministic execution SHALL record actual mapped-cell evidence; a caller's
approval flag SHALL NOT provide that evidence.

#### Scenario: Sensitive permutation stays local

- **GIVEN** an explicit mapping swaps fictional sensitive values
- **WHEN** the separately gated workspace execution applies the mapping
- **THEN** mapped cells use the uniform replacement contract
- **AND** MCP returns bounded summaries and artifact paths without mapping literals
- **AND** ordinary generation remains source-free and synthetic

#### Scenario: Receipt is stale despite a fresh review digest

- **GIVEN** a genuine receipt binds the earlier exact source and policy bytes
- **WHEN** source or inline mapping bytes change and review produces a new digest
- **AND** execution supplies that new digest with the earlier receipt
- **THEN** preservation fails before publication
- **AND** the receipt and previous publication remain unchanged

#### Scenario: Piped approval text is supplied

- **WHEN** a detached local CLI receives APPROVE through piped stdin
- **THEN** no preservation receipt is created
- **AND** an agent approval flag cannot substitute for terminal confirmation

#### Scenario: Agent requests preservation without local approval

- **GIVEN** a policy requests preservation or unmatched-preserve fallback
- **WHEN** workspace execution lacks a matching locally issued receipt
- **THEN** execution fails before publication
- **AND** agent-provided booleans or authorization references grant no authority

#### Scenario: Agent consumes a matching local receipt

- **GIVEN** the separate execution surface has passed its activation gates
  and a local controlling-terminal operator approved exact input/review bytes
- **WHEN** workspace execution consumes the matching receipt
- **THEN** deterministic validation enforces sensitivity and snapshot binding
- **AND** paths remain workspace-confined and responses contain metadata only
- **AND** changed input bytes require renewed local review and approval

#### Scenario: Private extension review has completed but activation has not

- **WHEN** private implementation review passes without completed public
  amendment and registration evidence
- **THEN** the unreviewed extension is unavailable on the registered surface
- **AND** source-free generation tools cannot consume preservation authority

### Requirement: Transformation Failure Does Not Imply Clean Publication

Transformation execution SHALL distinguish budget rejection and actual budget
exhaustion with value-free typed diagnostics. Publication cleanup SHALL operate
only on captured invocation-owned identities. Unverifiable cleanup SHALL return
a distinct sanitized cleanup-incomplete error rather than imply no artifacts
remain; it SHALL NOT delete unverified paths or authorize overwrite retries.

#### Scenario: Snapshot total is exhausted

- **WHEN** policy, source, references, classification and review bytes exceed
  the effective shared total ceiling
- **THEN** execution fails before publication with amount, threshold, bytes,
  configuration origin and supported recovery keys
- **AND** no source values appear in responses, logs or exception chains

#### Scenario: Failed publication cannot verify cleanup

- **WHEN** cleanup cannot confirm the identity of an invocation-owned artifact
- **THEN** the error warns that output or staging may remain
- **AND** local inspection is required before retrying without overwrite
