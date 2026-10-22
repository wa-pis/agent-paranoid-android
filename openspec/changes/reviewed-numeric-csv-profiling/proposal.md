# Change Proposal: reviewed-numeric-csv-profiling

## Summary
Provide a reviewed, field-scoped route for genuine CSV numeric measures that are
currently classified as phone-like strings. Preserve conservative defaults and
verify both the streaming accumulator and standalone column profiler.

## Motivation
External feedback #3 reproduces loss of numeric type and distributions. However,
positive numeric strings can also be phones, account identifiers or secrets;
numeric parsing and majority voting do not prove that a column is safe.

## Scope
P1 investigation and implementation: synthetic reproductions; typed explicit
numeric-measure declarations; bounded statistics; direct-service and CLI parity;
plan fingerprint, audit and provider-payload review. Reuse the existing reviewed
decimal field contract where possible instead of inventing a global bypass.

Out of scope: retaining raw sensitive numbers, name-based declassification,
weakening identifier/local-category gates, or copying source extrema into decimal
generation bounds. No new authority follows from a declaration alone.

## Safety Impact
Keep a rare credential, SSN or sensitive identifier protected even in an otherwise
numeric sample. Name-based sensitivity and finite-number checks remain enforced.
Only safe aggregate metadata may leave profiling. Any actual safety-policy change
requires explicit scoped approval and negative tests before activation.

## Compatibility
Additive opt-in only; no default reinterpretation of old profiles or approved
plans. A changed profile/spec fingerprint requires new review. Runtime privacy
changes require candidate release checks.
