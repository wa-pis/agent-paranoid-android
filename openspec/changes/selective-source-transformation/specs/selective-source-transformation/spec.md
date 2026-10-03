# Selective Source Transformation Specification Delta

Proposed capability only; no existing guarantee is modified by this document.

## ADDED Requirements

### Requirement: Synthetic Identifier Privacy Agreement

Source-free string identifier generation and post-solve privacy validation SHALL
agree on the existing `synthetic_` plus ASCII integer token namespace, including
fields annotated with email, phone or SSN semantics. This recognition SHALL apply
only to identifier fields, SHALL NOT accept arbitrary prefixed sensitive text,
and SHALL NOT permit source-row reuse or broaden ordinary sensitive field formats.

#### Scenario: Sensitive semantic identifier uses a bounded synthetic pool

- **GIVEN** a string identifier with sensitive semantics and an explicit pool size
- **WHEN** seeded source-free generation creates repeated keys
- **THEN** exact synthetic identifier tokens pass privacy validation reproducibly
- **AND** arbitrary prefixed sensitive text fails privacy validation
- **AND** non-identifier fields retain semantic synthetic-format checks

### Requirement: Explicit runtime Trino authentication
The candidate SHALL compose driver-supported Basic, JWT, Kerberos, GSSAPI,
OAuth2 and Certificate authentication through the shared bounded Trino client.
Secrets SHALL be runtime-only, outside saved profiles, URLs and logs.
Authenticated connections SHALL use verified HTTPS. Missing requirements and
configuration conflicts SHALL reject before connection with value-free errors.
OAuth2 SHALL NOT use the driver's default console URL disclosure handler.
The candidate CLI browser route SHALL require explicit opt-in and a local
interactive terminal. MCP SHALL NOT install this callback. Browser redirects
and direct token-adapter requests SHALL be restricted to the configured HTTPS
Trino origin without printing authentication URLs. Existing invocation budgets
SHALL apply to token requests and before/after redirect callbacks.

#### Scenario: Noninteractive browser authentication
- **WHEN** the explicit OAuth2 browser flag is invoked through a pipe
- **THEN** the CLI rejects before connecting or publishing a profile

#### Scenario: Token server attempts a different origin
- **WHEN** the driver's direct adapter send targets another host, port or HTTP
- **THEN** the shared adapter rejects before network I/O with a value-free error

#### Scenario: Missing JWT and safe driver failure
- **WHEN** a JWT runtime secret is missing or authentication construction fails
- **THEN** no database connection is attempted and no secret or backend error
  is exposed in the detached user-facing error

### Requirement: Honest bounded Parquet profile evidence
Parquet profiles SHALL retain unknown null and distinctness statistics as null,
not measured zero. Unknown distinctness SHALL NOT establish a primary key or
relationship confidence. Automatic generation-spec inference SHALL reject unknown null ratios.
Local sensitivity inspection SHALL remain byte/cell/time bounded, retain no
source values and reject exhaustion instead of publishing a partial profile.

#### Scenario: Missing statistics and sensitive neutral column
- **WHEN** a fictional Parquet input has no null statistics or sensitive content
  in a neutral-named column
- **THEN** unknown null ratios remain null and sensitive content is flagged
- **AND** no input value appears in the serialized profile

### Requirement: Honest generation validation exit parity
All generation CLI entrances SHALL preserve supported deliberately invalid
output and its report while returning exit code 1 and JSON status
`validation_failed` whenever validation fails. Generation mode SHALL NOT
override validation status, and privacy failures SHALL still prevent publication.

#### Scenario: Mixed mode across input entrances
- **WHEN** fictional mixed-mode generation from spec, profile or CSV produces
  a failed validation report
- **THEN** the supported result and report remain published
- **AND** every entrance returns exit 1 and JSON status `validation_failed`

### Requirement: Read-only transformation review parity

CLI and generator MCP SHALL prepare the same value-free review and exact-byte
snapshot identity for a saved local behavior policy and supported source
snapshot. MCP SHALL enforce workspace paths and existing input, review and
transport budgets, write no artifacts and mint no approval receipt.

#### Scenario: Agent reviews a saved policy

- **GIVEN** a fictional source snapshot and saved policy inside the workspace
- **WHEN** `review_transformation` is called
- **THEN** its review and snapshot digest equal CLI `transform-review`
- **AND** no source/mapping values, database access, execution or approval occur

