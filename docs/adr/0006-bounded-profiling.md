# ADR-0006: Profile bounded metadata and preserve uncertainty

- Status: Accepted — retrospective baseline.
- Recorded: 2026-09-29. This is the recording date, not an invented original approval date.
- Authority and implementation boundaries: see Evidence below and the [register conventions](index.md#status-and-authority).

## Context

Large files and private values make unrestricted sampling, full in-memory profiling and exactness claims unsafe.

## Decision

Prefer streaming-first CSV profiling and bounded safe aggregates. Cache metadata only, with the documented source identity and cache-version invalidation. Cache freshness is not exact-byte execution approval.

Exact non-sensitive local categories need explicit field scope plus content/cardinality/length checks; other categories use synthetic labels. Sensitive values and raw rows do not enter caches. Distinct-count overflow is a lower bound, never an exact ratio or sufficient primary-key evidence. Missing temporal bounds are unknown; generator fallback dates are assumptions, not source observations.

## Alternatives and consequences

Raw samples would simplify debugging but leak data. Treating a saturated distinct tracker as exact can invent keys and relationships. A generic file-stat cache key is cheaper than a content snapshot but must not be reused as approval identity.

## Evidence

Sources: [profiling guide](../agent-guides/profiling.md), [CSV specification](https://github.com/wa-pis/agent-paranoid-android/blob/637065966c12584e11c9b437c1e8b8f8d708c0df/openspec/specs/safe-csv-profiling/spec.md), [safety model](../concepts/safety-model.md).
Executable anchors: [distinct overflow](https://github.com/wa-pis/agent-paranoid-android/blob/637065966c12584e11c9b437c1e8b8f8d708c0df/tests/test_schema_distinct_overflow.py), [local categories](https://github.com/wa-pis/agent-paranoid-android/blob/637065966c12584e11c9b437c1e8b8f8d708c0df/tests/test_local_category_policy.py), [date disclosure](https://github.com/wa-pis/agent-paranoid-android/blob/637065966c12584e11c9b437c1e8b8f8d708c0df/tests/test_date_fallback_disclosure.py).

## Revisit when

Revisit evidence precision when a consumer needs a stronger claim; do not upgrade unknown/lower-bound metadata merely for convenience.

