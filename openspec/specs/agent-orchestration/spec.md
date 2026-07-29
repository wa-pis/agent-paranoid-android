# Agent Orchestration Specification

## Purpose

Provide a safe AI-agent-ready orchestration layer that plans synthetic data
generation, requires review before generation, and delegates all deterministic
work to existing profile, spec, generation, validation, and safety code.

## Requirements

### Requirement: Agent Planning Stops Before Generation

The agent orchestration layer SHALL create review artifacts and stop before
writing generated datasets unless an explicit approval step is invoked.

#### Scenario: CSV folder is planned

- **GIVEN** a folder of source CSV files
- **WHEN** `agent-plan` runs
- **THEN** it writes `profile.json`, `dataset_spec.yaml`, `agent_request.json`,
  and `agent_plan.json`
- **AND** it does not write a `generated/` dataset folder

### Requirement: Approval Uses Reviewed DatasetSpec

The approval step SHALL load the prepared workspace and generate from the
reviewed `dataset_spec.yaml`.

#### Scenario: Workspace is approved

- **GIVEN** an agent workspace created by `agent-plan`
- **WHEN** `agent-approve` runs
- **THEN** generation uses the workspace `dataset_spec.yaml`
- **AND** generated artifacts are written under `generated/`
- **AND** `validation_report.json` and `generation_manifest.json` are written

### Requirement: Agent Does Not Return Rows

Agent orchestration SHALL return summaries and artifact paths instead of raw
source rows or generated rows.

#### Scenario: Agent plan or approval completes

- **GIVEN** an agent operation succeeds
- **WHEN** the CLI or API returns a result
- **THEN** the result contains phase, steps, artifact paths, counts, seed, and
  validation status
- **AND** it does not include dataset rows

### Requirement: Source Reuse Checks Remain Deterministic

Approved generation SHALL reuse the existing deterministic source-row safety
checks when source CSV data is available.

#### Scenario: CSV source is approved

- **GIVEN** the agent source is a CSV file or CSV folder
- **WHEN** generated rows are produced
- **THEN** source-row reuse checks run before output is committed
- **AND** the manifest reports `source_rows_copied: false`

### Requirement: LLM Is Planner Only

An LLM client SHALL be treated as a planner and reviewer, not as the generator
or validator.

#### Scenario: LLM client orchestrates the workflow

- **GIVEN** an LLM client is connected to the project
- **WHEN** it needs synthetic data
- **THEN** it may call `agent-plan`, summarize the `DatasetSpec`, request
  approval, and call `agent-approve`
- **AND** deterministic Python code performs generation and validation

### Requirement: Advisor Integration Is Provider Neutral

The agent workflow SHALL expose a typed provider-neutral interface that accepts
safe profile metadata and proposes a structured `DatasetSpec`.

#### Scenario: A model adapter proposes a DatasetSpec

- **GIVEN** a profile that passes the existing profile safety checks
- **WHEN** a provider adapter receives an advisor request
- **THEN** the request contains safe metadata, a deterministic baseline spec,
  and their SHA-256 fingerprints
- **AND** profile text is marked as untrusted data
- **AND** the request contains no source rows, generated rows, credentials, or
  provider SDK objects

### Requirement: Advisor Output Is Untrusted And Review Only

Model-produced proposals SHALL be validated before they can enter the reviewed
generation workflow.

#### Scenario: A structured proposal is returned

- **GIVEN** a proposal bound to the request fingerprints
- **WHEN** the core validates it
- **THEN** Pydantic validates the full `DatasetSpec`
- **AND** schema identity and core-owned safety settings remain unchanged
- **AND** sensitive and identifier classifications cannot be weakened
- **AND** the result requires human approval and performs no generation

### Requirement: Advisor Proposals Enter The Existing Review Gate

The agent workflow SHALL persist validated advisor proposals as review
artifacts and SHALL require the normal reviewed-spec approval before
generation.

#### Scenario: A pending workspace receives a valid proposal

- **GIVEN** an awaiting-approval agent workspace
- **WHEN** advisor handoff succeeds
- **THEN** `advisor_review.json` binds the safe request, proposal, and proposed
  spec fingerprint
- **AND** `dataset_spec.yaml` is updated atomically
- **AND** pending status summarizes the current effective spec
- **AND** interruption can resume without another provider call
- **AND** conflicting human edits fail closed

### Requirement: Advisor Exchange Has A Provider-Neutral JSON Boundary

The agent workflow SHALL export a safe advisor request and apply an untrusted
structured proposal without requiring a model-provider SDK.

#### Scenario: An external AI client proposes a DatasetSpec

- **GIVEN** an awaiting-approval workspace without an existing advisor review
- **WHEN** the client exports a request and applies a fingerprint-bound
  proposal JSON
