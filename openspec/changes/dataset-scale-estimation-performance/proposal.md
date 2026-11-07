# Change Proposal: dataset-scale-estimation-performance

## Status

Proposed 2026-11-04; implementation authorized 2026-11-08. Work is isolated on
`codex/dataset-scale-estimation`. See progress.md for measured implementation
evidence and remaining checks; no release is claimed.
Select a release candidate after implementation scope and benchmark evidence
are reviewed. This change does not authorize publication or live database tests.

## Why

The user reports roughly 20 minutes to generate 750,000 distinct rows with
25 columns and no complex relationships on a multicore CPU. This is a reported
observation, not a reproduced benchmark; hardware, field types, format and
validation costs are not yet known. Users need a forecast before starting,
a supported way past the default 100,000-row cap, and measured improvements.
Different rows are required: repeating a generated batch is not an optimization.

Current code has a configurable 100,000-row generation default, a 300-second
wall-clock budget and a 512 MiB output budget in core/limits.py. The internal
io/workflows.py estimate is conservative and format-agnostic; it protects a
budget and is not a user-facing prediction of actual serialized size.

## What Changes

- Forecast file size separately for CSV, JSON and Parquet, with uncertainty,
  assumptions, per-table totals and control-artifact overhead separated.
- Forecast logical database row payload and, when a database storage model is
  selected, approximate base-table storage. Exclude indexes, WAL, replicas,
  backups and other auxiliary storage; state exactly which row/page overhead
  is included. Do not equate a CSV file with database storage.
- Forecast end-to-end generation time on the current machine using optional
  bounded synthetic calibration and benchmark metadata; break down generation,
  validation and writing. Show a range or explicitly unknown, not false precision.
- Add a reviewed large-generation execution policy supporting at least the
  750,000 x 25 case without hidden environment edits or globally removing caps.
- Profile, remove measured bottlenecks, stream bounded batches, and enable
  bounded process parallelism for eligible workloads when measurements justify it.
  The first scalable engine supports independent tables in valid/edge modes;
  relationships, global rules and negative/mixed/load-test modes reject before
  generation. The legacy engine remains available for those bounded workloads.
- Expose shared estimates and execution settings consistently through Python,
  CLI and MCP planning/inspection, preserving human approval and summary-only output.

## Scope And Safety

Preserve source-free generation, seeded reproducibility, schema/business rules,
relationships, source-row reuse checks, privacy checks and atomic publication.
Distinctness means unique declared keys and, when requested, unique complete
rows; repeated individual categorical values remain valid. Reject impossible
uniqueness requirements rather than retrying indefinitely or duplicating rows.

Read-only database/profiling caps remain separate and unchanged. No database
writes, live infrastructure benchmarks, external AI calls, source-preserving
execution, automatic approval or unrestricted resource use are added.

## Success

Reproducible synthetic benchmark evidence for 750,000 distinct rows x 25 columns,
including total elapsed time, peak memory, output bytes, validation time and
1/2/4-worker results. On a recorded >=4-core reference host, aim for at least
2x end-to-end speedup versus the measured baseline on the same host; this is a
release acceptance target, not an assertion that the user's 20-minute run is
reproduced. If unmet, document findings and revise scope before calling the
performance goal complete. Forecast accuracy and unsupported-case behavior
must pass the acceptance matrix in design.md.
