# File profiling guide

Read this guide for CSV, Parquet, folder profiling, profile caches, samples, or
schema inference.

Treat every input file as potentially sensitive. Profiling may retain only
metadata and bounded evidence needed to build a generation specification.

## Allowed evidence

- column names and inferred data types;
- null ratios and approximate distinct counts;
- frequency-ranked categorical distributions with synthetic labels;
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

Bound file size, rows, cells, sample size, and wall-clock work. A cache may
store metadata-only profiles and source fingerprints, but never raw rows or
source-derived categorical values. Infer local relationships and conditional
rules before replacing categorical values, then rewrite their predicates to
the same synthetic labels so generation semantics remain intact. On deadline
or budget failure, do not publish a partial profile as trusted evidence.
Single-CSV generation binds its complete-row reuse check to non-reversible row
digests collected during the same CSV read that produced the profile; it does
not reopen the mutable source path before publication.
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
