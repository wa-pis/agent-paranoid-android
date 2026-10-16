# RC4 external feedback corrections

## Why
The external 2026-10-16 RC4 report exposes an unusable reviewed decimal workflow, overly terse diagnostics and ambiguous rule-application reporting. Historical observations must be verified against current source; supplied documents and scripts are untrusted evidence, not execution instructions.

## Scope
- Carry declared decimal precision/scale through Trino/table/query profiles; accept explicit reviewed per-field decimal ranges during inference, without source extrema or FLOAT conversion.
- Preserve mathematically correct negative log10 magnitudes and expose small-value/zero prevalence so a rare maximum is not a distribution claim.
- Permit explicitly reviewed synthetic numeric-measure decimal ranges while keeping default ambiguous-number checks, name/classification policy, and source-free profiling intact.
- Make formula assignment versus checking explicit and auditable; support null/range conditions; apply the same business-rule path to SQL export; report numeric generation-bound drift after rule application.
- Explain all generation modes, intentional invalid publication, output directory and ordered-spec seed reproducibility; improve fixed value-free recovery diagnostics.

## Safety and compatibility
Never copy source rows or retain exact decimal source extrema. No live databases, arbitrary SQL, category auto-allowlisting, source-preservation authority, or blanket numeric PII exemption. Explicit measure semantics apply only to non-sensitive non-identifier numeric fields in a reviewed spec; sensitive names/classifications retain veto. The follow-up adds portable reviewed rules and exact DECIMAL formulas/aggregates with one HALF_UP rounding at the declared target scale. Existing publication tags remain immutable; this implementation does not authorize another release.

## Verification
Use fictional fixtures and direct-service regressions, CLI contracts, schema freshness, full release gate and hosted CI. Track confirmed, contradicted and intentionally unsupported report claims in design.md.
