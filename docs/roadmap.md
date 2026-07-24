# Roadmap

The roadmap is ordered by safety and integration value, not by a fixed delivery
date.

## Implemented For 0.7.0

- Lightweight base installation with explicit `parquet`, `mcp`, `trino`, and
  `all` extras.
- Review-first allowlisted Trino planning through MCP without raw-SQL access
  on the default tool surface.
- HMAC-authenticated, metadata-only MCP audit records with integrity
  verification and bounded fail-closed storage.
- An explicit compatibility and deprecation policy for future DatasetSpec
  `schema_version` revisions.

## Implemented For 0.6.0

- One reviewed `DatasetSpec` contract across CLI and Python generation and
  validation workflows.
- Removal of the deprecated parallel specification API and conversion layer.
- Consistent `dataset_spec.json` and `dataset_spec.yaml` artifact names.
- A smaller project README backed by the published task-oriented documentation
  site.

## Implemented For 0.5.1

- Tokenless PyPI publication with post-publish digest comparison and a clean
  public-index installation smoke test.
- OpenSSF Scorecard reporting and expanded standard project links on PyPI.

## Implemented For 0.5.0

- Structured generator MCP business-rule inputs with strict contract checks,
  sensitive-literal rejection, bounded formulas, manifest fingerprints, and
  compact validation summaries.
- Typed package metadata, strict core/rules/MCP type checks, installed-wheel
  smoke coverage, and pull-request dependency review.

## Completed In 0.4.0

- Content-aware PII and secret detection across CSV, Trino, and imported
  profile trust boundaries.
- Configurable input, output-size, disk-reserve, execution-time, and Trino
  server-side query budgets.
- Locked dependencies, vulnerability auditing, CodeQL, full-history secret
  scanning, and live Trino integration coverage.
- Reproducible release artifacts with CycloneDX SBOMs, checksums, provenance,
  and SBOM attestations.

## Completed In 0.3.0

- Full MCP workflow for safe CSV profiling, spec inference, deterministic
  generation, validation, and export.
- Direct safe-profile handoff between Trino and generator MCP tools.
- Versioned DatasetSpec contract and auditable generation manifests.
- Runtime raw-profile and source-row reuse protections.
- End-to-end AI integration demo.
- Review-first agent orchestration with `agent-plan` and `agent-approve`.

## MVP Freeze

Keep the current MVP focused on the reliable golden path:

- CSV file or CSV folder input.
- Safe profile metadata, not source rows.
- Reviewable `DatasetSpec`.
- Deterministic generation by explicit seed.
- CSV, JSON, and Parquet export.
- Validation report and generation manifest.
- MCP responses that return summaries and artifact paths, not dataset rows.

Treat these as non-negotiable release gates rather than new feature work:

- `ruff`, `compileall`, and the full pytest suite pass.
- Quickstart commands in README run against checked-in fixtures.
- Generated manifests report `synthetic: true` and
  `source_rows_copied: false`.
- OpenSpec baseline stays aligned with implemented behavior.

## Later

- Pluggable synthetic providers for organization-specific semantic types.
- More cross-table aggregate constraints and controlled negative scenarios.
- Packaging and deployment examples for isolated MCP workers.
