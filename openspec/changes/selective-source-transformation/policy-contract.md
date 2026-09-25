# Behavior Policy Contract — Review Draft

Internal execution design with a read-only local CLI review step; not permission
to execute source-preserving transformations. Existing DatasetProfile/DatasetSpec
schemas and source-free generation remain unchanged.

## Separate Evidence And Decisions

A versioned private behavior policy references a source schema fingerprint and
contains one explicit decision per `(entity, field)`. Profiling observations
remain evidence, not mutable declarations of permission. Duplicate decisions,
unknown fields, missing fields and schema drift fail preflight. Postponed wizard
decisions are incomplete and cannot produce an executable specification.
Each field's review evidence includes a bounded system comment describing its
likely data meaning and the basis/uncertainty of the sensitivity suggestion.
The comment is value-free and advisory; it cannot supply a missing user
decision. In particular, a profile's default `sensitive=false` is not a
reviewed non-sensitive declaration or preservation authority. Only a person's
explicit per-field `sensitive=false` decision records non-sensitive status;
absence of a finding remains unknown. Positive evidence or a conflicting
classification still blocks preservation rather than being silently overridden.
Every direct or unmatched-value preserve action also requires a separate,
bounded operator comment explaining the requested retention. This private
comment is not an authorization reference and is never copied into the
value-free review, logs or transport errors. Exact policy bytes, including
the comment, are bound to the approval snapshot; changing it invalidates the
receipt. A comment alone cannot override positive sensitivity evidence or
enable execution. The displayed system comment and final sensitivity decision
are bound with classification evidence
to the local approval snapshot; changes require renewed review.
The private value-free review renders a positive metadata/profile signal as
`observed_sensitivity=sensitive` and no positive signal as `unknown`, never as
observed non-sensitive. Its comment uses fixed phrases derived from bounded
metadata; arbitrary semantic labels and source values are not echoed. This
review projection does not yet create the versioned behavior profile or wizard.

The shared core parses and validates decisions without reading a source, opening
a mapping file, executing a formula or generating data. CLI, wizard and agent
adapters must use this same core rather than independently interpreting YAML.
Parsing a valid policy is not approval to execute it.

## Action Variants

Use a discriminated union rather than a bag of optional, ignored settings:

| Action | Required configuration | Reject |
| --- | --- | --- |
| preserve | Explicit user authorization, non-sensitive declaration and bounded operator comment | Mapping, generator or formula settings; unresolved sensitivity conflict |
| synthesize | Reviewed generation policy reference | Preservation or mapping settings |
| substitute | Exactly one inline mapping, local CSV reference or named domain reference; unmatched policy | Generator settings unless unmatched synthesis is explicitly configured |
| replace_text | A file-wide exact-text CSV table and/or a field-scoped exact-text CSV table; unmatched policy defaults to reject | No table, inline/domain mapping, implicit type conversion or copying unmatched cells |
| derive | Supported formula and declared dependencies | Mapping or preservation settings |
| drop | No execution settings | Mapping, formula or generator settings |

Names here describe semantics; serialized model names/version identifiers remain
subject to independent design review. No wildcard preserve action. Unknown
configuration keys and unknown versions are errors, not silently ignored input.
Sensitive preservation cannot be authorized by an agent. A declaration alone
does not override detected sensitivity or represent privacy certification.

## Private Mapping Representation

Inline mappings are lists of typed source/replacement pairs, not YAML object
keys: object keys can conflate `true`, `1` and strings during parsing. CSV
references name source/replacement columns and use the field's declared type.
Both inputs normalize through one type-aware validator. Duplicate source keys
are rejected, including duplicates with identical replacements; ambiguous
configuration is not resolved by first/last-wins ordering.

