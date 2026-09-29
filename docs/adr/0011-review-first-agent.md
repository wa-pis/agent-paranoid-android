# ADR-0011: Use a review-first, recoverable agent state machine

- Status: Accepted — retrospective baseline.
- Recorded: 2026-09-29. This is the recording date, not an invented original approval date.
- Authority and implementation boundaries: see Evidence below and the [register conventions](index.md#status-and-authority).

## Context

Planning, external advice and generation have different authority. Interrupted publication must not cause a second generation with uncertain identity.

## Decision

Agent planning writes safe profile/spec/plan artifacts and stops. Review exposes metadata and the exact effective-spec fingerprint; advice returns to review. Approval must match the reviewed identity and revalidate source/profile safety.

Completion stores a checkpoint. Recovery verifies the unchanged spec, source binding, manifest, reports and generated artifacts, then publishes missing metadata without regenerating rows. Legacy unbound plans must be replanned. Source-free agent approval is not the local transformation-preservation approval in ADR-0021.

## Alternatives and consequences

Auto-approving a model suggestion eliminates the review boundary. Retrying generation as recovery can change output or overwrite evidence. More workspace artifacts are accepted to make states and tampering observable.

## Evidence

Sources: [agent design](../agent_design.md), [orchestration specification](https://github.com/wa-pis/agent-paranoid-android/blob/637065966c12584e11c9b437c1e8b8f8d708c0df/openspec/specs/agent-orchestration/spec.md), [application boundaries](../reference/application-boundaries.md).
Executable anchors: [approval](https://github.com/wa-pis/agent-paranoid-android/blob/637065966c12584e11c9b437c1e8b8f8d708c0df/tests/test_agent_approval.py), [recovery](https://github.com/wa-pis/agent-paranoid-android/blob/637065966c12584e11c9b437c1e8b8f8d708c0df/tests/test_agent_recovery.py), [status](https://github.com/wa-pis/agent-paranoid-android/blob/637065966c12584e11c9b437c1e8b8f8d708c0df/tests/test_agent_status.py).

## Revisit when

A new transition or approval shortcut requires explicit state/identity semantics and interruption tests.

