# Schema Validation Performance

## Status

Implementation and verification completed, unreleased, 2026-11-23. All twelve
public CSV runs succeeded; [benchmark.md](benchmark.md) and
[validation.md](validation.md) record performance, equivalence and safety checks.
This internal execution change selects no version, tag or publication.

## Why

The latest [public CSV benchmark](../source-independent-profiling/benchmark.md)
shows schema validation remains a substantial export stage. The validator
repeats type dispatch, field metadata access and primary-key field lookup for
every row, although the effective specification is fixed within one call.

## What Changes

- Prepare ordered field metadata, scalar type checkers and primary-key metadata
  once per entity and validation call.
- Preserve every entity, row-shape, count, required-value, type, string-length
  and primary-key check, including error ordering and supported mapping rows.
- Retain existing scalar parsing, strict privacy and deterministic generation;
  rebuild preparation after specification edits instead of caching verdicts.
- Compare the exact validator behavior against the previous implementation and
  record fresh public CSV timings and memory separately from historical evidence.

## Safety And Compatibility

The shared validator applies to specifications from every supported source.
Source labels do not select a weaker policy. No source access, detector policy,
public signature, setting, dependency, artifact format, seed algorithm or random
call order changes. Ordinary generation, streaming, callback rechecks and report
validation keep their existing trust boundaries and budgets.
