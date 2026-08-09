# Agent Orchestration Delta

## ADDED Requirements

### Requirement: Rare-Category Sanitization Is Complete And Order Independent

Advisor request construction SHALL replace every rare profile category in both
the profile and baseline by stable entity-and-field identity without assuming
that their category lists use the same order. Generated placeholders SHALL be
opaque, deterministic, field-scoped, and collision-free against every
categorical string in both objects. Structural-identity preservation alone
SHALL NOT satisfy the sanitization check; no original rare value may remain in
the provider-bound request.

#### Scenario: Baseline categories are reordered

- **GIVEN** a safe profile contains a rare category and a valid baseline lists
  the same categories in a different order
- **WHEN** an `AdvisorRequest` is built
- **THEN** the rare value is replaced in both profile and baseline
- **AND** the serialized request contains none of the original rare value
- **AND** entity, field, relationship, count, and non-value distribution
  structure remain unchanged

#### Scenario: Baseline contains a placeholder-shaped literal

- **GIVEN** any profile or baseline category already matches the generated
  placeholder syntax
- **WHEN** a different rare category is sanitized
- **THEN** the generated placeholder uses a deterministic non-colliding name
- **AND** the ordinary literal is not treated as generated solely because its
  text matches the syntax

#### Scenario: Persisted advisor review is revalidated

- **GIVEN** a persisted request contains generated placeholders and the current
  workspace profile is reloaded
- **WHEN** profile and baseline fingerprints are verified
- **THEN** generated-placeholder provenance is established from the reviewed
  request and stable field/category identity rather than list position alone
- **AND** a reordered or truncated category list fails closed instead of
  restoring an unrelated raw value

### Requirement: Advisor Failure Redaction Drops Provider-Controlled Context

The OpenAI adapter SHALL convert every ordinary SDK construction exception,
including exceptions outside the SDK's typed error hierarchy, plus provider
transport, structured-validation, and incomplete-response failures to typed
bounded local errors. Public errors, metadata, logs, formatted tracebacks,
`__cause__`, and `__context__` SHALL contain no provider exception object,
provider exception text or dynamic Python exception class name, response
payload, prompt, profile value, credential, or raw response status. Error
reasons SHALL come from a finite local allowlist.

#### Scenario: SDK or provider call raises an exception

- **GIVEN** SDK initialization or a provider call raises any ordinary exception,
  including one outside the SDK's typed error hierarchy, containing a synthetic
  secret marker in its message or Python class name
- **WHEN** the adapter returns its typed failure
- **THEN** the marker is absent from the error string, representation, metadata,
  logs, and formatted traceback
- **AND** both `__cause__` and `__context__` are empty
- **AND** the public message is one exact fixed local allowlisted value
- **AND** call-local bounded metadata records only the local failure class

#### Scenario: Structured output is invalid

- **GIVEN** provider output fails local Pydantic validation and the validation
  exception contains provider-controlled content
- **WHEN** the adapter raises `OpenAIAdvisorCallError`
- **THEN** the original validation exception is not retained
- **AND** the failure reason is the fixed local `invalid_response` status

#### Scenario: Provider reports an incomplete status

- **GIVEN** a provider response has a non-completed or unexpected status value
- **WHEN** the adapter rejects the response
- **THEN** the public error uses a fixed bounded local message
- **AND** raw status text is absent from the error and metadata

### Requirement: External Advisor Requests Are Source-Free By Construction

The advisor request sent to an external provider SHALL contain only synthetic
or non-reversible categorical representations. Heuristic sensitive-value
classification SHALL NOT be the final decision for whether a source-derived
categorical value may cross the provider boundary.

#### Scenario: Common categorical values are profiled

- **GIVEN** a profile contains a low-cardinality string field whose values are
  not recognized by the sensitive-value heuristics
- **WHEN** an external advisor request is built
- **THEN** every category value is replaced with a field-scoped synthetic label,
  rank, masked pattern, or count-only representation
- **AND** the original values are absent from the serialized request,
  fingerprints, metadata, logs, and provider error surfaces
- **AND** category counts, nullability, and non-value structural relationships
  remain available for deterministic planning

### Requirement: Provider Constraints Are Semantically Enforced

Untrusted advisor proposals SHALL preserve the local DatasetSpec constraint
contract. Formula constraints SHALL use only allowlisted numeric arithmetic and
validated field references; string constants, unknown references, and sensitive
targets SHALL be rejected before persistence or generation. Generated rows SHALL
undergo privacy and type validation after constraint solving and before
publication.

#### Scenario: Provider proposes a string formula constant

- **GIVEN** an advisor proposal adds a formula that evaluates to a string
  constant or targets a sensitive field
- **WHEN** the proposal is validated or generation is requested
- **THEN** the proposal is rejected with a fixed local reason
- **AND** no generated row, validation report, manifest, or CSV output contains
  the proposed value
- **AND** the provider expression and nested exception text are absent from
  public errors and logs

#### Scenario: Formula validation fails

- **GIVEN** a provider-controlled expression is syntactically invalid or
  produces a type error
- **WHEN** deterministic generation or validation reports the failure
- **THEN** the public diagnostic uses a finite local error reason
- **AND** it does not include the expression, AST dump, expected value, actual
  value, or nested exception text
