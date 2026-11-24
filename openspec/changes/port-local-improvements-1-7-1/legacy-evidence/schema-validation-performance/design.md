# Design: Schema Validation Performance

## Prepare Once, Check Every Value

Build the ordered field plan and primary-key metadata once per entity and
invocation. Select the existing scalar type check for each declared field type
during preparation rather than redispatching on that type for every cell.
Keep preparation local; specification edits must be observed on the next call.
Do not retain rows, validation results or mutable specification state globally.

Preserve the existing parsers and native-scalar rules, including integer/boolean
distinctions, finite floating-point checks, numeric strings and temporal parsing.
Retain string-pattern length validation independently of its type check.
Row mappings, exact field sets, required values, primary-key type/uniqueness and
all error ordering keep their existing behavior. Errors must not include values.

## Shared Boundaries

This changes only internal schema-validation execution. Existing callers in
mandatory generation checks and report validation retain their settings,
fail-fast behavior and mutation boundaries. Privacy, normalization, relationship
and constraint checks remain separate and execute as before. No source adapter
may bypass the shared validator, and no additional source reads or SQL are needed.

No generator, CSV writer, classifier, output policy or publication logic changes.
The ordinary and tiled generators retain their distinct seed namespaces and
each must reproduce its previous output byte for byte.

## Evidence

Use bounded fictional data to profile the repeated work. Compare exact errors
and exception behavior with a frozen previous implementation across supported
scalar types, invalid rows, mapping variants and specification mutations. Keep
existing privacy and publication regressions enabled.

Repeat the unchanged public CSV benchmark for 100,000 and 750,000 rows with 25
fields, three fresh processes per path/size, no concurrent heavy work and the
same seed and limits. Record exclusive stages and sampled process-tree RSS;
retain actual validator counts, artifact audits, repeat and historical hashes,
private permissions and cleanup. Preserve all previous benchmark artifacts and
distinguish diagnostic timing from public API performance.