The first executable CSV replacement primitive is a separate exact-text table:
each decoded source CSV cell is matched to a literal left-hand cell and, on a
match, replaced with the literal right-hand cell. `true -> false` and
`001 -> 1` mean text substitution, not Boolean or numeric conversion. No
trim, case fold, type inference, cascade or brute-force lookup is involved.
Duplicate left-hand strings reject. This primitive does not by itself grant
permission to retain unmatched source values; reviewed per-field actions and
the local approval/snapshot boundary still apply. The owner requires both
file-wide and per-column tables. The private policy declares one optional
file-wide CSV table plus an optional CSV table on each `replace_text` field
decision; at least one must apply to every such decision. A file-wide table is
valid only for a single-entity CSV policy, so it cannot silently span multiple
files. A column-scoped rule
applies only to its declared column; a file-wide rule applies to every
`replace_text` column in that file, not to columns with other actions. Both
levels remain subject to field decisions and sensitivity/preservation gates.
The owner-approved target precedence is a matching per-column key first, then
a file-wide match, then the declared unmatched policy. Match the original cell
once; never feed replacement text into another rule. Duplicate keys within a
single table still reject. Matcher, private approval-material preflight and
value-free trace support this precedence; public output execution remains
unavailable. The value-free review reports whether file and
column rules are configured, without showing their literals. No cascade or
implicit two-step replacement is permitted.
For a field declared sensitive or unknown, or with positive sensitivity
evidence, local CSV review and receipt verification check only replacements
reachable from the fixed source bytes. A reachable right-hand literal must
not equal an original value in any sensitive/unknown column of that same
snapshot. This comparison uses the same CSV decoding/dialect as profiling,
does not persist raw source values, and fails with a value-free error. An
explicitly reviewed non-sensitive column is not blanket-banned from ordinary
text substitutions, though execution still needs its separate safety gate.

Debugging is local and opt-in. A bounded dry-run/trace may report source row
ordinal, column ordinal, rule scope (file or column), mapping-rule ordinal
and matched/unmatched outcome,
plus per-rule counts. It must not include source/replacement literals, hashes
of them, raw row fragments or unbounded event output; default agent/MCP
summaries remain aggregate and value-free. Trace generation and ordinary
execution must share the same matching code and fixed input snapshot.

Null is distinct from empty string. Exact decimal values are text plus declared
precision/scale; never parse them through binary float. Dates and timestamps are
distinct types; no implicit timezone conversion or timestamp truncation. Actual
CSV null tokens, encoding and timezone policy must be explicit before execution.

Unmatched values default to rejection. Explicit preserve fallback requires the
same permission as preserve action; synthesis fallback requires its own complete
generation policy. Apply the mapping once, never cascade replacement values.
Uniqueness and relationship constraints decide whether an explicitly declared
many-to-one map is compatible; no automatic key-collision repair.

Mapping loaders must reuse bounded local-file/path controls. External scripts,
network URLs and API callbacks are unsupported, not dynamically loadable hooks.
Inline policies and mapping files are restricted inputs. General logging, model
repr, validation exception chains and machine-readable errors must not expose
their contents. Safe summaries contain action counts and opaque references only.
Private save/load must preserve mappings; public summaries must omit entries.

## Shared Domains And Relationships

Named mapping domains own exactly one concrete inline or local CSV mapping
definition; domain-to-domain indirection is not supported. Linked field decisions
reference that domain rather than duplicating independent dictionaries. Domain
members declare input/entity/field identity and compatible types; composite keys
declare ordered field tuples and map the whole tuple, not each part independently.
Relationship declarations bind parent and child tuples to compatible domains.
Reject conflicting domain definitions, incompatible membership/types, ambiguous
tuple ordering and uniqueness-breaking mappings before execution. Domain state
is local, bounded and private; independent runs share it only by explicit policy.

In the private draft preflight, each field's domain reference carries an
explicit zero-based `component` for a composite key. Every entity using that
domain must bind exactly one field to every component in the mapping tuple;
missing, duplicate or out-of-range positions fail. Scalar domains may omit
the component. Field types must agree across entities sharing a domain, and
every component is typed against its own field before approval material is
prepared. The value-free review shows an opaque domain ordinal and component
position, never private domain names or mapping entries. This establishes only
ordered field binding; relationship execution and full composite-key
validation remain pending.

## Replacement Semantics

Owner-approved synthesis payload: `generation_policy_ref` identifies a bounded
local DatasetSpec 1.1 document, not a new generation format. Its exact bytes are
part of the reviewed snapshot as `generation_policy`; execution must consume
those bytes, never reopen an unbound path. Reuse DatasetSpec validation and the
existing deterministic generation contract. Referenced entity/field identity
and output type must agree with the transformation policy. The transformation
seed and one-to-one row count govern execution, not an unrelated requested
dataset size. This does not enable source-value reuse or public execution.

