# Design: controlled-negative-scenarios

## Approach

Compile each table's existing field and row rules into internal invalid cases.
For every row selected by the existing mode and invalid-ratio controls, apply
one case and advance through the bounded case list. A seeded random offset
keeps output reproducible while avoiding a fixed first-rule bias.

Invalid values are derived by the engine rather than supplied as new literals:
null for required fields, a synthetic sentinel outside an allowlist, the next
finite number beyond a bound, a forced matching condition plus an invalid
dependent value, reversed timestamps, or a perturbed formula result.

## Compatibility

No public command, option, rule-file shape, artifact schema, or valid-mode
behavior changes. Existing negative output values are intentionally not a
stable contract; the documented guarantee is deterministic rule violation.

## Deferred

Foreign-key and aggregate-formula negative cases require coordinated
cross-table mutation and will be added separately.
