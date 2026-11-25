# Tasks

- [x] Implement explicit policy selection and bounded standard-library CSV
  streaming in the public bundle exporter; retain mandatory checks and legacy
  fallback limits.
- [x] Add spec-only `--stream-csv` / `--workers` CLI options and focused public
  contract, dispatch, error and metadata tests.
- [x] Record actual engine identity in existing manifest reproducibility evidence;
  retain default/fallback compatibility and matching verification checks.
- [x] Verify full tiled CSV equality across worker counts, scalar/quoting cases,
  cross-tile key failures, schema/privacy checks and report settings.
- [x] Verify incremental output/time bounds, destination safety, worker failure,
  cancellation and complete atomic bundle cleanup.
- [x] Verify base-package/installed CLI operation without PyArrow or DuckDB and
  retain source-profile, source-overlap, business-rule and MCP behavior.
- [x] Document opt-in usage, limits, fallback, seed semantics, module ownership,
  roadmap and unreleased behavior without adding a dependency or extra.
- [x] Run focused and full regression checks, type/lint/docs/OpenSpec validation
  and independent review; record evidence before release-candidate acceptance.