Owner-approved DECIMAL formula rounding is ROUND_HALF_UP at declared scale;
precision overflow rejects. Exact arithmetic must not pass through binary
FLOAT. Tests and implementation of this contract remain required.

The private exact row-formula evaluator reuses the bounded arithmetic syntax
parser and evaluates decimal literal text and integer/Decimal operands as
rational numbers, rounding only the final result. It rejects aggregate calls,
missing/null/bool/float operands and division by zero. Resource limits are 1024
literal coefficient digits/exponent magnitude and 16384 bits for intermediate
numerators/denominators, alongside the existing expression and runtime budgets.
This helper alone does not activate derive or settle nullable formula semantics.

The Financial Values And Dependencies section of design.md is normative for
synthesis and unmatched-value synthesis fallback: declared magnitude/range,
sign, null, zero, precision/scale, rounding and overflow rules must all apply.
Binary float conversion cannot establish exact financial precision. Prohibited
replacement values remain prohibited in inline, CSV and synthesized outputs.
For canonical offset-aware DATETIME mapping values, different text denoting the
same instant is also an identity replacement and is rejected. This does not
convert timezones or define the execution timezone policy.
Non-null synthesized values must differ from originals except the approved zero
and declared-rounding coincidences; those exceptions never skip generation or
authorize wholesale copying. Derived totals must be recomputed and validated.
If no permissible replacement satisfies the policy and constraints, fail with a
bounded value-free error rather than retaining the input or relaxing constraints.

## Closed CSV Execution Development Status

The private `trace_csv_replacements` dry-run binds to the same canonical request
and source snapshot as execution and uses `match_scoped_text` for identical rule
precedence. It reports only replace-text actions, with original source row/column
ordinals, rule scope/ordinal and aggregate counts. Event display truncates at an
explicit limit; total traced cells and distinct rule counters have rejecting
limits. Unmatched rules are reported without executing fallback actions. Dropped
columns do not renumber source ordinals. No cells, mappings, receipt or output
dataset are returned; this is not a public CLI/MCP surface or an execution approval.

The private `io/transformation_execute.py` prototype supports `replace_text`,
`drop`, `preserve` and unmatched-preserve. It is not connected to public
CLI/Python/MCP execution and is not release acceptance. Direct non-null STRING/INTEGER/FLOAT/DATE
`substitute` pairs support inline/CSV mappings with reject-on-unmatched or
receipt-bound preserve fallback.
Single-file non-null STRING/INTEGER/FLOAT/DATE domains match complete ordered original tuples,
using the preflight-validated component positions, independent of policy order.
INTEGER keys use strict ASCII signed decimal parsing, with no float intermediate;
CSV mappings reuse typed normalization and replacements use decimal integer text.
FLOAT uses the existing approximate numeric contract and the same ASCII
decimal/exponent parser for source keys and CSV mappings; non-finite values,
overflow and nonzero underflow to zero reject. It is not exact DECIMAL arithmetic.
DATE matches canonical ISO text without conversion. DATETIME remains closed
pending the explicit execution-timezone/equivalence contract below.
Direct `synthesize` and synthesis fallback for substitute/replace_text reuse
the existing generator with bound DatasetSpec 1.1, policy seed and source row
count. Each reference is generated once; final transformed projections are
validated against its spec regardless of optional reporting settings. Current
execution requires one matching entity, valid mode and non-null generated
cells. Unchanged generated text rejects; numeric coincidence exceptions remain
unfinished. Approximate FLOAT `derive` executes in dependency order using
transformed INTEGER/FLOAT inputs, not original cells. Only finite numeric
literals are allowed; arithmetic/nonfinite results reject, and CSV column
order is preserved. INTEGER derive uses the shared exact rational evaluator
with INTEGER dependencies, rejects fractional final results and never rounds
through float. DECIMAL derive result integration remains pending.
Cross-input relationships and other typed substitutions remain unsupported;
they fail rather than silently
falling back to another action. Final independent implementation review and
activation gates still apply.

