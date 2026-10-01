# ADR-0021: Require local human approval of exact preservation inputs

- Status: Accepted — owner decision 2026-09-24; execution gated.
- Recorded: 2026-09-29. This is the recording date, not an invented original approval date.
- Authority and implementation boundaries: see Evidence below and the [register conventions](index.md#status-and-authority).

## Context

A model-generated policy, boolean approval or schema hash cannot authorize retaining source values or detect changed source content.

## Decision

Preserve only explicitly reviewed non-sensitive fields with a bounded operator comment and no positive or conflicting sensitivity evidence. Missing, unknown or disputed field decisions cannot authorize preservation; the absence of an observed sensitivity signal is not itself a non-sensitive decision. Preserve fallbacks have the same requirements; DECIMAL preservation remains blocked by default.

Use fresh local interactive CLI confirmation of the full value-free effective review. Bind restricted receipt identity to exact policy, source, classification, review, mapping and generation-policy bytes, including referenced inputs. Revalidate and consume those same snapshots. Agents/MCP cannot mint or broaden receipts; noninteractive execution may only consume a matching existing receipt.

## Alternatives and consequences

An opaque authorization_ref, piped confirmation or existing source-free agent approval is insufficient. A separately controlled cryptographic human authority was not selected. The chosen local-operator model does not resist an equal-privilege local process impersonating a person; a receipt is integrity evidence, not proof of personhood.

Human confirmation cannot override positive sensitivity or authorize wholesale row copying.

## Evidence

Sources: [selected local trust boundary](https://github.com/wa-pis/agent-paranoid-android/blob/637065966c12584e11c9b437c1e8b8f8d708c0df/openspec/changes/selective-source-transformation/safety-boundary.md), [policy identity contract](https://github.com/wa-pis/agent-paranoid-android/blob/637065966c12584e11c9b437c1e8b8f8d708c0df/openspec/changes/selective-source-transformation/policy-contract.md).
Executable anchors: [receipt](https://github.com/wa-pis/agent-paranoid-android/blob/637065966c12584e11c9b437c1e8b8f8d708c0df/tests/test_transformation_receipt.py), [approval](https://github.com/wa-pis/agent-paranoid-android/blob/637065966c12584e11c9b437c1e8b8f8d708c0df/tests/test_transformation_approval.py), [snapshot](https://github.com/wa-pis/agent-paranoid-android/blob/637065966c12584e11c9b437c1e8b8f8d708c0df/tests/test_transformation_snapshot.py).

## Revisit when

A stronger identity threat model or sensitivity exception requires a new explicit decision and safety review, not a receipt-format tweak.
