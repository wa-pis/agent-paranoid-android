# File profiling guide

Read this guide for CSV, Parquet, folder profiling, profile caches, samples, or
schema inference.

Treat every input file as potentially sensitive. Profiling may retain only
metadata and bounded evidence needed to build a generation specification.

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

## Forbidden behavior

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
