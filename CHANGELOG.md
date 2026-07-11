# Changelog

All notable changes to this project are documented here.

## Unreleased

### Added

- GitHub Actions quality gates for linting, compilation, tests, and an 85%
  coverage floor on Python 3.11 and 3.12.
- Hypothesis-based regression tests for SQL/PII and CSV safety boundaries.

## [0.3.0] - 2026-07-10

### Added

- A workspace-bounded generator MCP server with `profile_csv`,
  `infer_dataset_spec`, `generate_dataset`, `validate_dataset`, and
  `export_dataset` tools.
- Inline safe profile handoff from the Trino MCP workflow to DatasetSpec
  inference.
- Versioned `DatasetSpec` contract with `schema_version: "1.0"` and reference
  validation for entities, fields, relationships, constraints, and privacy
  rules.
- Synthetic generation manifests with seed, format, row counts, validation
  status, spec fingerprint, package/schema versions, and provenance flags.
- Runtime checks for unsafe sensitive profile distributions and exact source
  CSV row reuse.
- A safe Trino-profile to synthetic CSV demo and end-to-end coverage.

### Changed

- Synthetic emails now use `example.test`; phone and SSN-like values use
  explicitly reserved or invalid test ranges.
- DatasetSpec JSON artifacts are emitted as JSON when the output suffix is
  `.json`; YAML remains the default for `.yaml` and `.yml`.
- Legacy Trino profile JSON containing both `source_type` and `columns` is now
  routed correctly instead of being accepted as an empty DatasetProfile.

### Fixed

- Safe Trino SELECT validation now rejects CTEs, joins, subqueries, ordering,
  table functions, and likely PII hidden behind aliases.
- Generation size limits apply to direct and legacy generator APIs, not only
  CLI workflows.
- DatasetSpec business rules, primary-key uniqueness, relationship cardinality,
  typed conditional defaults, and aggregate count mappings are validated.
- CSV safety checks use detected encoding and delimiter; duplicate headers are
  rejected and Parquet preserves homogeneous scalar types.
- Generation bundles and profile caches use collision checks, atomic writes,
  and cache keys that include rule-sampling configuration.

## [0.2.0] - 2026-07-10

### Added

- Domain-agnostic `DatasetProfile` and `DatasetSpec` pipeline.
- Multi-entity deterministic generation, relationship reconciliation,
  constraint solving, and validation.
- Safe CSV-folder profiling, profile caching, and CSV/JSON/Parquet export.
- Compatibility adapters and deprecation warnings for legacy
  `GenerationSpec` workflows.

[0.3.0]: https://github.com/wa-pis/agent-paranoid-android/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/wa-pis/agent-paranoid-android/releases/tag/v0.2.0
