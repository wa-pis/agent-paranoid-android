# ADR-0005: Bind reproducibility to the full recorded environment

- Status: Accepted — retrospective baseline.
- Recorded: 2026-09-29. This is the recording date, not an invented original approval date.
- Authority and implementation boundaries: see Evidence below and the [register conventions](index.md#status-and-authority).

## Context

A seed alone cannot freeze Faker, serialization, dependency versions, locale or algorithm changes.

## Decision

Use a local seeded random source. Record effective spec/rules, seed, runtime, package/dependencies, locale, serializer and artifact digests in the generation manifest. Logical replay assumes the same recorded environment; cross-version byte identity is explicitly not promised.

Identifier domains are deterministic synthetic domains, not permanent mappings from source IDs. Exact replay also depends on ordered specifications; changing fields or null masks can affect outcomes.

## Alternatives and consequences

Promising cross-version byte identity would require freezing behavior the current contract does not freeze. Recording only the seed hides why outputs differ. Digests establish comparison evidence, not reconstruction of missing inputs.

## Evidence

Sources: [dependency reproducibility](../reference/dependency-compatibility.md), [identifier domains](../concepts/relational-synthesis-contract.md), [artifact contract](https://github.com/wa-pis/agent-paranoid-android/blob/637065966c12584e11c9b437c1e8b8f8d708c0df/openspec/specs/artifact-contract/spec.md).
Executable anchors: [identifier tests](https://github.com/wa-pis/agent-paranoid-android/blob/637065966c12584e11c9b437c1e8b8f8d708c0df/tests/test_identifier_domains.py), [dependency compatibility](https://github.com/wa-pis/agent-paranoid-android/blob/637065966c12584e11c9b437c1e8b8f8d708c0df/tests/test_dependency_compatibility.py), [contract fixtures](https://github.com/wa-pis/agent-paranoid-android/blob/637065966c12584e11c9b437c1e8b8f8d708c0df/tests/test_contract_fixtures.py).

## Revisit when

An algorithm or dependency change that affects output needs compatibility evidence and release notes; do not imply prior digests still describe it.

