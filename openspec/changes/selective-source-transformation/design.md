# Design: selective-source-transformation

## Approach

Separate local transformation from profile-based generation. A statistical
profile cannot reconstruct original row combinations: this mode needs bounded
access to the authorized input rows. Profiling records observations; an explicit,
reviewed transformation policy authorizes each field action.

Reuse existing deterministic generation, constraint validation and safe output
publication where their contracts fit. Do not add a parallel framework or
weaken privacy validation to make a sample pass.

## Data And Contracts

The user-editable data behavior profile SHALL expose the same per-field actions,
including substitute and its mapping reference and unmatched-value policy.
Keep observed profiling evidence separate from user-authored behavior decisions
within the versioned profile contract: observations do not grant preservation
authority. Saving/reloading a behavior profile and deriving a transformation
specification must retain these decisions without silently switching to synthesis.
The wizard and direct profile editing configure the same decisions. Unsupported
versions or conflicting profile/specification policies fail explicitly rather
than ignoring the substitution option. Exact model/schema names require design
review; do not inject these settings into existing aggregate-only profiles
without a versioned compatibility plan. A private local YAML behavior profile
may declare mapping entries inline or reference a separate local CSV mapping
file. Both forms have equivalent typed semantics. Profiles with inline source
values become restricted source-bearing inputs, not shareable aggregate profiles.
Shared/exported profiles must omit entries and use opaque references instead.

The proposed versioned policy describes:

- Input selection and schema, approved destination and work budgets.
- An explicit action for every input field: preserve, synthesize, substitute,
  derive, drop.
  Unmapped/new columns fail preflight; there is no implicit preserve wildcard.
- Explicit sensitivity/semantic declarations. Heuristics can raise conflicts;
  neither heuristics nor advisors may grant preservation authority.
- Financial magnitude/range policy, precision, sign, null handling and
  replacement-equality policy. The exact model fields are not yet API promises.
- Named key-mapping domains and explicit relationships, including composite
  keys and dependencies across approved inputs.
- Declarative formulas and validation expectations.
- Seed, algorithm/policy versions and reproducible input identity.

Preserve retains logical values and their within-row combinations, not
necessarily original CSV quoting or byte formatting. Row correspondence is
internal: do not export an original-to-replacement lookup table. CSV sequence
is retained. SQL row order is not assumed; replay requires a stable identity
or explicitly supported deterministic ordering over a fixed input snapshot.
If reproducibility cannot be established, fail the requested reproducible run.

A mapping domain provides stable replacement of the same key across linked
fields/tables. Independent domains must not accidentally share row-counter
identifiers. Mapping state remains local, bounded and excluded from reports.

## Explicit Substitution Dictionaries

A field's substitute action references a user-supplied local typed mapping
instead of a sampled generator. This is a first-class specification decision,
not a wizard-only option. The wizard edits the same versioned policy accepted
by noninteractive CLI and Python transformation entry points. Identical input
and policy must have identical semantics across those interfaces; no hidden
wizard state is required. This does not extend default MCP or profiling tools
with raw-row access. Final serialized action names remain subject to API review.

For example, map date 2025-04-30 to 2026-09-23
for all occurrences in explicitly selected reporting-date fields. This is exact
typed substitution, not substring replacement or an implicit global date shift.
Apply each mapping once to the original value; do not cascade replacement values
through other entries. Shared domains reuse the same mapping across approved
inputs; unrelated fields remain governed by their own policies.

Require an explicit policy for unmapped values: reject, synthesize, or preserve
only where preservation is independently authorized. Default to rejection.
Reject duplicate conflicting entries, type mismatches, prohibited replacement
values and collisions that violate declared uniqueness or relationship rules.
Many-to-one mappings must be explicit and compatible with declared constraints.
Null and timestamp/timezone matching require explicit semantics; a date example
does not authorize truncating timestamps. Recompute dependents after replacement
and validate date ordering, durations and all declared constraints. Fail rather
than silently shifting other dates to repair a conflict.

Mappings can contain sensitive originals and are restricted local inputs.
Allow inline YAML or a referenced CSV file; additional file formats require
explicit design rather than an arbitrary loader. External scripts and APIs are
an unapproved future TODO, not part of this candidate or an executable hook.
Reference mappings from shared specifications by an opaque policy identifier; never
embed real mapping entries in repository examples, reports, logs, provider
requests or default MCP responses. They do not override sensitivity checks or
establish anonymization. Synthetic sample mappings are suitable for docs/tests.

## Financial Values And Dependencies

Preserve approximate scale using explicit, validated rules rather than raw-value
reuse or a universal multiplier. Financial arithmetic must honor declared
precision. Sign, nulls, zero handling and acceptable magnitude tolerances must
be declared; no silent defaults may claim source fidelity.

