# Changelog

All notable changes to this project are documented here.

## Unreleased

### Added

- Cross-table average aggregate mappings across deterministic generation,
  validation, safe profile inference, and read-only Trino profiling.
- Deterministic controlled negative generation across required, allowed-value,
  numeric-bound, conditional, temporal, and formula business rules.
- Coordinated negative foreign-key and concrete-field aggregate-formula cases
  that preserve unrelated rows and parent tables.
- Bounded expected-versus-observed violation counts in business-validation
  reports and generation manifests for controlled invalid datasets.
- A checked-in controlled-invalid example with tested CLI/MCP reproducibility
  from one spec, rule file, seed, mode, and invalid ratio.
- A public stability table mapping Python, CLI, MCP, `DatasetSpec`, advisor,
  and artifact contracts to owners, compatibility rules, and test gates.
- A versioned catalog covering every golden JSON and MCP fixture with enforced
  additive-only or schema-versioned change rules.
- A compatibility inventory for retained CLI aliases, legacy Python wrappers,
  transitional model access, migration targets, and minimum support windows.
- Immutable `v0.11.0` spec and manifest fixtures proving current readers and
  deterministic generation remain compatible with the previous feature release.
- A public support policy for CPython versions, optional extras, provider
  adapter maturity, compatibility notices, and release gates.
- Bounded release regressions for profiling, multi-entity generation, and
  validation wall time and peak traced allocations.
- Staged timeout cleanup coverage for folder, review, and single-entity
  generation outputs.
- A real Parquet `doctor` capability smoke that generates and reads a temporary
  bundle with secret-free reinstall guidance on failure.
- A local MCP `doctor` capability smoke that constructs the generator
  transport and verifies audited tool registration without starting a server.
- A local Trino `doctor` capability smoke that validates allowlisted SQL and
  constructs a client without executing a query or contacting a coordinator.
- A local OpenAI `doctor` capability smoke that verifies the structured SDK
  surface and advisor construction without credentials or provider requests.
- Isolated base-wheel build, installation, metadata, size, and `doctor` smoke
  coverage on every supported Python version from 3.11 through 3.14.
- ARM64 pull-request build and hardened runtime health checks for every CLI,
  generator MCP, and Trino MCP container target.
- Blocking container scans for fixable High and Critical vulnerabilities in
  every native CLI and MCP target before publication.
- A fail-closed dependency-license gate for application, optional, development,
  and documentation environments without adding a scanner dependency.
- A dated security review with scanner evidence and explicit dispositions for
  all remaining OpenSSF Scorecard governance and maturity findings.
- Canonical OpenSpec requirements for behavior-preserving CLI boundaries and
  safety-equivalent direct/MCP application services, with the completed change
  archived for the 1.0 contract freeze.
- A canonical public-contracts OpenSpec capability covering retained aliases,
  wrappers, migration targets, and minimum deprecation windows.
- The completed public stability map merged into the canonical public-contracts
  OpenSpec capability and archived with its implementation evidence.
- The completed versioned golden-contract catalog merged into canonical
  OpenSpec and archived with its compatibility evidence.
- Previous feature-release fixture compatibility merged into canonical
  OpenSpec and archived with its immutable provenance evidence.
- Runtime, optional-extra, and provider-adapter support policy merged into
  canonical OpenSpec and archived with its release-gate evidence.
- A canonical public Python API capability covering reviewed top-level exports,
  with the completed golden-contract change archived.
- A canonical artifact-contract capability covering stable generation bundle
  filenames and metadata-only validation report fixtures.
- A canonical MCP interface capability covering stable discovery schemas and
  the default exclusion of unrestricted raw SQL.
- Cross-table average reconciliation merged into canonical synthetic-generation
  OpenSpec and archived with its deterministic and aggregate-only evidence.
- Controlled negative field and row-rule coverage merged into canonical
  synthetic-generation OpenSpec and archived with deterministic evidence.
- Controlled foreign-key and aggregate-formula negative cases merged into
  canonical synthetic-generation OpenSpec and archived with isolation evidence.
- Bounded expected-versus-observed negative validation artifacts merged into
  canonical synthetic-generation OpenSpec and archived with privacy evidence.
- CLI and generator MCP negative-case reproducibility merged into canonical
  synthetic-generation OpenSpec and archived with executable example evidence.
- A canonical operational-readiness capability covering bounded synthetic
  profiling, generation, and validation resource regression gates.
- Fail-closed path-aware CI classification that keeps strict documentation
  checks while skipping heavy Python, container, and security jobs for docs-only
  pull requests and main pushes.

### Fixed

