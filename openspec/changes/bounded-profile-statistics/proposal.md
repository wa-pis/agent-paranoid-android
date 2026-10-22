# Change Proposal: bounded-profile-statistics

## Summary
Improve safe numeric/temporal/cardinality evidence and reduce repeated SQL scans
without increasing disclosure or permitting database writes.

## Motivation
The feedback's proposed magnitude truncation is incorrect: negative decimal
exponents represent subunit values. Sign plus maximum exponent alone cannot
describe mixed scales. Main already supports optional zero/subunit mass and a
minimum subunit exponent; verify those corrections and the provenance of profiles
that lack them before adding anything.
Parquet distinct counts are explicitly unknown; repeated query aggregates can
be expensive even though execution is bounded.

## Scope
P2: verify existing safe zero/subunit aggregates and their generation semantics; audit
decimal query coverage; bounded Parquet cardinality; temporal granularity;
category-budget recovery; measured query batching within existing work budgets.

Out of scope: exact sensitive extrema, raw values, temp tables/materialization,
unbounded scans, approximate counts labelled exact, or automatic source frequency
reproduction beyond reviewed aggregate semantics.

## Safety Impact
Keep existing suppression for sensitive numeric/temporal evidence. New aggregates
must have bounded validation and disclosure rules. Batch queries remain trusted,
read-only, authorized and charged against source/transport/invocation budgets.
Do not raise category limits or query budgets globally to make a probe pass.

## Compatibility
New statistics are optional and default to unknown for old profiles. Define
fingerprint/cache migration before adding fields; regenerate schema and golden
contracts where affected. Changed generation requires a candidate release.