The user permits equality for source zeros and coincidences after declared
rounding. This is not permission to copy all rounded values: the replacement
process still runs. Other synthesized non-null values must differ from their
source value. If the allowed domain makes this impossible, fail with a bounded
policy error rather than silently preserving the original.

Derive fields are recomputed from transformed inputs. Enforce declared row and
cross-row totals, balances and FK constraints. Derived values may coincide
with originals when the declared formulas require it; such equality is not
evidence of source copying. Conflicting preservation, formulas and replacement
rules fail before publication.

Keep exactly one output row per input row, including duplicate rows. Do not
silently deduplicate, scale, delete or manufacture rows to satisfy constraints.
Existing orphan references require an explicit disposition; no automatic
repair or recreation of their source frequency is promised.

## Validation And Artifacts

On 2026-09-24 the user approved explicit distinct uncertainty: capped folder
profiling reports a lower bound (“at least X%”), never an exact uniqueness claim,
and cannot automatically nominate a primary key from overflow evidence.
Uncapped measurements retain their existing six-decimal precision. Profiles
without measurement-kind metadata remain unspecified rather than retroactively
certified exact. This is separate from unchanged-source-value reporting below.

Validate row correspondence, preserved combinations, replacement policies,
types, declared key mappings, formulas and privacy boundaries.

Report separately:

1. Policy execution and schema/constraint conformance.
2. Measured utility against declared expectations.
3. Privacy checks and residual risks of permitted preserved data.

Unmeasured utility is not a pass. Reports contain policy references, action
counts and safe aggregate outcomes, not source samples, sensitive extrema,
identifier mappings or original/replacement pairs. Sensitive aggregates also
require disclosure controls; do not assume aggregation alone is safe.

Output provenance must state transformed/mixed origin and which fields were
authorized for preservation. Do not emit the existing unconditional claims
that all output is synthetic or that no source rows/values were copied.
A restricted output is not automatically safe for redistribution.

### Unchanged Source Values Percentage (Approved Requirement)

The user approved a transformation-report indicator on 2026-09-24:
“Сохранено исходных значений: X%” (source values left unchanged).
This measures actual unchanged values at corresponding input/output positions,
not the percentage of fields configured with the preserve action, uniqueness,
utility, or privacy assurance. Report the comparison scope and denominator;
do not claim a measured percentage when no comparison was performed.
The executable contract must define typed equality, nulls, dropped/derived
fields and empty inputs before implementation and acceptance.

Expose only permitted aggregate results, never source values or comparison
pairs. Existing aggregate disclosure controls still apply; a withheld or
unavailable result must not be rendered as 0%. This requirement grants no
preservation authority and does not change source-free generation or resolve
the separate capped-distinct uncertainty decision. Runtime reporting remains
unimplemented.

## Failure Modes

Reject incomplete field policies, schema drift, sensitivity conflicts,
unsupported formulas/SQL, missing key mappings, inconsistent constraints,
unsafe paths and exhausted budgets. Publish atomically only after validation;
leave existing output and source data intact on failure. No raw exception
chains, SQL literals or source values in user-facing errors.

Database adapters remain read-only. Temporary-table writes/materialization
are not authorized by this proposal. A raw-row read surface for transformation
needs a separately reviewed bounded adapter path; aggregate-only tools and
default MCP tools must not acquire this capability implicitly.

## Alternatives

- Fully synthetic generation remains useful but cannot preserve source row
  combinations from aggregates alone.
- Independent category sampling loses code/name/segment correspondence.
- Preserving every unspecified field is unsafe under schema drift.
- Blanket numeric declassification misses numeric identifiers and secrets.
- AI is optional: it proposes rules from permitted metadata, never authorizes
  copying or enforces correctness.

## Implementation Gate Decisions

Before runtime work, settle the explicit safety-policy amendment, versioned
contract and CLI surface, SQL snapshot/order semantics, key-mapping lifecycle,
financial tolerance configuration and safe utility-report disclosure.
These are implementation decisions, not claims of existing support.

### Approved repeated-key cardinality (2026-09-24)

For source-free generation, an observed repeated identifier cardinality defines
a fixed synthetic pool, not a ratio scaled with output rows. Four keys remain
four when generating more rows. Carry only the count, never identifier literals
or source-to-output row mappings. `synthetic_identifier.pool_size` is an optional
positive integer; omission retains the existing per-row behavior. Censored CSV
counts and overflowing folder trackers must not nominate a pool or primary key.
Nulls and undersized output may leave pool members unused; declared relationships
remain authoritative. Aggregate estimates define a requested pool, not an exact
source-fidelity claim. This does not enable the source-preserving transformation
path or resolve its separate approval-authority gate.
