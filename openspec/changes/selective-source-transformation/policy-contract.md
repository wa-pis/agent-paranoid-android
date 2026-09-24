# Behavior Policy Contract — Review Draft

Internal design for implementation; not a supported CLI/API or permission to
execute source-preserving transformations. Existing DatasetProfile/DatasetSpec
schemas and source-free generation remain unchanged.

## Separate Evidence And Decisions

A versioned private behavior policy references a source schema fingerprint and
contains one explicit decision per `(entity, field)`. Profiling observations
remain evidence, not mutable declarations of permission. Duplicate decisions,
unknown fields, missing fields and schema drift fail preflight. Postponed wizard
decisions are incomplete and cannot produce an executable specification.

The shared core parses and validates decisions without reading a source, opening
a mapping file, executing a formula or generating data. CLI, wizard and agent
adapters must use this same core rather than independently interpreting YAML.
Parsing a valid policy is not approval to execute it.

## Action Variants

Use a discriminated union rather than a bag of optional, ignored settings:

| Action | Required configuration | Reject |
| --- | --- | --- |
| preserve | Explicit user authorization and non-sensitive declaration | Mapping, generator or formula settings; unresolved sensitivity conflict |
| synthesize | Reviewed generation policy reference | Preservation or mapping settings |
| substitute | Exactly one inline mapping, local CSV reference or named domain reference; unmatched policy | Generator settings unless unmatched synthesis is explicitly configured |
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

## Replacement Semantics

The Financial Values And Dependencies section of design.md is normative for
synthesis and unmatched-value synthesis fallback: declared magnitude/range,
sign, null, zero, precision/scale, rounding and overflow rules must all apply.
Binary float conversion cannot establish exact financial precision. Prohibited
replacement values remain prohibited in inline, CSV and synthesized outputs.
Non-null synthesized values must differ from originals except the approved zero
and declared-rounding coincidences; those exceptions never skip generation or
authorize wholesale copying. Derived totals must be recomputed and validated.
If no permissible replacement satisfies the policy and constraints, fail with a
bounded value-free error rather than retaining the input or relaxing constraints.

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
dependency syntax is not implemented; expression/declaration agreement is still
pending formula validation. No expression is evaluated by this check.
Observed `sensitive` fields cannot use preservation or unmatched-preserve, even
when the decision declares them non-sensitive. This check does not authenticate
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
creates a receipt. These helpers are not a public CLI command or execution
grant: source snapshot loading/reprofiling, complete semantic checks, the
scoped safety amendment and end-to-end no-reopen execution still remain.

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
String/date/integer CSV mappings work; float text conversion, DATETIME and Decimal
remain unfinished. This adapter is not exposed through CLI/MCP and grants no
permission to preserve source data or execute transformations.

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