- Low-level Trino execution helpers are private; public SQL access remains
  limited to validated safe-select and dedicated bounded profiling methods.
- Mocked-cursor regressions prove forbidden and non-allowlisted SQL is rejected
  before a Trino connection or cursor execution can occur.
- Contract tests preserve allowlisted metadata discovery and aggregate-only
  Trino profiling through dedicated internal query builders.
- Agent input detection requirements are merged into canonical orchestration
  OpenSpec and the completed change is archived with its implementation evidence.
- Direct Python generation now rejects specs containing raw-looking sensitive
  categories, unsafe sensitive distributions, or privacy-policy opt-outs.
- CLI and generator MCP regressions verify malicious on-disk specs fail before
  artifact creation and never echo rejected sensitive values.
- Lightweight no-op Python matrix checks for docs-only changes so existing
  branch-protection requirements are reported instead of remaining pending.

- MCP extras exclude the incompatible 2.x SDK until the transport migrates to
  its replacement API.
- Incomplete staged generation and review bundles are removed when interactive
  cancellation interrupts writing or validation.
- Mid-write disk exhaustion removes partial staged folder, review, and
  single-entity output without publishing success metadata.
- Interrupted folder publication removes the renamed destination, while
  interrupted single-entity publication restores replaced files and removes
  partial new output.
- A versioned delivery plan from `0.13.0` through `1.0.0`, with explicit scope,
  exit criteria, release gates, and deferred work.
- An ordered remaining-work checklist from completed feature scopes through
  OpenSpec closure, RC security review, public artifact verification, and 1.0.

## [0.12.0] - 2026-07-31

### Added

- Generated CLI parser-surface contract coverage for public commands, aliases,
  and agent workflow defaults ahead of the 0.12 interface refactor.
- A golden contract for the supported top-level Python export surface.
- Golden contracts for generation bundle filenames and validation reports.
- Golden contracts for generator and Trino MCP tool names and JSON schemas.
- A row-free semantic value provider contract with fail-closed validation for
  organization-specific synthetic values.

### Changed

- Expanded the supported CPython CI matrix from 3.11-3.12 to 3.11-3.14 and
  moved isolated wheel smoke tests to Python 3.14.
- Moved reusable argparse behavior, argument validators, recovery hints, and
  structured parser errors behind a dedicated CLI parsing boundary.
- Moved review-gated agent command registration behind the same parsing
  boundary without changing command names, options, defaults, or help.
- Moved dataset, validation, environment, audit, and examples command
  registration behind the CLI parsing boundary while preserving the public
  parser contract.
- Moved CLI error and validation-result rendering behind a dedicated
  presentation boundary without changing stdout, stderr, JSON, or exit-code
  behavior.
- Moved review-first agent human summaries and JSON document rendering behind
  the same presentation boundary while preserving output contracts.
- Moved examples, audit verification, and doctor output behind the
  presentation boundary, with typed doctor results separating checks from
  rendering.
- Separated generator MCP transport registration and audit wrapping from
  application services while preserving tool order and public contracts.
- Separated Trino MCP transport registration and audit wrapping from the
  allowlisted application services and opt-in safe SELECT policy.
- Added direct-service boundary tests proving unsafe workspace paths and Trino
  SQL are rejected before filesystem or database I/O.
- Documented the stable CLI, MCP transport, and application-safety boundaries
  in the implementation map and contributor workflow.

## [0.11.0] - 2026-07-31

### Added

- Guided provider-backed CLI flow with `agent-advise`, lazy optional OpenAI
  loading, structured proposal validation, and explicit review guidance before
  and after advice.
- Deterministic row-free golden fixtures for CLI JSON, MCP responses,
  `DatasetSpec`, advisor exchanges, and generation manifests, with an explicit
  review-first update command.

## [0.10.0] - 2026-07-30

### Added

- Optional OpenAI Responses API advisor with structured `AdvisorProposal`
  output, separate trusted and untrusted roles, bounded non-streaming requests,
  disabled response storage, provider-error redaction, reference-agent
  selection, and isolated dependency-budget coverage.
- Provider adapter guide covering the Python protocol, versioned JSON wire
  format, trust-channel mapping, implementation template, safety requirements,
  compatibility rules, and contract-test checklist.

### Changed

- Updated `docker/login-action` from 4.5.1 to 4.6.0 while retaining an
  immutable full-commit pin and matching workflow contract test.

## [0.9.0] - 2026-07-29

### Added

- Read-only `agent-status` inspection for planned and completed agent
  workspaces, with concise human output and a versioned `--json` contract.
- Automatic `agent-plan` source detection for CSV files, CSV folders, and
  validated safe-profile JSON, while retaining `--source-type` as an override.
