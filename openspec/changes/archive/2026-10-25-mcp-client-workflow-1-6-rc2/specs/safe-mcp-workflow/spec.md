# Safe MCP Workflow Delta: mcp-client-workflow-1-6-rc2

## ADDED Requirements

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
