# Value Normalization Performance

## Status

Implementation and verification completed, unreleased, 2026-11-23. All twelve
public CSV runs succeeded; [benchmark.md](benchmark.md) and
[validation.md](validation.md) record performance, equivalence and safety checks.
This internal execution change selects no version, tag or publication.

## Why

The latest [public CSV benchmark](../schema-validation-performance/benchmark.md)
shows normalization remains a measurable validation stage. Already typed values
do not require string decoding, but the current walk still looks up their field
and parser metadata for every cell.

## What Changes

- Avoid field/parser lookups for actual non-string values after the unchanged
  scalar safety check. Prepare conversion metadata and the scalar-type tuple
  locally once per call.
- Preserve numeric/boolean string parsing, nullable empty strings, structural
  and scalar errors, error order and copy-on-write identity behavior.
- Keep raw-value privacy separate from report normalization, rebuild after
  specification edits and apply the same policy to every source-derived spec.
- Verify exact normalization outcomes, exceptions and object identities, then
  repeat both public CSV benchmarks without replacing historical evidence.

## Safety And Compatibility

No source access, public signature, setting, dependency, artifact format,
classifier, random-call order or seed algorithm changes. Structural and scalar
checks remain active even for already typed generated rows. Normalization does
not mutate input rows or authorize their publication; mandatory privacy and
other validation boundaries retain their existing order and budgets.
