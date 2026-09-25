# Selective Source Transformation Specification Delta

Proposed capability only; no existing guarantee is modified by this document.

## ADDED Requirements

### Requirement: Existing permitted SQL connectors remain usable

The system SHALL consistently enforce already-permitted boolean expressions
across supported SQL profiling adapters without widening source authorization,
function allowlists or resource budgets.

#### Scenario: Compound predicate without new SQL capabilities

- **GIVEN** an allowlisted single-table query with supported predicates
- **WHEN** predicates are combined using AND, OR and supported negation
- **THEN** connector/function classification does not reject permitted syntax,
  while forbidden functions, unauthorized columns and exceeded budgets still fail.

### Requirement: Effective generation settings are truthful

The system SHALL apply documented setting precedence consistently across
generation entrances and SHALL record settings actually used by generation.
Intentional invalid-data modes SHALL NOT bypass privacy enforcement.

#### Scenario: Explicit mode differs from a saved specification

- **GIVEN** a saved specification and an explicit mode/ratio selection
- **WHEN** generation resolves that selection under the documented contract
- **THEN** output behavior, effective specification and manifest agree, or the
  conflicting request is rejected explicitly rather than silently ignored.
- **AND** validation status, publication behavior and JSON/exit semantics follow
  the documented distinction between controlled negatives and failed valid runs.

### Requirement: Typed artifacts and unknown evidence are honest

Supported exact financial types SHALL retain precision/scale without float
intermediates. Typed Parquet output SHALL preserve declared supported logical
types; unsupported or intentionally invalid values SHALL follow an explicit
contract rather than silently converting a whole column. Profiling SHALL NOT
present unmeasured statistics or sensitivity as observed zero or established safety.
For 1.6.0rc1, exact DECIMAL precision SHALL be 1..38 with scale 0..precision;
higher precision SHALL fail with a value-free error, never fall back to FLOAT,
implicit rounding or decimal256 output.

#### Scenario: Typed output is read back

- **GIVEN** a supported specification containing dates, timestamps, nullable
  fields and exact decimal values
- **WHEN** a valid dataset is published as Parquet and read back
- **THEN** physical logical types and decimal precision/scale remain consistent
  with the specification, and unavailable profiling evidence stays unavailable.

### Requirement: Diagnostic recovery preserves confidentiality

Diagnostics SHALL distinguish missing dependencies from known local capability
failures and retain completed checks when a smoke test fails. Recovery guidance
SHALL use bounded safe categories rather than source data or backend exceptions.

#### Scenario: Installed optional capability fails publication

- **GIVEN** the required optional dependency is installed
- **WHEN** a local capability smoke fails during publication
- **THEN** doctor reports the failed check and an appropriate safe cause, does
  not mislabel the dependency as absent, and exposes no credentials or source values.

### Requirement: Scoped typed substitution dictionaries

The system SHALL support explicit local replacement dictionaries scoped to
selected fields or shared mapping domains through a first-class substitute
action distinct from synthesize. Matching SHALL use declared types
and SHALL apply once to original values. Unmapped values SHALL fail unless
an explicit compatible policy authorizes their handling. Mapping entries SHALL
remain outside logs, reports, external providers and default MCP responses.

#### Scenario: Wizard and noninteractive parity

- **GIVEN** a transformation policy selecting substitution rather than synthesis
- **WHEN** that policy is saved by the wizard or authored directly and executed
  through supported CLI or Python transformation interfaces
- **THEN** the same approved input and policy produce equivalent results without
  hidden interactive state or a fallback to synthesis unless explicitly declared.

#### Scenario: Consistent reporting-date replacement

- **GIVEN** a date mapping from 2025-04-30 to 2026-09-23 for selected fields
- **WHEN** an authorized input contains multiple occurrences of that date
- **THEN** every occurrence in those fields maps to 2026-09-23, unrelated fields
  are unaffected, row count is unchanged and dependent constraints are validated.

#### Scenario: Conflicting mapping

- **GIVEN** conflicting entries, a prohibited target or a mapping that violates
  declared uniqueness or temporal constraints
- **WHEN** transformation is validated
- **THEN** publication fails without exposing the original/replacement values.

### Requirement: Behavior profile retains substitution decisions

The editable data behavior profile SHALL support explicit per-field substitution,
mapping references and unmatched-value handling. Observed statistics SHALL remain
distinct from user-authored behavior policies. Profile persistence and conversion
to a transformation specification SHALL preserve approved substitution decisions.
Profiles SHALL NOT embed sensitive mapping entries in shared artifacts.

#### Scenario: Inline and file-based mappings

- **GIVEN** equivalent mappings declared inline in private YAML or in a referenced
  local CSV file
- **WHEN** either policy is validated and executed
- **THEN** typed replacement semantics are equivalent and source-bearing inline
  policies are treated as restricted inputs, never exported as safe metadata.

#### Scenario: Profile to executable policy

- **GIVEN** a behavior profile selecting substitution with a local mapping reference
- **WHEN** it is saved, reloaded and converted to a transformation specification
- **THEN** the action, scope, mapping reference and unmatched-value policy survive
  unchanged, and execution uses the mapping rather than an inferred generator.

#### Scenario: Conflicting or unsupported profile policy

- **GIVEN** incompatible profile/specification decisions or an unsupported version
- **WHEN** the transformation policy is loaded
- **THEN** validation fails explicitly instead of silently dropping substitution.

### Requirement: Consistent user documentation

Before release the complete documentation surface SHALL be audited and every
affected page SHALL distinguish source-free generation from transformation,
document field decisions and mapping security, and avoid unsupported privacy
claims. Historical release evidence SHALL remain identifiable as historical.

