# ADR-0010: Treat approved SQL as a bounded virtual source

- Status: Accepted — retrospective policy; aggregate extension authorized 2026-09-28.
- Recorded: 2026-09-29. This is the recording date, not an invented original approval date.
- Authority and implementation boundaries: see Evidence below and the [register conventions](index.md#status-and-authority).

## Context

Users need SQL-derived schemas/results without granting unrestricted query execution or confusing aggregate profiling with row capture.

## Decision

Parse one bounded local single-table SELECT; authorize physical table/columns through aliases. Query profiling uses no-row schema and aggregate wrappers and retains safe metadata, fingerprint and policy version, never SQL text/literals or query rows.

Policy 1.1 permits aliased SUM/COUNT/MIN/MAX/AVG and optional GROUP BY on authorized columns. COUNT(*) counts rows, not projection-star disclosure. Keep exclusions for joins, CTEs, subqueries, windows, arbitrary functions, writes and unsupported aggregate/grouping forms. Sensitive source references cannot be declassified through aliases/grouping. Derived expressions remain marked unsupported for automatic dependency-preserving inference.

## Alternatives and consequences

Accepting arbitrary SQL is incompatible with the boundary. Recreating SQL aggregates in an internal formula engine is outside the accepted RC scope. Private row-result capture is a separate surface and does not enlarge default profiling/MCP budgets.

## Evidence

Sources: [SQL specification](https://github.com/wa-pis/agent-paranoid-android/blob/637065966c12584e11c9b437c1e8b8f8d708c0df/openspec/specs/sql-query-source-profiling/spec.md), [safety guide](../agent-guides/trino-security.md), [owner policy record](https://github.com/wa-pis/agent-paranoid-android/blob/637065966c12584e11c9b437c1e8b8f8d708c0df/openspec/changes/selective-source-transformation/policy-contract.md).
Executable anchors: [SQL source policy tests](https://github.com/wa-pis/agent-paranoid-android/blob/637065966c12584e11c9b437c1e8b8f8d708c0df/tests/test_sql_query_source.py), [profiling tests](https://github.com/wa-pis/agent-paranoid-android/blob/637065966c12584e11c9b437c1e8b8f8d708c0df/tests/test_sql_query_profiling.py).
Scoped prior [AI review evidence](https://github.com/wa-pis/agent-paranoid-android/blob/637065966c12584e11c9b437c1e8b8f8d708c0df/openspec/changes/selective-source-transformation/reviews/16eece3-ai-safety.md) does not approve future changed code.

## Revisit when

An additional SQL shape/function needs a separate policy amendment, negative tests and the required safety review.

