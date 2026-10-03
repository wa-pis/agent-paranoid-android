## ADDED Requirements

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
agent/MCP client to issue or broaden a preservation receipt. Registration
SHALL remain unavailable until matching policy amendments, executable interface
evidence and independent safety review of the precise activation SHA complete.
Existing default profiling/generation tools and disclosure budgets SHALL remain
unchanged.

The concrete activation candidate SHALL name its separate workspace tool
`execute_transformation`. It SHALL require the reviewed `snapshot_sha256`,
resolve source/policy/receipt/output paths through the existing workspace
boundary, share the bounded transport request budget and publish only a new
validated local bundle. Success SHALL return `transformation_completed`,
digest, provenance counts and output-budget metadata, never rows or mapping
literals. Local `transform-approve` SHALL be the only supported receipt issuer;
`transform-execute` and MCP SHALL consume, not create, preservation authority.
These names SHALL NOT imply that candidate registration is publicly active.

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

#### Scenario: Private code review has completed but activation has not

- **WHEN** private implementation review passes without completed public
  amendment and registration evidence
- **THEN** no transformation execution tool is registered
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
