# ADR-0002: Keep synthetic generation source-row-free

- Status: Accepted — retrospective baseline.
- Recorded: 2026-09-29. This is the recording date, not an invented original approval date.
- Authority and implementation boundaries: see Evidence below and the [register conventions](index.md#status-and-authority).

## Context

Profiling real inputs is useful for structure, but shuffling, sampling or masking source rows would change the product's safety boundary.

## Decision

Generate fresh values from reviewed metadata/specifications, never from a source-row pool. Possible PII remains sensitive by default. Recheck privacy after solving constraints and before publication; disabling optional reports does not disable mandatory safety checks.

Exact local business enums are a narrowly allowlisted, content-checked exception, not a general permission to retain values. Default provider/MCP summaries stay source-literal-free. Selective mixed-origin transformation is a separate gated surface, governed by ADR-0020.

## Alternatives and consequences

Row masking and pseudonymization were not selected as the generation model. Exact-row non-reuse checks are a backstop, not proof against partial-value correlation or reidentification. No differential privacy, k-anonymity or blanket anonymity guarantee is made.

## Evidence

Sources: [safety model](../concepts/safety-model.md), [generation guide](../agent-guides/generation-and-rules.md), [synthetic-generation specification](https://github.com/wa-pis/agent-paranoid-android/blob/637065966c12584e11c9b437c1e8b8f8d708c0df/openspec/specs/synthetic-generation/spec.md).
Executable anchors: [safety tests](https://github.com/wa-pis/agent-paranoid-android/blob/637065966c12584e11c9b437c1e8b8f8d708c0df/tests/test_safety.py), [generation hardening](https://github.com/wa-pis/agent-paranoid-android/blob/637065966c12584e11c9b437c1e8b8f8d708c0df/tests/test_generation_contract_hardening.py), [privacy corpus](https://github.com/wa-pis/agent-paranoid-android/blob/637065966c12584e11c9b437c1e8b8f8d708c0df/tests/test_privacy_corpus.py). These are coverage references, not a fresh test run.

## Revisit when

A request to retain source values must use the separate transformation decision, not weaken generation checks.

