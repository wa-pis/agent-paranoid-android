## ADDED Requirements

### Requirement: Transformation Authority Is Separate From Generation

Workspace transformation execution SHALL be a separately selected mixed-origin
operation. It SHALL NOT reuse source-free generation approval or permit an
agent/MCP client to issue or broaden a preservation receipt. Registration
SHALL remain unavailable until matching policy amendments, executable interface
evidence and independent safety review of the precise activation SHA complete.
Existing default profiling/generation tools and disclosure budgets SHALL remain
unchanged.

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
