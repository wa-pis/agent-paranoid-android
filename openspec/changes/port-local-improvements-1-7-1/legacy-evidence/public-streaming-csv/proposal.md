# Explicit Public Streaming CSV Export

## Status

Implemented and locally validated, unreleased, 2026-11-21. This public CLI/Python
execution and reproducibility change requires normal release-candidate review;
it selects no version, tag or publication.

## Why

The [streaming experiment](../dataset-scale-estimation-performance/streaming-generation-evidence.md)
preserved seeded CSV bytes and mandatory checks while avoiding a full Python
dataset. At 750k × 25, Python/Arrow took a median 43.35 seconds and 782.5 MiB
process-tree RSS, compared with 47.67 seconds and 1114.9 MiB with DuckDB.
Those are benchmark measurements, not acceptance figures for public bundle
export. CSV does not require Arrow conversion or a new dependency; it can
stream validated Python tiles through the existing CSV dialect directly.

Users need to request large export explicitly, retain ordinary generation by
default, and keep global relationships and business rules on their existing
complete-dataset path.

## What Changes

- Add `streaming=ParallelGenerationPolicy(...)` to `generate_dataset_bundle`
  and `--stream-csv` with optional `--workers` to the spec-only `generate` CLI.
  Add no package extra, optional module requirement or runtime dependency.
- Stream eligible single-entity valid-mode CSV specifications without
  relationships, constraints or a business-rule applier using `tiled-v1`.
  Keep bounded process scheduling, mandatory per-tile checks, whole-run key/count
  checks, safe CSV formatting, time/byte budgets and atomic bundle publication.
- Retain the legacy complete-dataset path and its existing limits for
  ineligible specifications. Streaming-specific limits do not enlarge fallback
  runs. Reject the flag on the source-profile route.
- Record the selected `tiled-v1` engine in the manifest's existing
  `reproducibility.generator_algorithm_version` field. Default/fallback exports
  retain legacy seeded behavior and version evidence.

## Scope And Safety

CLI opt-in bounds are 1,000,000 rows, 25,000,000 cells and one through four
workers, with four workers by default. Python callers supply an explicit
typed policy. The configured generation deadline and output byte budget remain
in force, including artifact overhead. No hard RSS guarantee is introduced:
primary-key tracking still grows with row count.

Generated candidates pass mandatory schema/privacy validation before file I/O.
No source rows, database access, external AI provider or Arrow/DuckDB staging is
introduced. Existing source-row overlap, review/approval and MCP workflows do
not opt in. Business-rule files, relationships, non-valid generation and other
global solving keep their existing implementation. The public result remains
a metadata/validation summary rather than generated rows.
