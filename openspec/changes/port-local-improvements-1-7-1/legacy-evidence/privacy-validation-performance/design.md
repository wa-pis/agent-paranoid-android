# Design: Privacy Validation Performance

## Prepare Metadata, Preserve Value Checks

In `safety.validate_generated_row_privacy`, build one ordered field plan per
entity and invocation from the effective specification. Each entry contains
the field name, declared type, semantic type and existing sensitivity decision.
Iterate that plan for every row. Do not retain it globally or on the mutable
specification; later invocations must observe edited names, sensitivity flags,
semantic types and declared types.

Keep the existing row-mapping, blank-value and composite-value checks in their
order. Only then skip actual non-string values. The unchanged detector returns
`None` for these values, and the existing synthetic namespace guard applies
only to strings. Composite values must still fail even in negative generation.

For strings, retain numeric parsing only when the caller explicitly requests
the existing report policy. Mandatory generated-row checks remain strict even
when a numeric field contains a parseable phone-shaped string. Run the existing
content detector and synthetic namespace policy unchanged; semantic-type
precedence, all credential/PII detectors and their ordering stay intact.

## Boundaries And Compatibility

The effective specification is unchanged during one synchronous validation
operation. Build a fresh plan for independent calls and after callbacks. Do not
cache row values or validation results, skip all strings in a declared numeric
field, or add a synthetic-prefix shortcut to the detector. Existing mandatory
checks remain active with disabled report sections and in every generation mode.

This change does not touch the core privacy classifier, generation, CSV encoding,
budgets, source overlap checks, publication, report assembly or public contracts.
The shared validator reaches ordinary generation, streaming tiles, callback
rechecks and independent row/artifact validation through existing callers.

## Evidence

Use a bounded synthetic-only profile to confirm where work was removed, focused
equivalence and mutation tests for safety, and the existing public CSV benchmark
for export behavior and timings. Preserve the prior shared-validation report and
raw results. New public measurements must have a distinct output path, unchanged
fixture/policies, artifact audits and byte/hash equality to the proper baseline.
Do not claim an export speedup from the diagnostic microprofile alone.
