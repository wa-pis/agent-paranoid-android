# ADR-0008: Keep exact financial types out of binary FLOAT

- Status: Accepted — retrospective baseline and gated candidate extension.
- Recorded: 2026-09-29. This is the recording date, not an invented original approval date.
- Authority and implementation boundaries: see Evidence below and the [register conventions](index.md#status-and-authority).

## Context

Binary FLOAT cannot represent exact base-ten financial contracts. A numeric type also does not prove a value is non-sensitive.

## Decision

DatasetSpec 1.1 exact DECIMAL uses explicit precision/scale and reviewed decimal_range bounds, integer units/base-ten arithmetic, and Parquet decimal128 up to precision 38. Profiling carries declared shape, not exact source decimal values/extrema; bounds require explicit review. Unbounded SQL numeric remains approximate, not advertised as exact.

Transformation decimal mappings require matching declarations and exact normalization. Preservation stays blocked by default. Existing private formula rounding is HALF_UP at declared scale, but formula execution is not an RC requirement or public activation (ADR-0026). Source-free active constraints on DECIMAL entities remain fail-closed under their existing contract.

## Alternatives and consequences

Silently converting to FLOAT loses precision; inferring sensitive extrema or disabling content checks would weaken privacy. Precision overflow rejects rather than rounding away a constraint. Broader formula and exception policies are not inferred from DECIMAL support.

## Evidence

Sources: [profiling guide](../agent-guides/profiling.md), [generation guide](../agent-guides/generation-and-rules.md), [transformation policy](https://github.com/wa-pis/agent-paranoid-android/blob/637065966c12584e11c9b437c1e8b8f8d708c0df/openspec/changes/selective-source-transformation/policy-contract.md).
Executable anchors: [exact dataset](https://github.com/wa-pis/agent-paranoid-android/blob/637065966c12584e11c9b437c1e8b8f8d708c0df/tests/test_exact_decimal_dataset.py), [decimal units](https://github.com/wa-pis/agent-paranoid-android/blob/637065966c12584e11c9b437c1e8b8f8d708c0df/tests/test_exact_decimal_units.py), [private rounding](https://github.com/wa-pis/agent-paranoid-android/blob/637065966c12584e11c9b437c1e8b8f8d708c0df/tests/test_transformation_decimal_rounding.py).

## Revisit when

Any sensitive-numeric exception, new precision range or public formula contract requires explicit policy and tests, not an incidental parser change.

