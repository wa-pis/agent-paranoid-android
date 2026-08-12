# Agent Orchestration Specification Delta

## Added Requirements

### Requirement: GigaChat Advisor Is Explicit And Review Gated

The agent workflow SHALL expose GigaChat only as an explicitly selected
optional advisor and SHALL preserve the existing deterministic review and
approval boundary.

#### Scenario: GigaChat proposes a DatasetSpec

- **GIVEN** the GigaChat extra, runtime credentials, and a planned agent
  workspace
- **WHEN** the user selects `gigachat` for `agent-advise`
- **THEN** the adapter receives only a validated provider-neutral exchange
- **AND** package instructions and untrusted profile metadata use separate
  message roles
- **AND** one non-streaming completion requires a strict `AdvisorProposal`
  schema
- **AND** successful output is validated against the original fingerprints
- **AND** human approval remains required before deterministic generation

#### Scenario: GigaChat is not selected

- **GIVEN** a base installation or a different advisor selection
- **WHEN** planning, approval, generation, or validation runs
- **THEN** the GigaChat SDK is not imported
- **AND** no GigaChat credential is resolved
- **AND** no GigaChat network request occurs

### Requirement: GigaChat Receives No Source Literals

The GigaChat adapter SHALL preserve the external-provider privacy boundary for
the complete serialized request.

#### Scenario: A profile contains sensitive and locally preserved values

- **GIVEN** source data contains sensitive literals and an explicitly approved
  local bounded business category
- **WHEN** a GigaChat advisor request is serialized
- **THEN** source rows, sensitive literals, credentials, tokens, and generated
  rows are absent
- **AND** exact preserved category values and matching categorical predicate
  values are replaced by field-scoped synthetic labels
- **AND** the reverse label mapping is not sent to GigaChat
- **AND** exact values may be restored only inside the local fingerprint-bound
  review flow

### Requirement: GigaChat Invocation Is Bounded And Fail Closed

Every GigaChat advisor invocation SHALL enforce local request, response,
token, timeout, retry, and total-work limits.

#### Scenario: Provider work stays within policy

- **GIVEN** a safe exchange and valid bounded GigaChat settings
- **WHEN** the adapter invokes the provider
- **THEN** request size is checked before network work
- **AND** exactly one non-streaming structured completion is requested
- **AND** timeout, output-token, retry, and total-work ceilings are explicit
- **AND** response content is byte-bounded before proposal JSON parsing

#### Scenario: Provider output is not safely complete

- **GIVEN** an empty, multiple-choice, truncated, filtered, `blacklist`,
  oversized, malformed, extra-field, or schema-invalid response
- **WHEN** the adapter validates the completion
- **THEN** it raises a stable redacted contract error
- **AND** raw provider content and exception text are discarded
- **AND** no review artifact, approval, generated record, or output is written

### Requirement: GigaChat Has No Application Authority

The GigaChat adapter SHALL not receive or gain authority over sources,
workspaces, persistence, approval, generation, or validation.

#### Scenario: Provider or model output is adversarial

- **GIVEN** GigaChat returns instructions, invented entities, changed safety
  settings, stale fingerprints, or an attempted approval
- **WHEN** the proposal enters the provider-neutral boundary
- **THEN** deterministic code either substitutes the exact local baseline
  during the documented compatibility fallback or rejects unauthorized content
- **AND** the adapter cannot access a database, filesystem publisher, or
  generator to act on it
- **AND** the existing pending workspace remains safe and retryable

#### Scenario: Beta structured output materializes invalid baseline defaults

- **GIVEN** GigaChat returns schema-shaped JSON that omits known fields or
  weakens baseline-owned identity, privacy, or existing constraint values
- **WHEN** the first `AdvisorProposal` validation fails
- **THEN** the adapter requires matching baseline entity and constraint identity
  and substitutes the exact local fingerprint-bound `dataset_spec`
- **AND** no provider-proposed dataset value survives the compatibility fallback
- **AND** the normalized proposal passes the same Pydantic, fingerprint,
  profile, privacy, and advisor-contract validation or fails closed

### Requirement: GigaChat Errors And Metrics Are Redacted

GigaChat diagnostics SHALL be bounded and SHALL exclude all request, response,
authentication, and source content.

#### Scenario: SDK or provider call fails

- **GIVEN** an SDK exception or non-success provider response contains a
  credential, token, request fragment, response fragment, header, or local path
- **WHEN** the failure crosses the provider boundary
- **THEN** the caller receives only a stable local error category
- **AND** logs and per-call metadata contain none of those values
- **AND** metadata may retain only bounded model, setting, byte-count, timing,
  retry, finish-category, status, and validated usage fields
