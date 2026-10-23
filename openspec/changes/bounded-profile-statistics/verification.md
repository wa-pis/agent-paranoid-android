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
passed. Parquet follow-up #642 completed full green CI and merged as
`7ff706da1cfcb5e0b7fa66cd2b4e58ca2615ef9a`. No package release is claimed.

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
identified installed version 1.6.0 but supplied no source configuration.
Historical temporal provenance and bounded batching evaluation remain open.
Independent bounds defects and category recovery are documented below. No live
database was used.

## Independent temporal reproduction (S6)

Fictional reviewed bounds 1000-01-01 through 3000-01-01 plus .999999 seconds
reproduce an output one microsecond above the upper endpoint when the RNG
selects its largest offset. Three naive/positive/negative-offset cases failed
before the fix. Integer timedelta day/second arithmetic fixes all three without
changing second-resolution sampling. Twelve direct endpoint cases cover lower
and upper selection, subsecond intervals, different compatible offsets and
extreme DATE endpoints. Alongside existing aggregate-to-generation, fallback,
CSV, SQL-profile and RC4 tests, 160 tests passed. Full CI remains pending.

This is an independent boundary defect, not proof of the external report's
cause. Monthly source grain remains unknown and is not inferred from extrema;
the bounded reviewed extension is specified in design.md for future activation.


A separate partial-bound reproducer returned 2020 for a supplied maximum of
2010. Four DATE/DATETIME partial-bound tests failed before the effective-order
check; they now reject instead of silently clamping. Two CLI regressions verify
that an existing dataset is unchanged and no manifest is published. The complete
18-case temporal matrix passes. Neither independent defect establishes the
historical report's cause.

Final temporal verification: 286 temporal, SQL, CSV, generation-contract, golden
artifact and documentation tests passed. Mypy (156 sources), Ruff, strict MkDocs
and strict OpenSpec passed. Full CI for this temporal follow-up remains pending.


## Category work and scope (S7)

Nineteen fictional boundary cases cover stopping after the default 20-value
ceiling plus one overflow sentinel, pre-iteration field/limit rejection, strict
query-builder limit types, both adapters rejecting wrong output entity/field
before row-count fetch, and CLI recovery without raw category preservation.
All 17 initial cases reproduced their respective gaps before correction; two
additional privacy/recovery cases passed. Existing PostgreSQL exact-scope
pre-connection and wildcard bounded-metadata tests remain applicable.

The focused existing adapter/privacy/builder suites passed 225 tests before the
two added recovery cases. Mypy (156 files) and Ruff passed. The source default
remains 20; no globally raised cap, silent truncation, schema change or new
preservation permission is introduced. Full candidate CI remains pending.

Final category verification on the temporal follow-up base: 183 focused category,
SQL adapter, PostgreSQL profiler and documentation tests passed. Mypy (156
source files), Ruff, strict MkDocs and strict OpenSpec passed. Full candidate
CI remains pending.
