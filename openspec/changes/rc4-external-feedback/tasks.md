# Tasks

- [x] Reproduce and classify report claims on current source.
- [x] Repair Trino decimal metadata and reviewed inference range handoff.
- [x] Add coarse numeric shape prevalence and generation coverage.
- [x] Implement scoped reviewed decimal numeric-measure semantics with privacy vetoes.
- [x] Make rule assignment/checking explicit, conditions expressive and SQL export consistent.
- [x] Improve generation UX and value-free diagnostics; document reproducibility and negative artifacts.
- [x] Add regression tests, documentation and regenerate public schemas/contracts.
- [x] Run full release gate and prepare reviewable changes; no publication.

Validation: `openspec validate rc4-external-feedback --strict` passed.
`scripts/check_release.sh`: 3393 passed, 23 skipped, 91.11% coverage;
lint, types, licenses, dependency policy, schema freshness, resource budgets
and quickstart all passed. Tests use fictional data; live database access was not used.