- Metadata-only `agent-plan` review summaries covering inferred fields,
  sensitive classifications, relationships, confidence, assumptions, and
  safety warnings, with escaped untrusted names.
- Versioned `--json` results for `agent-plan` and `agent-approve`, plus
  structured machine-readable argument, input, and path errors across all
  three agent commands.
- Fingerprint-bound agent approval with random plan identifiers, profile and
  effective-spec SHA-256 values, read-only MCP plan inspection, and persisted
  `approval_receipt.json` records.
- Recoverable agent approvals with an atomic completion checkpoint,
  `recovery_required` status, CLI/Python/MCP recovery operations, full bounded
  bundle revalidation, and idempotent repeated approval.
- High-level generator MCP `plan_dataset` orchestration for workspace CSV
  files, CSV folders, and safe profiles, with automatic source detection and
  the existing review, approval, status, and recovery gates.
- Provider-neutral `DatasetAdvisor` request and proposal contracts with safe
  metadata-only input, fingerprint binding, strict proposal validation, and
  no provider SDK dependency or generation side effect.
- Recoverable `advise_agent_workspace` handoff with atomic
  `advisor_review.json` and `dataset_spec.yaml` persistence, conflict-safe
  retries, current-spec status summaries, and the existing approval gate.
- Provider-neutral `agent-advisor-request` and `agent-advisor-apply` JSON
  handoff for external model clients, with bounded proposal input, stale and
  conflicting content rejection, and no provider SDK dependency.
- Self-describing `AdvisorExchange` export with immutable trusted instructions,
  explicitly untrusted request metadata, and generated `AdvisorProposal` JSON
  Schema.
- Provider-neutral `ExchangeDatasetAdvisor` for application-owned
  structured-output clients, with defensive exchange copying and validation
  against the original fingerprint-bound request.
- Runnable review-first reference agent covering safe planning, advisor
  proposal persistence, read-only status, exact-fingerprint human approval,
  deterministic generation, and validation without a provider SDK.
- Read-only `agent-review` CLI and Python report with detailed field,
  relationship, privacy, and fingerprint metadata, bounded human output, and a
  versioned row-free JSON contract.

### Changed

- Updated the Docker build, registry login, and QEMU GitHub Actions to
  immutable Node.js 24-compatible releases.

## [0.8.1] - 2026-07-28

### Added

- Independent installation smoke tests for the base package and the Parquet,
  MCP, and Trino extras.
- Dependency-count and wheel-size budgets for release artifacts.
- Typed `AgentPlanSummary` and `AgentGenerationSummary` result models while
  retaining the existing serialized JSON and dict-style reads.

### Changed

- Aligned AI prompts and integration documentation with the review-first
  `DatasetSpec`, approval, output-format, and artifact-only MCP contracts.
- Extended strict type checking to the CLI and agent-facing interfaces.
- Documented `all` as a development, demo, and container convenience rather
  than the recommended installation.

## [0.8.0] - 2026-07-26

### Added

- Separate minimal OCI targets for the CLI, generator MCP server, and Trino MCP
  server, with non-root users and target-specific health checks.
- A hardened Compose deployment with read-only root filesystems, dropped
  capabilities, bounded resources, generator network isolation, narrow mounts,
  and Docker secret-backed audit logging.
- Tag-only multi-platform GHCR publication with BuildKit SBOM and provenance,
  GitHub artifact attestations, and keyless Cosign signatures.
- `TEST_DATA_AGENT_AUDIT_HMAC_KEY_FILE` as a bounded, no-follow alternative to
  placing an audit key directly in process environment.

### Security

- Container targets exclude dependencies and mounts outside their role: the
  generator has no Trino stack or network, and the Trino worker has no
  generator workspace.
- Base images and GitHub Actions are pinned to immutable digests or commit
  SHAs; pull-request jobs have no registry write permission.

## [0.7.1] - 2026-07-26

### Changed

- Running `test-data-agent` without a command now prints a guided start screen
  instead of failing with a missing-command parser error.
- `generate` reports the valid DatasetSpec and safe-profile forms when its
  input is missing or ambiguous.
- CLI argument and command errors now point to the exact contextual `--help`
  command for recovery.

### Added

- Added `test-data-agent examples` with copy-ready CSV, folder, DatasetSpec,
  safe-profile, agent-review, and validation workflows.
- Added `test-data-agent --version` and examples to command-specific help.
- Expanded the CLI reference and README discovery instructions.

## [0.7.0] - 2026-07-24

### Added

- Optional installation groups for Parquet, MCP, Trino, and the complete
  integration set.
- A documented, fail-closed DatasetSpec compatibility and deprecation policy
  with an explicit supported-version registry.
