## Context

The audit examined CLI/MCP, database adapters, local profiles/cache, providers, transformation, deterministic generation/validation, and release tooling at immutable SHA `33a9ebdc3d1d158984945c3053f866cdd20bbc8d`. Nine findings are independently source-validated; eight have bounded offline synthetic probes. Audit-line allocation is established statically. No actual memory-exhaustion attack, live database or external-provider call was executed.

## Decisions

Use the smallest shared control that prevents each source-to-sink violation. Reuse existing numeric privacy inspection and provider category projection where practical. Preserve sensitivity/identifier lineage independently of output alias. Cache authority must match the current invocation, not prior authorization. Apply budgets before dangerous operations and before publication; metadata estimates do not replace decoded-byte accounting.

Resource limits must cover formula operands/results, Parquet decoded batches and total cells, inherited CSV request deadlines, and bounded audit reads. Large allocations are tested with bounded inputs or instrumentation, never with hostile multi-GB fixtures.

## Compatibility

Reject unsafe inputs with specific redacted exceptions. Keep ordinary safe formulas and profiles deterministic. If numeric-only formula semantics alter a public contract, document migration and test compatibility. Cache format/policy changes invalidate stale entries safely. No new dependency or speculative architecture is required.

## Work And Release State Machine

`fix -> focused regression -> commit/push -> full release gate -> full exact-SHA audit`.
A confirmed finding goes back to `fix`. An incomplete or unavailable review/check is not success.
After a clean review, finish original transformation acceptance, exact-main checks, required GitHub approval and Ubuntu artifact preflight. Bind accepted SHA and digests into the signed manifest/tag, publish the unused RC, and verify public artifacts. Persist progress in tasks/evidence so automation does not repeat passed checks without source changes. Do not amend published tags or silently promote stable.

## Risks And Open Questions

Native Parquet decoder allocation may precede Python checks; deployment memory containment remains relevant. PostgreSQL `sslmode=require` server-identity limitations and direct Python StringPattern budgets are hardening advice, not additional validated findings. No claim of absolute security or private-data acceptance follows from this audit.
