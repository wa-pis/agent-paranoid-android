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
