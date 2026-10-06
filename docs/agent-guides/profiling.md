# File profiling guide

Read this guide for CSV, Parquet, folder profiling, profile caches, samples, or
schema inference.

Treat every input file as potentially sensitive. Profiling may retain only
metadata and bounded evidence needed to build a generation specification.

Parquet profiles represent unavailable null and distinctness statistics as
`null`, not zero. Unknown distinctness cannot nominate a primary key or supply
relationship-confidence evidence.
Automatic spec inference rejects unknown null ratios; provide an explicit
reviewed spec rather than silently inventing a distribution. Local sensitivity
inspection uses bounded batches with existing cell, expanded-byte and time
budgets. It retains only flags, not values; composite content is conservatively
sensitive. Exhaustion fails without publishing a partial trusted profile.
Numeric inspection uses an explicit textual representation only for sensitivity,
not field matching. Unsupported binary evidence is conservatively sensitive.
The existing local profiling deadline spans inspection and metadata finalization;
the generation deadline is not a substitute.

SQL query-source files follow the same rule. Parse and authorize the bounded
file before database access, retain only a source fingerprint, policy version,
virtual schema, and safe aggregates, and never retain SQL text, literals,
backend messages, endpoints, or query rows. Database wildcard selectors must
first resolve to a deterministic explicit-column snapshot.

## Allowed evidence

- column names and inferred data types;
- null ratios and approximate distinct counts;
- bounded values and counts for explicitly allowlisted non-sensitive business
  enums, or frequency-ranked synthetic labels for other categorical fields;
- numeric ranges and percentiles;
- date/time ranges;
- string-length distributions;
- masked patterns; and
- synthetic examples that were not copied from the input.

Parquet `decimal128(p,s)` and declared PostgreSQL/allowed-query
`numeric(p,s)` retain schema-only precision and scale (up to 38 digits) in
`DatasetProfile`; no decimal source values or extrema are retained. A profile
cannot supply exact generation bounds on its own: infer-spec requires a human
to provide a reviewed `decimal_range` in DatasetSpec 1.1. Higher declared
precision fails closed. Unbounded SQL `numeric` retains its legacy approximate
FLOAT path and must not be presented as exact financial evidence.

Folder CSV profiles label `unique_ratio_kind` as `exact` (rounded to six decimal
places) or `lower_bound` when the 10,000-value distinct tracker overflows.
For `lower_bound`, display “at least X%”, not exact uniqueness. The ratio uses
non-null normalized values and is truncated downward to six decimal places.
Overflow evidence cannot nominate a primary key, even when its lower bound
exceeds the usual threshold. Relationship discovery excludes lower-bound parent
keys and omits lower-bound child distinct ratios from numeric evidence. Older
profiles and other producers default to `unspecified`, not proven exact; reprofile
old folder artifacts to obtain the new uncertainty metadata. This statistic is
unrelated to the planned percentage of unchanged values after transformation.
Cache format 5 invalidates older folder caches and recomputes their evidence,
including repeated-identifier pool sizes.
Unspecified metadata is omitted from canonical profile fingerprints to preserve
saved-plan compatibility; explicit exact/lower-bound evidence remains hash-bound.

## Forbidden behavior

These are source-free profiling/generation rules. The separate gated selective
transformation contract (ADR-0029) permits explicit mapped replacements to equal
other source values for every field, with value-free sensitivity notes. It does
not permit raw profile/review/transport disclosure or broaden direct preserve.

- copying or shuffling source rows;
- exposing real names, emails, phones, addresses, IDs, tokens, secrets, or
  other PII;
- preserving unique sensitive identifiers;
- leaking rare free-text values; or
- using a source sample as generated output.

Profile implementations should detect delimiter, encoding, and headers where
practical; infer types; estimate nulls and cardinality; detect likely PII;
mask sensitive evidence; and produce a reusable profile suitable for spec
inference.

Local category preservation is requested with a typed, field-scoped
`entity.field` allowlist. CLI workflows accept repeatable
`--local-category ENTITY.FIELD` options and persist the reviewed scopes in the
safe profile and inferred DatasetSpec. The allowlist is authorization input,
not proof that a value is safe; content checks remain mandatory before any
source literal is preserved. Database entities use their complete qualified
identity, for example `--local-category hr.public.employees.status`.

