# Feedback statistics verification

## Existing numeric prevalence S1/S2

The RC4 regression verifies mixed-scale sampling, zero-only generation and
negative subunit orders. Fictional boundary tests verify non-null denominators,
legacy omitted metadata/serialization and rejection of Boolean, negative,
fractional, missing or excessive counts and inconsistent subunit orders.
PostgreSQL, Trino and query-summary builders share `prevalence_sql`; no duplicate
metadata or source query is introduced. This is not evidence of exact decimal
bounds or source fidelity.

## Parquet S5

The existing 256-row sensitivity scan now also counts bounded private scalar
digests; no second scan, source rows or digest output is added. Non-null
ratios use the complete inspected population. The cap is 10,000 per column;
overflow is lower_bound, while repetitions at the cap remain exact. Binary,
composite and nonfinite equality stays unknown. Null metadata retains its
independent unknown policy. Incomplete inspection rejects without a profile.
No key, identifier pool or relationship is nominated by this change.

193 focused Parquet, adapter, identifier, discovery, contract and documentation
tests passed. This includes CLI/direct fingerprint parity, value-free artifacts,
empty/all-null inputs, signed zeros, decimals, censored/unknown evidence,
missing/malformed null metadata, truncated inspection and existing cell,
decoded-byte and deadline limits. Ruff, mypy (156 source files), strict MkDocs
and strict OpenSpec validation passed. Existing schema fields suffice: no schema
version change. Reprofiling changes profile fingerprints and requires new review.
An additional 248 CLI, I/O workflow, agent planning/approval and advisor tests
passed. Full PR CI remains pending; there is no package release claim.

## SQL S3 and S8 measurements

138 focused numeric prevalence, PostgreSQL profiler, query-builder and Trino
masking tests passed. A 26-case matrix exercises integer, float and DECIMAL query
summaries for both SQL adapters, mixed zero/subunit and all-zero evidence, and
one/48-column schemas. It checks negative maximum exponents, non-null
prevalence denominators and source-free profiles. Trino DECIMAL table summaries
retain the same value-free evidence without exact extrema.

At the service boundary, query profiles use one no-row schema query, one row
count and one aggregate per column: 3 requests at width 1, 50 at width 48.
Trino DECIMAL table profiles use metadata, row count and one aggregate per
column, also 3/50. Existing PostgreSQL table tests establish 12 statements for
their four-column/two-table fixture, or 13 with one allowed local category.
These are deterministic fake-client statement counts, not live latency or scan
cost measurements. No query batching or budget increase is claimed; the S8
batching evaluation remains open.

## Remaining evidence

Historical profile provenance remains unconfirmed. The user tentatively
identified installed version 1.6.0 but supplied no source configuration. Temporal
granularity/out-of-range reproduction, category recovery and bounded batching
evaluation remain separate unchecked tasks. No live database was used.
