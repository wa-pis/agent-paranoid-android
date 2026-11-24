# Tasks

- [x] Replace the frozen active-OpenSpec directory list with structural checks.
- [x] Normalize validation values and cover malformed row/key inputs.
- [x] Share precise numeric comparisons and integer aggregates.
- [x] Order formula/aggregate dependencies and test failure publication behavior.
- [x] Reconcile documentation and remove duplicated Trino env parsing.
- [x] Run focused, contract, lint, type and full regression checks.

Local acceptance: final full pytest 1837 passed / 10 skipped;
Ruff, mypy (121 source files), contract fixtures
and strict MkDocs build passed. No release, live service or PyPI verification
is claimed. Merge and release-candidate review remain separate from this change.
