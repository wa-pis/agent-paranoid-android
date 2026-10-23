# Tasks
- [x] N1: Reproduce #3 on both CSV profiler paths with fictional measures and verify current privacy behavior.
- [x] N2: Decide and specify the smallest reviewed numeric declaration using the existing decimal/numeric_measure contract where possible.
- [x] N3: Enforce typed, finite, bounded parsing at the deterministic service boundary; retain sensitive names and identifier protections.
  - [x] Reject nonfinite/overflowing float text in the shared parser and invalidate pre-fix folder caches.
  - [x] Complete the reviewed numeric declaration decision and its boundary checks.
- [x] N4: Test formatted phones, numeric secrets, late outliers, mixed types and float normalization; no majority-based bypass.
- [x] N5: Verify source-free profile/spec artifacts, plan fingerprints, CLI and provider summaries.
- [x] N6: Update safe-csv-profiling baseline, public guides, schema if affected, changelog and migration notes.
- [x] N7: Run focused safety tests, types, lint and complete candidate gates before release.


N7 checkpoint: #645 passed full green CI and merged as
`80145958b579540b6852c6860de27f41a591c79d`. The subsequent combined exact-source
candidate release gate passed before #646 (4603 tests; 91.90% coverage).
This records candidate checks, not authorization to publish a package.