#### Scenario: Candidate documentation acceptance

- **GIVEN** a candidate implementing transformation
- **WHEN** release readiness is assessed
- **THEN** documented workflows run on fictional fixtures, documentation checks
  pass, and current help, guides and artifact descriptions agree with behavior.

### Requirement: Explicit, isolated transformation mode

The system SHALL require a distinct opt-in transformation policy and SHALL NOT
silently enable source copying in existing generation or profiling surfaces.
Implementation SHALL require reviewed safety-policy amendments and executable
tests before this proposed exception can become operational.

#### Scenario: Existing generation

- **GIVEN** a normal generation request without a transformation policy
- **WHEN** generation runs
- **THEN** existing source-free guarantees remain enforced.

#### Scenario: Trusted local operator approval

- **GIVEN** a complete reviewed transformation plan and fixed local input snapshots
- **WHEN** the operator confirms the exact plan and preserved columns through
  the interactive local CLI
- **THEN** the terminal displays every effective field action, preservation
  fallback and reviewed sensitivity status without source values, and a
  restricted receipt binds that displayed review, its classification evidence,
  the plan and input bytes; execution rejects changed policy, source, evidence
  or referenced mapping. Default MCP/agent advice cannot create a receipt.
- **AND** a caller-supplied reference or noninteractive flag alone does not
  authorize preservation; the local trust model does not claim resistance to a
  process with the same terminal and filesystem privileges as the operator.

### Requirement: Exhaustive field policy and sensitivity

Every input field SHALL have an explicit preserve, synthesize, substitute, derive or drop
action. Preservation SHALL require explicit authorization for non-sensitive
reference data. User sensitivity declarations SHALL be authoritative additions
to protection, not optional hints. AI SHALL NOT authorize declassification.

#### Scenario: New or sensitive column

- **GIVEN** an unlisted column or a sensitive field marked preserve
- **WHEN** preflight runs
- **THEN** the operation fails closed without exposing values or publishing output.

### Requirement: One-to-one correspondence

Each input row SHALL correspond to exactly one output row. Preserved logical
values and their within-row associations SHALL remain unchanged. Duplicate rows
SHALL NOT be silently removed. Output row count SHALL equal input row count.

#### Scenario: Reference context and financial facts

- **GIVEN** rows containing authorized product, segment and bank reference fields
- **WHEN** only the amount is synthesized
- **THEN** each row retains its original reference combination and row identity
  within the operation, without exporting a source-to-output lookup table.

### Requirement: Financial replacement and equality exceptions

Synthesized financial values SHALL satisfy declared magnitude, precision, sign
and null policies. Equality with the original SHALL be allowed for zeros and
coincidences after declared rounding. These exceptions SHALL NOT bypass value
generation. Other synthesized non-null values SHALL differ from the original.

#### Scenario: Rounded coincidence

- **GIVEN** an explicitly declared rounding precision
- **WHEN** a newly generated value rounds to the original amount
- **THEN** equality is accepted without claiming every amount changed.

#### Scenario: No valid replacement

- **GIVEN** a replacement domain with no permissible different value and no
  applicable equality exception
- **WHEN** transformation runs
- **THEN** it fails with a bounded policy error and publishes no partial output.

### Requirement: Explicit dependencies and consistent replacement keys

Declared key relationships SHALL use consistent local replacement mappings.
Derived values SHALL be recomputed from transformed inputs. Undeclared
relationships SHALL NOT be claimed as preserved. No dependency rule may silently
override preservation decisions or row-count invariants.

#### Scenario: Linked identifiers and derived total

- **GIVEN** linked identifier fields in the same mapping domain and a declared
  total formula over replaceable amounts
- **WHEN** transformation runs
- **THEN** matching source keys map consistently, unrelated domains remain
  distinct, and the total is calculated from transformed amounts.

### Requirement: Bounded local processing and deterministic replay

Source reads SHALL be read-only, allowlisted and budgeted. Source rows and
mapping values SHALL NOT be sent to AI providers or default MCP responses.
Replay SHALL depend on a fixed input, explicit seed, policy and algorithm
version; arbitrary SQL result order SHALL NOT be treated as stable identity.

#### Scenario: Unsupported source semantics

- **GIVEN** a SQL input without the identity/order guarantees required by its
  requested reproducibility policy
- **WHEN** preflight runs
- **THEN** it fails explicitly rather than promising deterministic correspondence.

### Requirement: Honest validation and provenance

Output SHALL identify transformed/mixed origin and authorized preservation.
It SHALL NOT claim fully synthetic or guaranteed anonymous data. Constraint
conformance, measured utility and privacy results SHALL be distinct, with
unmeasured properties explicitly reported as unmeasured.

#### Scenario: Valid constraints but unmeasured fidelity

- **GIVEN** a result satisfying declared constraints without measured statistical
  similarity or anonymity guarantees
- **WHEN** a report is produced
- **THEN** conformance may pass but fidelity is not labelled passed and retained
  reference combinations remain an explicit residual privacy consideration.

### Requirement: Safe atomic publication

All declared validations SHALL complete before output publication. Failures
SHALL preserve source data and existing output and SHALL NOT reveal raw source
values, sensitive aggregates or provider/database exception payloads.

#### Scenario: Budget or constraint failure

- **GIVEN** an exhausted work budget or inconsistent transformation rules
- **WHEN** execution cannot complete safely
- **THEN** no partial dataset is published and a bounded diagnostic identifies
  the policy or limit category without disclosing input values.