Execution consumes revalidated fixed input bytes, never reopened source paths.
Preservation requires the existing local receipt verifier, including exact-byte
binding and owner-only regular-file checks; a policy authorization reference
alone is insufficient. The engine does not mint receipts. Whole-row copying
and recognizable sensitive output remain rejected.

The private result carries restricted UTF-8 comma CSV bytes (omitted from repr)
and a value-free retention summary. Input decoding/dialect is shared with
profiling; output columns follow source order minus drops, and row order is
unchanged. Retention compares corresponding output cells, excludes dropped
cells, and reports unavailable for an empty comparison scope. The percentage
does not authorize preservation or certify anonymity. No filesystem publication
or mixed-origin manifest is implemented by this in-memory prototype.

## Approval Identity Binding

A schema fingerprint detects structural drift, not changes to source contents.
Approval must bind the reviewed behavior policy and immutable identities of the
source snapshot, referenced CSV mappings and referenced generation policies,
including transitively referenced policy inputs. Paths and opaque names alone
are insufficient. Execution must verify those identities and consume the same
bounded snapshot/bytes that were verified, preventing check-then-reopen races.
Any changed or unverifiable input invalidates approval. Database inputs require
an explicitly supported fixed-snapshot/replay contract; a schema or query hash
alone cannot prove unchanged rows. Identity evidence itself remains restricted
where it could reveal source-derived information. Runtime approval/snapshot
implementation is deferred, not this requirement.

## Validation Layers And Tests

1. Structural parsing: reject unknown versions/actions/keys, conflicting action
   settings, duplicate field decisions and multiple/missing mapping sources.
   A substitute action selects one of inline, CSV or domain reference; each
   domain definition selects one concrete inline or CSV source.
2. Schema binding: require every field decision, matching types and exact source
   identity; do not infer authorization from evidence.
3. Semantic preflight: check sensitivity, mapping types/duplicates, null policy,
   dependency cycles, financial precision, declared uniqueness and budgets.
4. Execution approval: trusted local operator sees all effective field actions,
   preservation fallbacks and value-free sensitivity/conflict status before
   confirming the exact reviewed plan in an interactive CLI. A restricted
   receipt binds that display, its classification evidence, reviewed policy
   and fixed source/mapping identities. Mutation invalidates approval. Default
   MCP and agent advice cannot create the receipt. The
   selected local trust model does not resist equal-privilege impersonation;
   implementation and independent safety review remain pending.
5. Post-execution validation: one-to-one rows, source-free fields, permitted
   preserved combinations, formulas and privacy; publish atomically only on pass.

Initial implementation tests should exercise layers 1–2 without file reads or
generation, plus private round-trip and redacted failure behavior. Do not mark
layers 3–5 implemented merely because a policy parses or serializes successfully.

## First Internal Implementation Slice

`core/transformation_mapping.py` only parses inline scalar tuples, CSV-reference
declarations and named-domain references. It is not a behavior profile, loader,
schema-bound mapping validator or execution API. Its bounded fixed error detaches
Pydantic validation errors; repr omits private entries and references. Model dumps
are explicitly private round-trip payloads, never public summaries. Even existing
model instances are revalidated at the parsing boundary.

Collection ceilings reuse existing input row/column defaults. Total byte/cell
budgets, configured per-invocation limits, scalar lengths, CSV path authorization,
column uniqueness/tuple arity, typed normalization, duplicate-key checking,
domain resolution and approval are still preflight/loader work. Do not expose
this structural parser as a completed safety boundary or claim executable support.

The next internal slice, `core/transformation_policy.py`, adds draft version
`0.1`, field-action declarations, unmatched-value policy and concrete named
domains. It rejects duplicate decisions/domains and unresolved domain references.
Preservation declarations require an explicit non-sensitive classification and
an authorization reference; neither the classification nor the reference is
verified authorization. The schema fingerprint is structurally checked only.
No schema binding, source access, expression evaluation or transformation occurs.
These models remain private draft structures, not a supported public API.

