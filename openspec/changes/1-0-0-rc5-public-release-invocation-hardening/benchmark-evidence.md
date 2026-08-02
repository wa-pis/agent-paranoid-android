# RC5 Invocation Default Benchmark Evidence

## Scope

The benchmark uses the production `TrinoProfiler`, `TrinoMasker`, query
builders, SQL execution accounting, and shared `QueryWorkBudget` against
deterministic synthetic responses. Its representative table has 100 columns:
20 sensitive string columns, 20
low-cardinality string columns, and 60 numeric columns.

The workload requires two table-level statements, one aggregate statement per
column, and one additional top-values statement for each low-cardinality
non-sensitive string column. The expected total is therefore 122 statements,
leaving 28 statements of headroom under the 150-statement default.

## Recorded Run

- Date: 2026-08-02
- Platform: Darwin 25.5.0 arm64
- Python: 3.11.2
- Command: `.venv/bin/python scripts/benchmark_trino_invocation_defaults.py`

```json
{"configured_deadline_seconds": 120.0, "elapsed_seconds": 0.031659, "profiled_columns": 100, "remaining_deadline_seconds": 119.968316, "statement_headroom": 28, "statements": 122}
```

## Decision

Retain the OpenSpec starting defaults of 100 profiled columns, 150 statements,
and 120 seconds. The column and statement limits cover the representative
aggregate-only profile while bounding wider or higher-fan-out invocations. The
recorded elapsed time measures local orchestration only; it excludes network
and Trino execution time. The 120-second value is a fail-closed invocation
deadline, not a database latency guarantee.