#### Scenario: A review path escapes the workspace

- **WHEN** source or policy paths resolve outside the configured workspace
- **THEN** the tool rejects before reading those files
- **AND** public transformation execution remains gated

### Requirement: Configurable capacity and actionable limit failures

Transformation SHALL support a configured target workload of 1,000,000 rows
and 100 columns, with mandatory fictional end-to-end acceptance at 300,000 rows
and 50 columns. Byte, value-width and time budgets SHALL remain explicit and
independently enforced; capacity SHALL NOT imply arbitrary-width or unbounded
inputs. Aggregate-only profiling disclosure budgets SHALL remain separate.

Resource limits SHALL be configurable for a run/session and a saved profile,
with documented keys, ranges and deterministic precedence. Limit failures SHALL
distinguish a request above the configured threshold from an observed runtime
exceedance, disclose safe dimension/amount/limit/units and effective setting
origin, and explain concrete supported session and saved-profile configuration.
Errors SHALL remain value-free across core, worker, CLI/Python/MCP boundaries.

#### Scenario: Private query capture limit crosses the worker boundary

- **GIVEN** a fictional authorized PostgreSQL result and explicit transformation
  limits independent of aggregate-profiling disclosure budgets
- **WHEN** capture exceeds a configured dimension in the isolated worker
- **THEN** the parent receives only validated dimension/count/threshold/origin
  diagnostics after worker cleanup, without backend text or partial output
- **AND** changing the documented session or saved-profile setting permits a
  subsequent in-budget capture, review and temporary publication without
  changing source-free profiling budgets or activating public execution.

#### Scenario: Requested capacity exceeds configured budget

- **GIVEN** a requested workload above an effective configured limit
- **WHEN** preflight validates the request
- **THEN** it rejects before avoidable source work with requested amount, limit,
  units, setting origin and supported session/profile recovery instructions
- **AND** it neither increases the limit nor silently truncates the workload.

#### Scenario: Common profile source exceeds its file ceiling

- **GIVEN** a fictional regular source file inside the authorized root, with
  size above its effective behavior-policy file-byte ceiling but below the
  remaining common aggregate byte budget
- **WHEN** common profile loading or local profile creation captures that source
- **THEN** descriptor size is checked against the file ceiling before reading
- **AND** the observed-limit error retains dimension, amount, threshold and
  setting origin, without publishing a partial result or increasing limits.

#### Scenario: Processing reaches a configured limit

- **GIVEN** a transformation total snapshot budget configured through
  `resource_limits.max_total_input_bytes` or
  `TEST_DATA_AGENT_TRANSFORM_MAX_TOTAL_INPUT_BYTES`
- **WHEN** policy, references, source, classification evidence and displayed
  review consume that budget, including an exact-zero remainder before a read
- **THEN** preparation and receipt revalidation preserve a value-free typed
  limit diagnostic with amount, threshold, bytes, effective origin and recovery
  settings, without publishing output or truncating inputs
- **AND** read-only CLI/MCP review uses the same effective ceiling rather than
  silently requesting a fixed default as a run override.

#### Scenario: Explicit snapshot run cap

- **GIVEN** an explicitly supplied transformation snapshot run cap
- **WHEN** it exceeds the configured session/profile ceiling
- **THEN** preparation rejects it as `requested_above_limit`
- **AND** a smaller admitted run cap is enforced cumulatively with
  `snapshot_run` diagnostics, without granting preservation authority or
  increasing source-free profiling/transport disclosure budgets.

#### Scenario: Processing reaches a configured runtime limit

- **GIVEN** an admitted workload whose observed consumption exceeds a limit
- **WHEN** processing detects the excess
- **THEN** it stops without partial publication and reports observed amount,
  limit, units and supported session/profile configuration instructions
- **AND** no source values, SQL literals or backend diagnostics are exposed.

#### Scenario: Configured scale acceptance

- **GIVEN** a fictional 300,000-row, 50-column workload and sufficient explicitly
  configured byte/time budgets within the supported target
- **WHEN** the end-to-end transformation runs through the actual interfaces
- **THEN** all rows/columns required by the policy are handled without truncation,
  configured limits remain enforced and measured resource evidence is recorded.

### Requirement: Report executed cell provenance

