# ADR-0014: Validate fixed inputs and publish completed artifacts safely

- Status: Accepted — retrospective baseline.
- Recorded: 2026-09-29. This is the recording date, not an invented original approval date.
- Authority and implementation boundaries: see Evidence below and the [register conventions](index.md#status-and-authority).

## Context

Paths can change after validation; partial outputs can be mistaken for complete results. Atomic rename and crash durability are different properties.

## Decision

Use bounded no-follow filesystem access and workspace/root policy, reject traversal/link escapes and revalidate relevant identity. Approval/execution consumes the same captured bytes rather than checking a path then reopening it.

Stage complete new bundles beside the destination and publish via the documented rename boundary. Preserve unrelated files and use manifest-owned overwrite/rollback rules. Revalidate recovery artifacts before completion. Catchable cancellation, budget and disk failures must not report partial publication as success.

## Alternatives and consequences

Writing directly to final paths creates misleading artifacts. Claiming all operations form a global transaction or survive power loss exceeds the contract: multi-file replacement and receipt/result markers have narrower guarantees. No universal fsync/crash-durability promise is made; individual writer behavior does not expand it.

## Evidence

Sources: [artifact persistence](../reference/stability.md), [resource/persistence operations](../operations/resource-budgets.md), [profiling identity guide](../agent-guides/profiling.md).
Executable anchors: [path policy](https://github.com/wa-pis/agent-paranoid-android/blob/637065966c12584e11c9b437c1e8b8f8d708c0df/tests/test_io_path_policy.py), [workspace store](https://github.com/wa-pis/agent-paranoid-android/blob/637065966c12584e11c9b437c1e8b8f8d708c0df/tests/test_workspace_store.py), [writers](https://github.com/wa-pis/agent-paranoid-android/blob/637065966c12584e11c9b437c1e8b8f8d708c0df/tests/test_io_writers.py).

## Revisit when

Revisit before promising crash/power-loss durability or supporting a new storage backend; retain explicit weaker guarantees meanwhile.

