# ADR-0007: Make relationships and business rules executable

- Status: Accepted — retrospective baseline.
- Recorded: 2026-09-29. This is the recording date, not an invented original approval date.
- Authority and implementation boundaries: see Evidence below and the [register conventions](index.md#status-and-authority).

## Context

Plausible-looking rows can violate keys, nullable references, formulas and cross-table invariants.

## Decision

Represent supported rules in typed YAML/JSON contracts, enforce them deterministically, and validate the result. Declared/generated key domains and reviewed relationships take precedence over heuristic guesses. Repeated-identifier pools retain counts, not source identifiers or lookup maps.

Valid publication requires the applicable invariants. Controlled invalid cases must be explicitly requested, reproducible and reported; they never bypass privacy. Source-free generation formulas remain supported independently of the narrower transformation RC scope in ADR-0026.

## Alternatives and consequences

Free-form LLM validation cannot establish invariants. Silently repairing conflicting keys or publishing a partially solved dataset hides invalidity. Exact source frequencies/totals are not guaranteed by retaining relational structure.

## Evidence

Sources: [generation and rules](../agent-guides/generation-and-rules.md), [relational contract](../concepts/relational-synthesis-contract.md), [validation specification](https://github.com/wa-pis/agent-paranoid-android/blob/637065966c12584e11c9b437c1e8b8f8d708c0df/openspec/specs/dataset-validation/spec.md).
Executable anchors: [business rules](https://github.com/wa-pis/agent-paranoid-android/blob/637065966c12584e11c9b437c1e8b8f8d708c0df/tests/test_business_rules.py), [generation hardening](https://github.com/wa-pis/agent-paranoid-android/blob/637065966c12584e11c9b437c1e8b8f8d708c0df/tests/test_generation_contract_hardening.py), [identifier pools](https://github.com/wa-pis/agent-paranoid-android/blob/637065966c12584e11c9b437c1e8b8f8d708c0df/tests/test_identifier_pool.py).

## Revisit when

A new rule family needs defined executable semantics and validation; prose or a prototype alone is insufficient.