Transformation reporting SHALL classify output cells as replacement, synthetic,
or original according to the actual executed action, independently of equality
with source values. It SHALL disclose only aggregate counts and proportions.
Dropped cells SHALL be counted separately and excluded from the denominator.
An empty output-cell scope SHALL have unavailable proportions, not zero percent.
This reporting SHALL NOT weaken independent sensitive-data or source-copy guards.

#### Scenario: Actual fallback determines origin
- **WHEN** an unmatched mapping preserves or generates a value
- **THEN** its origin is original or synthetic respectively, while a matched
  replacement remains replacement even when its result equals the input.

#### Scenario: Explicit formatting and physical serialization
- **WHEN** explicit type or format transformation is applied to original data
- **THEN** origin is replacement; formatting generated data retains synthetic
  origin, and physical file encoding or quoting alone does not change origin.

#### Scenario: Null and dropped cells
- **WHEN** a rule replaces a cell with null or empty text
- **THEN** it is replacement; an untouched null is original, and dropped cells
  have no output origin and do not contribute to output-cell proportions.

### Requirement: Input and output formats are independent

The transformation system SHALL support CSV and Parquet file inputs and
separately authorized bounded read-only Trino or PostgreSQL query-result
inputs. Each input SHALL independently support CSV, Parquet and SQL-script
file outputs through shared transformation and validation semantics. Adapters
SHALL own physical encodings while the common core owns field policy and
logical types. Approval SHALL bind the captured source and selected output
settings as well as the policy and mappings. SQL outputs SHALL NOT execute
database writes. SQL-file input is outside this requirement.

#### Scenario: Cross-format transformation

- **GIVEN** a fictional authorized input snapshot and reviewed field policy
- **WHEN** any of the four input kinds selects any of the three output kinds
- **THEN** the same one-to-one field rules and logical validation apply,
  independent of physical encoding, and failed validation publishes no output.
- **AND** null/empty, exact decimal and explicit temporal semantics survive
  supported adapter readback without implicit type coercion.

#### Scenario: Database query result exported as a script

- **GIVEN** an authorized bounded read-only Trino or PostgreSQL result snapshot
- **WHEN** SQL-script output is selected
- **THEN** the system creates a script file using its declared dialect and safe
  literal/identifier encoding, never executes it, and preserves source access
  allowlists, budgets and sensitivity gates.

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

#### Scenario: Intentionally invalid values cannot enter typed Parquet

- **GIVEN** mixed or negative generation produces a value incompatible with a
  declared Parquet field type, even after another entity has been staged
- **WHEN** the dataset is exported
- **THEN** the entire export fails without a partial dataset or manifest, and
  any previously published output remains unchanged.

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

#### Scenario: Substitution cannot disguise preservation

- **GIVEN** an inline, local CSV, or shared-domain mapping whose replacement
  would retain a non-null original value in a field
- **WHEN** the exact mapping and policy are validated before approval or execution
- **THEN** validation rejects the mapping without reporting either value;
  naming the action `substitute` does not grant preservation authority, even
  for a field otherwise eligible for explicit preservation.

### Requirement: Exact-text CSV replacement scopes

The separate `replace_text` action SHALL support an exact-text CSV table for
the whole single-file policy and optional tables for individual columns at
the same time. Matching SHALL use original decoded cell text once, without
type inference, coercion, trimming or cascade. File-wide rules SHALL apply
only to fields explicitly assigned `replace_text`, not override other field
actions. An unmapped cell SHALL fail unless a separately authorized fallback
is declared. A matching column key SHALL take precedence over a matching
file-wide key; otherwise the file-wide match, then declared fallback SHALL
apply. Duplicate keys within one table SHALL fail. Local trace SHALL be bounded
and value-free and report the same selected rule as execution.

#### Scenario: Column override does not cascade

- **GIVEN** fictional rules `a → b` file-wide and `a → c` for one column,
  and an additional file-wide `c → d` rule
- **WHEN** the original cell in that column is `a`
- **THEN** the result is `c`, not `b` or `d`, using the column rule once.
- **AND** another `replace_text` column without that override uses `b`.

#### Scenario: Combined global and column rules

- **GIVEN** a file-wide `true → false` rule and a distinct column-scoped
  `001 → 1` rule on a fictional CSV
- **WHEN** a reviewed transformation is evaluated
- **THEN** both scopes are considered in one pass over original cell text,
  unchanged input is not silently copied and no replacement is cascaded.
