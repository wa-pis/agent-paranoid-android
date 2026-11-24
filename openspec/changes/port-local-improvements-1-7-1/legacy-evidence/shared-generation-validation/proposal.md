# Shared CSV Generation Validation

## Status

Implementation and verification in progress, unreleased, 2026-11-21. This
internal execution change selects no version, tag or publication.

## Why

The [public CSV benchmark](../public-streaming-csv/public-csv-benchmark.md)
identified repeated validation as a substantial part of export time. Ordinary
CSV bundles currently validate inside generation, again at the bundle boundary,
and again for the report. Streaming repeats mandatory and report checks on each
tile and normalizes primary keys separately. Equivalent checks can share work
within one unchanged candidate dataset while preserving every safety boundary.

## What Changes

- Share mandatory enforcement and report evaluation before writing valid-mode
  CSV bundles that have no business-rule applier. Use a private candidate helper;
  retain the public row-returning generator's existing mandatory checks. The
  spec-only CLI omits its known default no-op wrapper so ordinary CSV generation
  can use this path, while preserving custom callbacks and rule files.
- Share per-tile mandatory/report work in existing eligible streaming CSV exports
  and reuse normalized rows for whole-run primary-key checks.
- Preserve raw generated-value privacy, declared-type report normalization,
  report settings and fail-fast behavior, generated rows, seeds and output bytes.
- Keep JSON, Parquet, SQL, non-valid modes and callback workflows on their
  existing paths, including post-callback mandatory checks and error order.
- Record new verification and benchmark evidence in this change. Preserve the
  earlier public CSV raw results and methodology as historical evidence.

## Safety And Compatibility

No public signature, option, dependency, artifact schema, generation algorithm or
source-row policy changes. Mandatory checks still precede row return or writing,
including when report sections are disabled. Validation results stay local to
the current operation; no persistent cache or public skip-validation capability
is introduced. Existing source-overlap checks, budgets, private staging, atomic
publication and value-free failures remain in force.
