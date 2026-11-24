# Design: Shared CSV Generation Validation

## Checked Candidate Boundary

Extract ordinary row creation and constraint solving into a private helper in
`generation/entity_generator.py`. Public `generate_dataset` calls that helper,
enforces the existing mandatory invariants and returns the same row mapping.
Only the valid-mode CSV bundle branch without a business-rule applier uses
candidates directly, immediately passing them through combined mandatory/report
validation before any dataset write. No unchecked candidate API is exported.
The spec-only CLI omits only its unchanged default no-op rule wrapper when no
rule file was supplied, for both ordinary and streaming generation. Explicit or
replaced callbacks remain active; profile and other command defaults are retained.

Other output formats, non-valid modes and every business-rule callback retain
the existing generator, callback and mandatory post-callback sequence. A callback
may mutate rows or the effective specification, even when it returns no report;
an earlier validation result cannot authorize those final rows. Caller-supplied
rows and independent artifact/SQL revalidation retain their existing boundaries.

## Share Only Equivalent Work

Keep the combined implementation in deterministic validation code. Prepare
normalization once for the report, reuse applicable schema/relationship/constraint
results, and construct the existing `DatasetValidationReport` with identical
sections, settings, ordering and fail-fast behavior. Mandatory checks execute
regardless of report settings. Preserve mandatory failure categories and
value-free errors.

Raw generated strings retain strict privacy classification; declaring a numeric
field must not permit a phone-shaped generated string merely because report
normalization can parse it. Report evaluation continues to decode numeric and
boolean strings by declared field type without modifying candidate rows. Share
work only where the inputs and policy are equivalent. Do not store validation
results on mutable rows/specifications, across calls, or in global state, and
introduce no skip flag.

## Streaming And Publication

Within each existing eligible streaming tile, solve constraints and run combined
validation before CSV encoding or writes. Reuse that operation's normalized rows
for whole-run primary-key checks rather than normalizing the tile again. Retain
sequence checks, cross-tile uniqueness, exact final counts, row/cell/time/byte
bounds, CSV formatting and the existing atomic bundle transaction. Keep original
rows for CSV encoding so normalization cannot change serialized values.

No generator random calls, seed namespaces, tile widths, manifest fields or
artifact names change. No additional dependency, eligibility rule, option or
automatic streaming threshold is needed.

## Verification And Evidence

Compare the combined report with standalone `validate_dataset` across report
settings and fail-fast cases; verify invalid candidates fail mandatory checks
before encoding with disabled report sections. Retain callback-mutation,
controlled-negative, caller-supplied-row, cleanup and original-data tests. Verify
byte-identical CSV and metadata for unchanged specifications and seeds, including
streaming worker counts and a partial final tile.

Update benchmark instrumentation to count executed shared evaluations and actual
row coverage rather than assert the former duplicate passes. Record fresh public
API timings, source hashes, stage accounting, output hashes and audits under
this change. The prior `public-streaming-csv/public-csv-results.json` and
`public-csv-benchmark.md` describe the measured earlier implementation and remain
unchanged; their recorded source hashes are historical, not assertions about a
later tree. Do not infer a speedup without new measurements.
