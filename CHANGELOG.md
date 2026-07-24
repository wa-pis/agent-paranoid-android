# Changelog

All notable changes to this project are documented here.

## Unreleased

## [0.5.1] - 2026-07-24

### Added

- Tokenless PyPI publication through a dedicated GitHub OIDC workflow that
  publishes wheel and source distributions from an existing GitHub Release.
- Post-publication verification that compares PyPI SHA-256 digests with the
  GitHub Release distributions, installs the exact public-index package in an
  isolated environment, and runs its self-check.
- OpenSSF Scorecard analysis with results published to GitHub code scanning.
- Standard PyPI project links for documentation, issues, changelog, and release
  notes.

### Security

- PyPI publication uses a scoped `pypi` environment, job-level
  `id-token: write`, immutable action pins, published-release checks,
  tag-bound build-provenance verification, and independent distribution
  name/version validation before upload. Repository code does not execute in
  the OIDC-enabled publish job.
- Post-publication checks run without an OIDC token and fail if PyPI exposes
  missing, additional, yanked, renamed, or digest-mismatched distributions.

## [0.5.0] - 2026-07-24

### Added

- PEP 561 `py.typed` package metadata and strict mypy checks for the stable
  core, generation, and validation modules.
- Isolated installed-wheel smoke checks for package metadata, CLI entry
  points, and the `test-data-agent doctor` command.
- Pull-request dependency review that rejects newly introduced dependencies
  with known Moderate-or-higher vulnerabilities.
- Structured business-rule inputs for generator MCP generation and export,
  with workspace paths or bounded inline payloads.
- Business-rule fingerprints and compact validation summaries in generation
  manifests, with detailed bounded reports kept as workspace artifacts.

### Changed

- CI and the release gate now type-check the stable package core, and release
  publication verifies the built wheel before creating attestations.
- Business-rule models now reject unknown keys, dangling DatasetSpec
  references, unsafe sensitive literals, excessive input, and unsupported or
  overly complex formula syntax before generation.
- The package version is now `0.5.0`.

### Security

- CLI and MCP rule paths reject attempts to inject PII, credentials, tokens,
  or arbitrary string values through scenarios, enum rules, conditions, or
  formulas.
- Rule payload bytes, estimated row/rule evaluations, expression complexity,
  and detailed validation errors are bounded to prevent memory, CPU, disk, and
  model-context exhaustion.

## [0.4.0] - 2026-07-23

### Added

- Content-aware PII and credential detection for emails, phone numbers, SSNs,
  payment cards, JWTs, private keys, bearer tokens, known provider tokens, and
  high-entropy secrets, with a synthetic positive/negative regression corpus.
- Configurable limits for input files, rows, columns, cells, expanded Parquet
  data, YAML aliases/depth, generated artifact bytes, free-disk reserve, and
  wall-clock generation time.
- Live Trino integration tests against a digest-pinned official container.
- CodeQL SAST and full-history Gitleaks scanning with immutable action pins.
- Locked dependency resolution, hash-based vulnerability auditing, CycloneDX
  release SBOMs, SHA-256 checksums, GitHub build provenance, and SBOM
  attestations.
- Public disclosure and contribution guidance for AI-assisted development.

### Changed

- **Breaking:** the Trino MCP server now defaults to HTTPS and requires both
  catalog and schema allowlists. Intentionally unrestricted or plain-HTTP
  local environments must set the explicit override variables documented in
  README.
- Every Trino connection now applies validated server-side execution,
  run-time, and physical-scan budgets in addition to the client result-row cap.
- Dataset generation estimates output size before allocating rows and
  publishes review bundles only after validation and exact bundle-size checks.
- The build backend and GitHub Actions are version/SHA pinned; CI builds the
  project from the locked, non-editable environment.

### Security

- Sensitive values in neutral column names are masked or suppressed across CSV
  profiles, folder profiles, Trino profiles, masked samples, and imported
  profile JSON.
- CSV, JSON, YAML, and Parquet readers fail closed on oversized or deeply
  nested input; generated outputs reject symlinks and partial bundles are
  removed on quota, validation, or artifact failures.
- Trino SQL validation rejects work-expanding generic query shapes, likely PII
  projections, missing allowlists, insecure transport by default, and
  oversized client responses.

## [0.3.1] - 2026-07-21

### Added

- Agent Paranoid Android project naming, package metadata, and public
  attribution note for the Radiohead inspiration.
- Public release scaffolding: MIT license, security policy, contribution guide,
  GitHub issue and pull-request templates, Dependabot configuration, and
  publication checklist.
- Review-first agent orchestration with `agent-plan`, `agent-approve`, Python
  API models, documentation, and OpenSpec requirements.
- PlantUML architecture diagrams for the application overview, review-first
  agent workflow, and safety boundaries.
- MVP and release checklists, OpenSpec change templates, and golden-path CLI
  regression coverage for the README quickstart flow.
- Release smoke script, `test-data-agent doctor`, DatasetSpec JSON Schema, MCP
  examples, and release-process documentation.
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

[0.5.1]: https://github.com/wa-pis/agent-paranoid-android/compare/v0.5.0...v0.5.1
[0.5.0]: https://github.com/wa-pis/agent-paranoid-android/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/wa-pis/agent-paranoid-android/compare/v0.3.1...v0.4.0
[0.3.1]: https://github.com/wa-pis/agent-paranoid-android/compare/v0.3.0...v0.3.1
[0.3.0]: https://github.com/wa-pis/agent-paranoid-android/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/wa-pis/agent-paranoid-android/releases/tag/v0.2.0
