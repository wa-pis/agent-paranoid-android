# Tasks

- [x] Remove the folder-only distinct ceiling and retain internal fingerprints.
- [x] Recompute old cached counts with cache format 5.
- [x] Cover more than 10,000 unique values, late duplicates and repeated-key pools.
- [x] Update profiling guidance, limits, roadmap and unreleased notes.
- [x] Run focused profiling, budget, compatibility and documentation checks.

Acceptance: 61 focused profiling/budget/contract checks, 49 documentation checks,
full pytest 1839 passed / 10 skipped, and 12 final distinct regressions including
a near-unique late duplicate. Ruff, mypy and strict MkDocs build passed.
No live service, publication or installed-release verification was performed.
