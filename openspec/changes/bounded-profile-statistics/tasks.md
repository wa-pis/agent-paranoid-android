# Tasks
- [x] S1: Run existing fictional subunit/mixed-scale/all-zero tests and add missing boundary cases only; retain negative-exponent semantics and reject the truncation proposal.
- [x] S2: Verify existing optional prevalence metadata, denominator, malformed aggregate rejection, old-profile defaults and generation behavior; do not add duplicate fields.
- [x] S3: Verify all SQL numeric summary builders and existing DECIMAL dispatch for consistent safe shape evidence, without extra raw-value queries.
- [ ] S4: Investigate provenance/version of external profiles missing supported metadata; implement only independently reproduced adapter gaps with safety regressions.
- [x] S5: Add bounded Parquet distinct evidence with exact/lower-bound/unknown semantics; test row-group null statistics unavailable or malformed.
- [x] S6: Specify bounded temporal granularity; reproduce the final report's apparent out-of-range date independently before treating it as a defect.
- [x] S7: Verify category name/scope preflight; document bounded limit recovery and evaluate explicit capped configuration without silent truncation.
- [x] S8: Measure per-column aggregate query costs with fake clients; batch only if the existing budgets and safety invariants are preserved.
  - [x] Measure narrow/wide query and Trino table profiles; verify existing PostgreSQL table counts.
  - [x] Evaluate a bounded batching design and retain separate invocation/scan accounting before implementation.
- [ ] S9: Regenerate affected schemas/cache contracts, update docs/changelog and run candidate gates.

S5 implementation and focused evidence are complete; full candidate CI remains
part of S9. No package release or live database verification is claimed.

S6 disposition: the independently reproduced long fractional-interval overshoot
is corrected with regression tests. Bounded month-start evidence/generation is
specified as a future reviewed extension in design.md, not an active inference
capability. The historical external date remains unconfirmed.

S7 disposition: bounded iteration, positive integer limits and pre-row-aggregate
category preflight are implemented. The default 20-category policy is retained;
recovery and a future field-scoped capped option are specified without activating
new preservation permissions. Full candidate CI remains in S9.
