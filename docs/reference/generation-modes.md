# Generation modes and folder replacement

These additions are under development after published RC3.

`edge` generates valid lower and upper numeric/decimal/date/time bounds,
zero when in range, both allowed booleans, all declared categories and string
length boundaries. Nullable fields with a positive null ratio include null cases.
Identifiers remain synthetic; constraint solving preserves declared uniqueness,
foreign keys, formulas and business rules, which can replace a field boundary
when it conflicts with another invariant. Row count stays unchanged: small
outputs cannot cover every boundary. Sensitive string fields retain safe
synthetic providers rather than source values. No invalid values are intentional.

`load_test` multiplies each entity's requested row count by
`generation_settings.load_multiplier` (default 10). Explicit CLI `--count` or
Python bundle `count` supplies the exact row count without multiplication.
Profile/CSV generation requires an explicit count and uses that count exactly.
Generation remains seeded and valid; all row, payload, disk and execution
budgets apply before allocation. An oversized request fails rather than truncates.
This mode produces data for load testing; it does not send traffic or run a benchmark.

DatasetSpec `generate --overwrite` replaces the entire destination folder,
including obsolete files. Without the flag, nonempty folders are rejected.
Generation, rules and validation finish before replacing existing output.
A sibling staging directory and previous-folder backup permit rollback on
publication failure. Directory replacement has a brief rename interval; it is
not a concurrent-reader atomic exchange. Do not modify the destination concurrently.
Symlinks and an output folder containing the input specification are rejected.
An interruption or a failure removing the previous folder can leave a hidden `.rollback`
folder; retain it until recovery is complete. Single-file generation keeps its
existing bundle-replacement contract. Transformation permissions do not change.

The default `load_multiplier` is omitted from serialization to preserve existing
specification fingerprints. Custom multipliers and materialized exact-count specs
change fingerprints and require fresh plan review.