- **THEN** request output contains safe metadata and no rows or credentials
- **AND** proposal input is bounded and validated by the existing advisor
  contract
- **AND** persistence is retryable and rejects stale or conflicting content
- **AND** generation still requires explicit reviewed-spec approval

### Requirement: Advisor Exchange Is Self Describing

The agent workflow SHALL provide a versioned provider-neutral exchange that
separates trusted instructions, untrusted request data, and the structured
response schema.

#### Scenario: An external AI client exports an exchange

- **GIVEN** a valid awaiting-approval workspace
- **WHEN** exchange-mode advisor export runs
- **THEN** package-owned trusted instructions are separate from the request
- **AND** the request remains fingerprint-bound and explicitly untrusted
- **AND** the response JSON Schema is generated from `AdvisorProposal`
- **AND** modified instructions or schema fail validation
- **AND** export has no provider, persistence, approval, or generation side
  effect

### Requirement: Advisor Client Adapter Preserves Trust Boundaries

The agent workflow SHALL adapt application-owned structured-output clients
without giving them authority over validation, approval, or generation.

#### Scenario: An in-process provider client returns a proposal

- **GIVEN** a safe fingerprint-bound advisor request
- **WHEN** `ExchangeDatasetAdvisor` invokes a structured-output client
- **THEN** the client receives a defensive copy of the self-describing exchange
- **AND** trusted instructions remain separate from untrusted request metadata
- **AND** the response is validated against the original request
- **AND** client mutation cannot weaken the validation source
- **AND** no persistence, approval, or generation occurs

### Requirement: Agent Workspace Status Is Observable

The agent workflow SHALL expose read-only status for planned and completed
workspaces without returning dataset rows.

#### Scenario: Workspace status is inspected

- **GIVEN** a valid planned or completed agent workspace
- **WHEN** `agent-status` runs
- **THEN** it reports the phase, next action, artifact paths, and safe summary
- **AND** `--json` returns a versioned typed contract
- **AND** status inspection does not generate data or modify the workspace

### Requirement: Agent Input Detection Is Narrow And Validated

The CLI SHALL infer CSV files, CSV folders, and validated safe-profile JSON
inputs when their shape is unambiguous.

#### Scenario: Agent source type is omitted

- **GIVEN** an unambiguous supported source path
- **WHEN** `agent-plan` runs without `--source-type`
- **THEN** it selects the matching source adapter
- **AND** explicit `--source-type` remains available as an override
- **AND** DatasetSpec and unsupported inputs fail with actionable guidance

### Requirement: Agent Plan Has A Safe Review Summary

The agent workflow SHALL provide a concise metadata-only review summary after
planning and while approval is pending.

#### Scenario: Plan summary is rendered

- **GIVEN** an inferred agent plan
- **WHEN** the CLI or typed API returns its summary
- **THEN** it reports fields, sensitive classifications, relationships,
  confidence, assumptions, and safety warnings
- **AND** untrusted names are escaped for terminal output
- **AND** source values and dataset rows are excluded

### Requirement: Agent CLI Has A Versioned Machine Contract

Agent planning, pending/completed status, and approval SHALL support stable
versioned JSON output for automation and AI clients.

#### Scenario: Agent command uses JSON mode

- **GIVEN** an agent CLI invocation with `--json`
- **WHEN** the command succeeds or encounters a known input error
- **THEN** stdout contains one typed versioned result or error
- **AND** stderr is empty
- **AND** errors include stable codes and documented exit status
- **AND** results and errors exclude dataset rows, raw values, and tracebacks

### Requirement: Approval Is Bound To The Reviewed DatasetSpec

Every new agent plan SHALL identify and fingerprint its safe review artifacts,
and approval SHALL require the exact fingerprint of the reviewed effective
`DatasetSpec`.

#### Scenario: Exact reviewed spec is approved

- **GIVEN** a valid agent plan and the fingerprint reported after review
- **WHEN** approval receives that fingerprint
- **THEN** the stored profile and current effective spec are verified before
  generation
- **AND** a typed approval receipt binds the plan identifier, profile
  fingerprint, and reviewed spec fingerprint
- **AND** a mismatch or legacy plan fails before generated output is written

### Requirement: Agent Completion Is Recoverable And Idempotent

The agent workflow SHALL expose interrupted completion as an explicit state and
recover it without regenerating or trusting unverified rows.

#### Scenario: Interrupted completion is inspected and recovered

- **GIVEN** an atomically published generated bundle with its completion
  checkpoint but incomplete root result metadata
- **WHEN** status is inspected and recovery is requested with the reviewed
  fingerprint
- **THEN** status reports `recovery_required`
- **AND** recovery revalidates fingerprints, artifacts, rows, validation, and
  source-row non-reuse before publishing completion metadata
- **AND** repeated approval of a completed matching plan returns its existing
  result without rewriting generated rows
