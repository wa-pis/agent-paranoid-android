# ADR-0022: Use one strict behavior policy and deterministic mapping semantics

- Status: Accepted — owner-approved target; private implementation.
- Recorded: 2026-09-29. This is the recording date, not an invented original approval date.
- Authority and implementation boundaries: see Evidence below and the [register conventions](index.md#status-and-authority).

## Context

Wizard, YAML and agent paths must not interpret replacement tables differently. Mapping files can contain restricted originals.

## Decision

Keep one explicit field decision per schema field, strict versions/keys/actions and separate evidence from decisions. Persist inline mappings as typed pair lists, not YAML keys that conflate booleans/numbers/strings. Inline and local CSV mappings use shared normalization and duplicate checks.

Exact text replacement matches original cells once: matching per-column rule, then file-wide rule, then explicit fallback. No trimming, case-folding, cascading or implicit copying on miss; default miss rejects. Shared domains/composite keys bind ordered compatible components; collisions must satisfy declared constraints, never auto-repair.

Load bounded root-relative local references once into the approval snapshot. Referenced synthesis reuses reviewed DatasetSpec bytes, the transformation seed and one-to-one count. Private serialization may retain maps; reviews/providers/logs must not.

## Alternatives and consequences

Independent per-interface dictionaries drift and can cascade replacements. Remote URLs, scripts and API callbacks are not approved replacement adapters and remain unsupported. Their mention in client feedback does not make them accepted scope.

## Evidence

Sources: [policy contract](https://github.com/wa-pis/agent-paranoid-android/blob/637065966c12584e11c9b437c1e8b8f8d708c0df/openspec/changes/selective-source-transformation/policy-contract.md), [transformation design](https://github.com/wa-pis/agent-paranoid-android/blob/637065966c12584e11c9b437c1e8b8f8d708c0df/openspec/changes/selective-source-transformation/design.md).
Executable anchors: [mapping](https://github.com/wa-pis/agent-paranoid-android/blob/637065966c12584e11c9b437c1e8b8f8d708c0df/tests/test_transformation_mapping.py), [mapping loader](https://github.com/wa-pis/agent-paranoid-android/blob/637065966c12584e11c9b437c1e8b8f8d708c0df/tests/test_mapping_loader.py), [roundtrip](https://github.com/wa-pis/agent-paranoid-android/blob/637065966c12584e11c9b437c1e8b8f8d708c0df/tests/test_policy_mapping_roundtrip.py), [decisions](https://github.com/wa-pis/agent-paranoid-android/blob/637065966c12584e11c9b437c1e8b8f8d708c0df/tests/test_transformation_decisions.py).

## Revisit when

A new mapping source/action or collision rule changes semantics and needs a decision; ordinary parser refactoring does not.