- **AND** local debugging reports only row/column/scope/rule ordinals, match
  status and bounded counts, never either literal or its hash.

#### Scenario: One mapping contract regardless of sensitivity

- **GIVEN** a sensitive field and a reachable replacement equal to an original
  value in a sensitive or unresolved field of the same fixed CSV snapshot
- **WHEN** local review or receipt verification runs for explicit replacement
- **THEN** source membership alone SHALL NOT reject the mapping, including an
  explicit permutation of sensitive values.
- **AND** effective sensitivity SHALL remain a value-free field note.
- **AND** direct preserve and preserve fallback SHALL retain their existing
  non-sensitive classification and local human receipt requirements.

#### Scenario: Explicit mapping versus synthesis at output normalization

- **GIVEN** fictional email-shaped explicit replacements and cells without an
  actually applied mapping
- **WHEN** CSV, SQL-script or Parquet output is encoded
- **THEN** only actually mapped cells use the uniform replacement contract.
- **AND** synthesis, derive and preservation retain their existing content
  checks; absent or malformed execution evidence SHALL NOT grant an exception.
- **AND** type, null, snapshot, budget and value-free transport checks remain.

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

### Requirement: Skill-guided agent use is version-accurate

For the release candidate, an agent integration SHALL be able to locate both
packaged project skills without network access, use installed command/tool
metadata to select an interface supported by that version, and produce a
bounded, value-free plan before any state-changing operation. Loading a skill
SHALL NOT register it automatically
in every agent runtime, activate an unfinished transformation path, grant data
preservation authority, or bypass existing review and approval boundaries.

#### Scenario: Installed package lacks transformation execution

- **GIVEN** an installed package containing both skills but no approved
  transformation execution interface
- **WHEN** an agent is asked to preserve source values
- **THEN** it reports that execution is unavailable and routes to the current
  review/specification workflow without copying values or inventing approval.

#### Scenario: Supported synthetic workflow

- **GIVEN** a fictional source and an installed version with documented
  source-free generation commands
- **WHEN** the agent chooses a workflow using the packaged skill
- **THEN** it proposes only supported profiling, review and generation steps,
  using existing CLI/Python/MCP permissions and value-free responses.

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

Every input field SHALL have an explicit preserve, synthesize, substitute,
replace_text, derive or drop
action. Preservation SHALL require explicit authorization for non-sensitive
reference data. User sensitivity declarations SHALL be authoritative additions
to protection, not optional hints. `sensitive: false` SHALL mean an explicit
per-column human non-sensitive decision, never an automatic interpretation of
no detector finding or a default profile value. Missing or uncertain evidence
remains unknown; positive sensitivity evidence or a conflict fails closed for
preservation. AI SHALL NOT authorize declassification. Even an explicit
non-sensitive decision does not itself authorize preservation: the exact plan
and preserved columns still require separate local interactive confirmation.

#### Scenario: No sensitivity finding is not a non-sensitive decision

- **GIVEN** a field with no positive detector finding or a profile default of
  `sensitive: false`, but no explicit human decision for that field
- **WHEN** preservation is requested
- **THEN** preflight rejects it as unresolved without exposing source values.

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
SQL aggregate columns SHALL be ordinary query-result fields, without internal
formula translation or total recomputation. Undeclared
relationships SHALL NOT be claimed as preserved. No dependency rule may silently
override preservation decisions or row-count invariants.

#### Scenario: Linked identifiers and SQL aggregate result

- **GIVEN** linked identifier fields in the same mapping domain and an aggregate
  column already computed by an authorized bounded SQL query
- **WHEN** transformation runs
- **THEN** matching source keys map consistently, unrelated domains remain
  distinct, and the aggregate column follows its explicit field action without
  internal formula evaluation or recalculation from transformed amounts.

### Requirement: Honest SQL-expression inference capability

Automatic specification inference SHALL reject query profiles with unmodeled
expression dependencies or missing dependency capability metadata.

#### Scenario: Unsupported SQL-expression generation dependency

- **GIVEN** a query profile with a source-dependent expression whose dependency
  is not modeled for generation
- **WHEN** automatic dataset specification inference is requested
- **THEN** inference rejects with a fixed value-free diagnostic, while authorized
  query profiling remains available and no expression text is persisted
- **AND** legacy SQL profiles missing dependency capability metadata require
  reprofiling; non-query legacy profiles retain their inference behavior.

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
