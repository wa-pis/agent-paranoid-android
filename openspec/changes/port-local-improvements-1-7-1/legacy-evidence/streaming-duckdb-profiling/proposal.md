# Streaming DuckDB Profiling

## Status

Unreleased implementation, 2026-11-21. Implementation and local validation are
complete; [validation.md](validation.md) records the evidence. No version, tag or publication is selected. This
runtime, optional-dependency and scratch-boundary change requires normal
release-candidate acceptance before publication.

## Why

Removing the separate 10,000-value ceiling makes Python distinct sets grow with
cardinality. The recorded [72-run component experiment](../dataset-scale-estimation-performance/distinct-benchmark-evidence.md)
found a useful large-profile tradeoff: streaming DuckDB used a median 384 MiB
RSS versus 2,982 MiB for sets at 750k × 25 unique values, taking 11.82 s versus
10.88 s. Sets were better for small and low-cardinality cases. Those component
measurements do not establish whole-profiler performance or a total-memory cap.

## What Changes

- Keep Python sets until the sum of per-field distinct fingerprints for one
  entity exceeds 1,000,000, then drain them into a lazy exact-count query and
  continue the same CSV iterator. Do not reopen or resample the source.
- Add the optional `profiling` extra and include it in `all`; keep base
  dependencies unchanged. An unavailable backend fails at handoff with a
  value-free installation hint, rather than growing unbounded sets.
- Send only integer field ordinals and one-time HMAC tokens into DuckDB.
  Bound batches, query resources, deadline and private temporary disk; clean
  scratch before returning counts or publishing trusted evidence.
- Require full-profile equality, including inferred relationships, constraints,
  category policy, identifiers and fingerprints, across the handoff.

## Compatibility And Scope

Completed profiles retain existing exact counts, six-decimal ratios and cache
format 5. Existing byte, row, cell, sample and time budgets remain. The switch
threshold is not a distinct-value ceiling or an increased input limit.

Single-file CSV profiling, generation, output serialization, database sources,
public Python exports and MCP tool schemas are outside this change. There is no
general SQL interface, configurable storage-backend framework, source-value
staging, automatic budget increase or release action.
