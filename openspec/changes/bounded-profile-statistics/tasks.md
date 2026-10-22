# Tasks
- [x] S1: Run existing fictional subunit/mixed-scale/all-zero tests and add missing boundary cases only; retain negative-exponent semantics and reject the truncation proposal.
- [x] S2: Verify existing optional prevalence metadata, denominator, malformed aggregate rejection, old-profile defaults and generation behavior; do not add duplicate fields.
- [ ] S3: Verify all SQL numeric summary builders and existing DECIMAL dispatch for consistent safe shape evidence, without extra raw-value queries.
- [ ] S4: Investigate provenance/version of external profiles missing supported metadata; implement only independently reproduced adapter gaps with safety regressions.
- [ ] S5: Add bounded Parquet distinct evidence with exact/lower-bound/unknown semantics; test row-group null statistics unavailable or malformed.
- [ ] S6: Specify bounded temporal granularity; reproduce the final report's apparent out-of-range date independently before treating it as a defect.
- [ ] S7: Verify category name/scope preflight; document bounded limit recovery and evaluate explicit capped configuration without silent truncation.
- [ ] S8: Measure per-column aggregate query costs with fake clients; batch only if the existing budgets and safety invariants are preserved.
- [ ] S9: Regenerate affected schemas/cache contracts, update docs/changelog and run candidate gates.