Bound file size, rows, cells, sample size, and wall-clock work. A cache may
store metadata-only profiles, source fingerprints, and explicitly allowlisted
bounded non-sensitive enum values, but never raw rows or sensitive source
values. Infer local relationships and conditional rules before replacing
non-allowlisted categorical values, then rewrite their predicates to the same
synthetic labels so generation semantics remain intact. On deadline
or budget failure, do not publish a partial profile as trusted evidence.
The closed common transformation workflow checks configured session total-byte
ceilings before profile capture. Existing behavior policies are parsed before
source capture so each source's file-byte ceiling is checked before reading and
while reading. New policy drafts use the configured session/default file ceiling;
aggregate limits remain independent, with no truncation or automatic increase.
Single-CSV generation binds its complete-row reuse check to non-reversible row
digests collected during the same CSV read that produced the profile; it does
not reopen the mutable source path before publication.
Review-first agent plans also bind CSV and CSV-folder approval to a SHA-256
digest of the source bytes captured before profiling. Approval and final
publication fail closed if those bytes change, and older unbound plans must be
replanned.
Dataset folders require one artifact stem per entity across CSV, JSON, and
Parquet inputs; duplicate stems fail before any row artifact is read.
The local profiling deadline is checked between individual field operations
and field finalization steps, not only between rows and files.

The normal flow is:

1. profile the input;
2. infer a generation specification;
3. generate synthetic data;
4. validate it; and
5. export the result.

Folder numeric sensitivity inspects both exact canonical decimal and retained float representations. Cache reuse binds the sorted local-category field authorization and verifies it against the stored profile; changed permissions require fresh profiling.

Exact local categories inspect integer values as decimal text for sensitive content, while retaining permitted small integers and booleans in their original types. Rejections do not include source values.

Dataset validation reads Parquet in256-row batches. Actual batch bytes and retained Arrow dictionary logical expansion share the configured `TEST_DATA_AGENT_MAX_PARQUET_EXPANDED_BYTES` allowance across Parquet entities; metadata page sizes are only an early gate. Rows and scalar leaf cells are cumulative across CSV, JSON and Parquet. Nested Parquet values obey cell/depth limits, and string character/binary byte lengths are checked before batch conversion to Python rows. Dictionary accounting includes retained storage plus logical expansion and is conservative. Arrow must decode one batch before these checks: native decoder peak RSS, page/dictionary allocations and Python object overhead are not bounded by this payload allowance. No partial dataset is returned on rejection.

Single-file CSV profiling carries an explicit budget through preflight, row/cell inspection and column finalization. Its default local deadline uses `TEST_DATA_AGENT_MAX_LOCAL_PROFILE_SECONDS`; an inherited MCP request deadline is checked at the same checkpoints. Profile serialization, temporary-file flush/fsync and post-replacement directory fsync are covered. Expiry restores an existing output through a same-directory rollback link, or removes a newly published output; temporary files/links are cleaned and a typed invocation-limit failure is returned. Concurrent replacement fails without overwriting the other writer. CSV row-digest profiling and generation retain the inherited request deadline through staged single-entity publication; expiry during replacements uses the existing rollback path. Checks are cooperative boundaries, not preemption of an active parser or filesystem operation.

Parquet metadata adapters now share the same pre-conversion Arrow leaf/depth/size and cumulative cell/decoded-byte checks as dataset readers. Bounded composites remain conservatively sensitive; limits fail before nested Python conversion. Native batch decode still precedes inspection and is not a peak-RSS guarantee.

Folder formula, temporal, conditional, aggregate and relationship mining share one cumulative inference-evaluation allowance, using `TEST_DATA_AGENT_MAX_BUSINESS_RULE_EVALUATIONS` (default5,000,000). Candidate work and row comparisons are charged inside loops. Existing local and captured MCP deadlines are checked there; exhaustion returns no trusted profile/cache. Public mining helpers accept an optional explicit `LocalProfileBudget` and preserve their normal candidate ordering and confidence semantics.

Transformation CSV output rejects formula-capable string cells and headers
before publication instead of modifying exact replacement text. Valid numeric
scalars retain numeric output, including negative values. Typed Parquet/SQL
output is governed by its own scalar encoding contract.

CSV-folder inventory uses streaming directory enumeration, checks the local and
captured invocation deadlines for every entry (including non-CSV entries),
rejects the first matching file beyond the configured file count, and sorts
only the bounded inventory. Cache fingerprints and agent fingerprints use the
same inventory control. Dataset validation applies it to CSV/JSON/Parquet.
Source byte fingerprinting charges actual per-file and aggregate bytes while
reading, with deadline checks before and after each bounded read. Growing
inputs fail closed; static inputs retain the existing fingerprint framing.
These are cooperative checks and do not preempt an active filesystem operation.

Cache fingerprint/load/write helpers accept an optional keyword-only
`LocalProfileBudget`; folder profiling passes its existing budget through cache
inventory. Default CLI/MCP source detection also uses bounded enumeration.

Transformation profile and policy files are captured below the trusted default
or explicit session total-byte ceiling before YAML parsing. A larger run budget
cannot raise this bootstrap file limit. After bounded parsing, explicit saved
profile limits may raise the aggregate source budget; session limits still win.

Saving a captured batch profile bounds every external recapture to its original
admitted byte length. Growing sources or declarations are rejected before payload
allocation; exact byte comparison still rejects other mutations before publication.