`validate_policy_field_coverage` checks the exact `(entity, field)` set against
an existing `DatasetProfile`, reparsing mutable nested profile contents and policy
instances. Duplicate, missing and unknown fields fail with a fixed detached error.
It also checks declared derive dependencies as exact field names within the same
entity: missing, dropped, repeated or cyclic dependencies fail. Cross-entity
dependency syntax is not implemented. Expression/declaration agreement uses
the shared bounded arithmetic parser (1024 characters, 128 AST nodes): the
exact set of ordinary field references must equal the declared dependencies,
and aggregate calls are rejected for this row-local action. Bare `sum`/`count`
column names remain field references rather than implicit function calls.
Malformed or unsupported expressions return a value-free detached policy error.
No expression is evaluated by this check; result types, null semantics and
financial rounding still require executable formula validation.
Observed `sensitive` fields, sensitive names and sensitive semantic types cannot
use preservation or unmatched-preserve, even when the decision declares them
non-sensitive. The value-free review reports this effective sensitivity, not
only the profile's boolean flag. This check does not authenticate
the supplied profile, resolve heuristic conflicts or grant preservation authority.
This is only part of schema binding: it does not verify the fingerprint, types
or authorization.
It neither reads source data nor returns an executable/approved policy.

`validate_policy_profile` additionally compares `schema_fingerprint` with
`transformation_schema_fingerprint`: SHA-256 of canonical UTF-8 JSON containing
version `0.1`, ordered entity names, and ordered field names/types/nullability.
Changing column order or type invalidates this binding; changing row counts or
observed distributions does not. This is column-schema identity only: constraints,
relationships, sensitivity evidence and source contents are not covered by that
hash and must be bound separately in execution approval. Mapping value types,
formula semantics and referenced generation-policy validation remain pending.

The private `render_policy_review` helper validates coverage and schema, then
renders every effective action, unmatched behavior and declared/observed
sensitivity status as bounded ASCII JSON. It excludes mapping values,
authorization references and expression literals; escaped identifiers cannot
inject terminal control lines. This is review material, not approval. The
private `snapshot_identity` helper hashes exact bounded review, policy,
classification-evidence, source and optional mapping/generation-policy bytes
under distinct labels. A changed part invalidates the identity. Callers still
must prove the snapshots were loaded safely and consume the same bytes at
execution; neither helper creates a receipt or enables preservation.

Private approval-material preparation parses bounded policy/profile bytes,
builds that value-free review and requires exact external CSV mapping and
generation-policy references before binding source bytes. The separate local
receipt helper opens `/dev/tty`, requires a fresh `APPROVE` line, writes only
the identity to an owner-only atomic file, and verifies it against the same
in-memory snapshots. A caller-supplied authorization reference alone never
creates a receipt. The public `transform-review SOURCE.csv POLICY.yaml` CLI
uses a fixed bounded CSV snapshot, derives classification evidence from those
same bytes, and includes referenced local mapping/generation-policy bytes
resolved relative to the policy file. It emits only the value-free field review
and snapshot digest; `--json` uses the normal versioned CLI envelope. It never
mints a receipt, writes transformed rows or treats a valid review as approval.
The receipt helpers remain private; complete semantic checks, the scoped
safety amendment and end-to-end no-reopen execution still remain.

`validate_inline_mapping_shape` checks a caller-declared tuple width and rejects
exact duplicate source tuples, including repeated nulls. Scalar kind participates
in equality, so booleans, integers and floats are not conflated before schema
normalization. This shape check does not establish type compatibility or detect
duplicates introduced by normalization. Many-to-one output tuples remain subject
to later declared uniqueness/relationship checks; no execution is authorized.

`validate_inline_scalar_mapping` currently handles already-typed string, integer,
float, boolean and canonical ISO date tuples plus explicit nullability. It does not coerce text or
integers into floats; empty string remains a string, not null. Dates must be exact
`YYYY-MM-DD` strings accepted by the standard calendar parser; compact/week dates,
timestamps and whitespace are rejected, never truncated or converted. Date strings
remain unchanged. Datetime/decimal types fail closed until their contracts are
implemented. This limited internal helper is not the CSV loader or full typed
mapping preflight. Duplicate detection is exact because no normalization occurs.

## Internal CSV Byte Parser

