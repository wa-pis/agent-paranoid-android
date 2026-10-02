# ADR-0024: Use typed input/output adapters around one transformation core

- Status: Accepted — owner-approved target; incomplete integration.
- Recorded: 2026-09-29. This is the recording date, not an invented original approval date.
- Authority and implementation boundaries: see Evidence below and the [register conventions](index.md#status-and-authority).

## Context

CSV-only internals would lose native null/decimal/type provenance and duplicate transformation semantics when database/Parquet routes arrive.

## Decision

Target four input families (CSV, Parquet, Trino query results, PostgreSQL query results) and three outputs (CSV, Parquet, PostgreSQL SQL script) through common transformation/validation. Bind source snapshots and explicit output schema/format before execution. SQL output is a file, not database writes.

Reuse scalar encoders and existing optional extras, but do not weaken synthetic-only writers to emit mixed-origin results. Do not use a lossy CSV roundtrip as the identity of a native source. Unsupported types and routes fail closed.

## Alternatives and consequences

A separate engine per format duplicates safety and mapping semantics. Relabelling a Parquet-encoded internal capture as the original source loses adapter/query identity. Private CSV-named functions and injected fictional drivers are transitional implementation details, not the final public API.

Twelve-route acceptance is a target, not a claim of completion. Named cursors, worker isolation and decoded-byte limits alone do not prove hard wire/RSS containment or scale.

## Evidence

Sources: [resumption architecture](https://github.com/wa-pis/agent-paranoid-android/blob/637065966c12584e11c9b437c1e8b8f8d708c0df/openspec/changes/selective-source-transformation/resumption-plan.md), [policy input/output contract](https://github.com/wa-pis/agent-paranoid-android/blob/637065966c12584e11c9b437c1e8b8f8d708c0df/openspec/changes/selective-source-transformation/policy-contract.md), [implementation map](https://github.com/wa-pis/agent-paranoid-android/blob/637065966c12584e11c9b437c1e8b8f8d708c0df/docs/implementation_map.md).
Executable anchors: [Parquet](https://github.com/wa-pis/agent-paranoid-android/blob/637065966c12584e11c9b437c1e8b8f8d708c0df/tests/test_transformation_parquet.py), [SQL output](https://github.com/wa-pis/agent-paranoid-android/blob/637065966c12584e11c9b437c1e8b8f8d708c0df/tests/test_transformation_sql.py), [query capture](https://github.com/wa-pis/agent-paranoid-android/blob/637065966c12584e11c9b437c1e8b8f8d708c0df/tests/test_transformation_query_capture.py).

## Revisit when

Choose public adapter contracts only with typed, end-to-end evidence; do not treat private function names as permanently accepted architecture.