- Metadata-only MCP audit records authenticated with an HMAC-SHA256 hash
  chain, plus `audit-verify` integrity checks and bounded secure file handling.
- Review-first `plan_trino_dataset` and `approve_dataset_plan` MCP tools for
  turning safe Trino profiles into approved synthetic generation.

### Changed

- The base installation now requires only Faker, Pydantic, and PyYAML.
- `doctor` reports optional features without failing unless they are requested
  through `--require-extra`.
- Trino's generic `run_safe_select` MCP tool is disabled by default and
  requires the explicit `TRINO_ENABLE_SAFE_SELECT=true` opt-in.
- Inline MCP profile payloads are size-bounded before validation.

### Security

- Enabled audit deployments fail before MCP tool execution when the log path,
  key, permissions, link state, or size limit is unsafe.
- Audit events exclude tool arguments, SQL, profiles, rows, return values, and
  exception messages.
- Unknown DatasetSpec schema versions fail before generation or validation.

## [0.6.0] - 2026-07-24

### Breaking Changes

- `DatasetSpec` is now the only supported generation and validation contract.
  The deprecated `GenerationSpec` models, converters, generators,
  validators, CLI fallback, and package-root exports have been removed.
- `validate` now requires a generated dataset folder rather than a
  single-table row file.
- Single-CSV workflows now write the effective spec as `dataset_spec.json`
  instead of `generation_spec.json`.

### Changed

- Safe profile payloads with top-level `columns` remain supported, but they are
  normalized directly into `DatasetProfile` and then processed through the
  `DatasetSpec` pipeline.
- Removed specification files fail before generation or validation with a
  link to the `0.6.0` migration guide.
- The package version is now `0.6.0`.

### Removed

- Deleted the retired specification, row generator, row validator,
  compatibility adapters, compatibility package, and completed refactoring
  script.

### Fixed

- Tag releases now dispatch the dedicated PyPI workflow instead of invoking it
  as a reusable workflow, keeping GitHub's attestation Build Config URI aligned
  with the PyPI Trusted Publisher configuration.
- Post-publication installation now waits for the PyPI simple index to expose
  the new version after its JSON metadata and files become available.

### Security

- Release workflows now deny token permissions by default and isolate
  `contents: write` in the GitHub Release job, after build and attestation.
- Public PyPI verification now installs locked runtime dependencies and the
  exact published wheel with mandatory SHA-256 hashes.

### Documentation

- Replaced the monolithic README with a focused installation and quickstart
  entry point.
- Added task-oriented guides for first generation, multi-table datasets,
  artifact review, business rules, MCP setup, safety, configuration, and
  troubleshooting.
- Added a searchable MkDocs site with strict link validation and a dedicated
  documentation CI build.
- Added GitHub Pages deployment from `main` with least-privilege permissions
  and a post-deployment public availability check.
- Added a `0.6.0` migration guide, updated architecture and OpenSpec contracts,
  and reduced README to a concise project entry point with a prominent
  documentation link.

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

[0.12.0]: https://github.com/wa-pis/agent-paranoid-android/compare/v0.11.0...v0.12.0
[0.11.0]: https://github.com/wa-pis/agent-paranoid-android/compare/v0.10.0...v0.11.0
[0.10.0]: https://github.com/wa-pis/agent-paranoid-android/compare/v0.9.0...v0.10.0
[0.9.0]: https://github.com/wa-pis/agent-paranoid-android/compare/v0.8.1...v0.9.0
[0.8.1]: https://github.com/wa-pis/agent-paranoid-android/compare/v0.8.0...v0.8.1
[0.8.0]: https://github.com/wa-pis/agent-paranoid-android/compare/v0.7.1...v0.8.0
[0.7.1]: https://github.com/wa-pis/agent-paranoid-android/compare/v0.7.0...v0.7.1
[0.7.0]: https://github.com/wa-pis/agent-paranoid-android/compare/v0.6.0...v0.7.0
[0.6.0]: https://github.com/wa-pis/agent-paranoid-android/compare/v0.5.1...v0.6.0
[0.5.1]: https://github.com/wa-pis/agent-paranoid-android/compare/v0.5.0...v0.5.1
[0.5.0]: https://github.com/wa-pis/agent-paranoid-android/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/wa-pis/agent-paranoid-android/compare/v0.3.1...v0.4.0
[0.3.1]: https://github.com/wa-pis/agent-paranoid-android/compare/v0.3.0...v0.3.1
[0.3.0]: https://github.com/wa-pis/agent-paranoid-android/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/wa-pis/agent-paranoid-android/releases/tag/v0.2.0