`core/transformation_csv.py` accepts an already bounded byte snapshot, never a
path. The declaration path is not opened. Encoding (`utf-8` or `utf-8-sig`),
delimiter (comma, semicolon, tab or pipe), and null token are explicit. A null
token must be nonempty; `None` disables conversion. Quoting does not escape the
null token. Empty strings remain strings. No encoding/dialect/type inference.

Headers must be unique, nonempty and exactly the union of declared source and
replacement columns. Row widths must match; duplicate source tuples fail.
Limits cover bytes, rows, columns, cells and cell characters. The required caller
budget is reused, with cooperative checks around parsing and validation; it is
not an interruptible timeout. The standard CSV parser may impose a lower process
field-size ceiling; this helper never changes process-global settings.

Results are private string/null tuples requiring typed preflight; numeric text
is not silently converted. Errors are fixed and detached. File access, snapshot
approval and cumulative multi-file budgeting remain adapter responsibilities.

`io/mapping_snapshot.py` reads a relative local path beneath an explicit absolute
root using existing descriptor-relative no-follow traversal. Absolute input paths,
parent traversal and symlink components fail. Regular-file opening is nonblocking
so a FIFO cannot stall before its type is rejected. Reads are byte-bounded and
reuse the caller deadline; descriptor size/mtime/ctime changes fail closed.
The private immutable result contains bytes and their SHA-256, omitted from repr.
Consumers must parse those returned bytes, not reopen the path. This is not an
atomic filesystem snapshot guarantee or execution approval; same-byte identity
and separately reviewed permissions still need binding at the execution boundary.

`io/mapping_loader.py` composes the snapshot reader, CSV-byte parser and typed
inline validator without reopening the source path. It passes explicit limits
and the same invocation budget through all stages. The private result retains
the validated mapping and hash of the bytes parsed, both excluded from repr.
String/date/DATETIME/integer and approximate FLOAT CSV mappings work. FLOAT accepts only
ASCII decimal/exponent syntax and rejects non-finite values, overflow, underflow
to zero and duplicate source keys after conversion. It is not exact DECIMAL;
Decimal remains unfinished. DATETIME validation accepts canonical ISO text with
an explicit numeric offset, `Z`, or no timezone; it retains the exact text and
never converts offsets. An execution timezone policy and equivalence/collision
preflight remain unfinished. This adapter is not exposed through
CLI/MCP and grants no permission to preserve source data or execute transformations.

CSV integer normalization accepts only an optional ASCII sign followed by ASCII
digits. It converts directly to Python int, never through float; whitespace,
exponents, underscores and boolean text are rejected. Leading zeros/sign variants
normalize, so duplicate source keys are checked again after conversion. Composite
string columns retain leading zeros; nullability is explicit on both sides.
The same budget covers normalization. This CSV-specific step does not weaken
strict inline mapping types; oversized integers may hit Python's safe digit limit
and fail with the same bounded error. No global integer limit is changed.

## Private Behavior Policy YAML

`core/transformation_yaml.py` loads/saves UTF-8 bytes without filesystem access.
The existing safe loader supplies depth/alias limits; policy loading additionally
rejects duplicate/non-string keys and YAML merge keys. Model validation is repeated
on load and before dump. Date-like strings must stay quoted; dump preserves their
string type rather than relying on YAML implicit timestamp conversion.

Caller byte ceilings and the same cooperative invocation budget apply to both
directions. Serialization checks the byte ceiling after materializing output;
it is not a streaming memory cap. Output includes private inline mappings and
must never be used as a public summary or provider/MCP payload. Filesystem
permissions/atomic writes, authorization and execution remain separate work.
Failures use detached fixed errors, not YAML snippets or validation payloads.

`io/behavior_policy_files.py` adds explicit root-relative local load/save using
the existing snapshot reader and atomic writer. Saving explicitly replaces the
destination with an owner-only file; it is not version history. Existing contents
survive failures before publication, with temporary files cleaned up. A failure
after the underlying atomic rename (for example directory fsync failure) may
leave the new file published; callers must not assume rollback in that case.
Deadlines are checked before publication, not inside filesystem syscalls.
Load/save errors remain fixed and detached. These operations grant no approval
to execute a policy or preserve source values.
