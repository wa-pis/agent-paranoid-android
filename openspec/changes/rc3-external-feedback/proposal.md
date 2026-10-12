# RC3 external feedback corrections

## Why
External RC1 feedback identified silent flags/modes, ambiguous relationship
reporting, missing Parquet CLI access and rejected query LIMIT shapes.

## Scope
Build on RC2. Preserve no-row reuse, privacy, SQL allowlists and budgets.
Correct deterministic contracts and document compatibility changes in
`docs/rc3-feedback.md`. Publish only after exact-commit release acceptance.
