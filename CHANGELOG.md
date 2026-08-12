# Changelog

All notable changes to this project are documented here.

## Unreleased

### Added

- Add an explicit experimental GigaChat advisor through the official Python
  SDK, its optional `gigachat` extra, local-only doctor smoke, and the existing
  review-gated `agent-advise --provider gigachat` workflow.

### Fixed

- Replace only identity-matched GigaChat beta structured-output failures with
  the validated local baseline before repeating full proposal and core checks.

### Security

- Keep GigaChat on fixed verified-TLS endpoints with runtime-only mutually
  exclusive authentication, bounded requests and responses, strict structured
  output, redacted failures, and no source-row or exact preserved-literal
  egress.

## [1.0.0] - 2026-08-12

### Changed

- Promote the accepted RC6 runtime and public contracts to the first stable
  compatibility baseline without changing runtime behavior.

## [1.0.0rc6] - 2026-08-11

### Added

- Add an allowlist-only `profile-postgres` CLI workflow that writes safe
  metadata and bounded aggregate profiles through the optional PostgreSQL driver.
- Add a typed field-scoped local category allowlist across CSV, folder, agent,
  CLI, profile, and generation-spec boundaries without weakening default
  category replacement.
- Add `export-postgres-sql` for one deterministic, atomically published
  PostgreSQL transaction containing quoted DDL, foreign keys, and INSERT
  statements generated from validated synthetic records.
- Add complete PostgreSQL and Trino guides plus runnable synthetic local
  examples for disposable profiling, generation, validation, and SQL execution.
- Add field-scoped, collision-safe placeholders for rare categorical values.
- Add typed per-call OpenAI structured completion results and failure metadata;
  retain `last_run_metadata` only as a legacy compatibility view.
- Add `trusted-local` and `shared-hardened` Trino deployment profiles, with a
  required finite cumulative scan ceiling for shared environments.
- Add bounded Trino deployment profile and effective scan-limit status to
  `doctor`.

### Changed

- Restore field-and-destination privacy policy: preserve explicitly allowlisted
  safe business enums locally, keep sensitive and unknown fields transformed,
  and keep every external-provider category source-literal free.
- Bind review-first CSV agent plans and final no-copy validation to the exact
  source version captured before profiling, rejecting changed or legacy
  unbound plans before publication.

### Fixed

- Validate JSON dataset fields by membership rather than object-key order, so
  deterministic sorted-key artifacts pass the documented standalone
  validation command.

### Security

- Document four accepted Low security findings with exact identities, risk
  ownership, revisit triggers, and a first post-1.0 hardening target.
- Pin the Dockerfile frontend to the immutable multi-platform digest behind
  `docker/dockerfile:1.7`.
- Bind single-CSV no-copy validation to SHA-256 row digests collected during
  the same read that produced the profile, so path replacement cannot switch
  the checked source before publication.
- Reject entity names reserved for generation control artifacts during spec
  validation and again before any dataset file is written.
- Reject duplicate entity stems across CSV, JSON, and Parquet dataset folders
  before any row artifact is read.
- Check local CSV profiling deadlines between individual field-processing and
  field-finalization operations.
- Reserve bounded terminal audit capacity before MCP tool execution so a full
  log rejects admission instead of losing the completion event.
- Replace source-derived CSV-folder text categories with collision-safe rank
  labels before caching, spec inference, or generation while preserving counts
  and conditional-rule semantics.
- Replace source-derived advisor constraint literals with the same field-scoped
  category labels, reject unrepresented strings, and preserve executable
  conditions across persisted-review verification.
- Replace every provider-bound categorical JSON scalar with a deterministic
  field-scoped label while preserving numeric distribution bounds.
- Recursively mask strings in bounded composite `run_safe_select` values so
  nested Trino maps, arrays, and rows cannot bypass the opt-in row policy.
- Prevent equal rare values in different fields from sharing a synthetic
  placeholder and prevent placeholders from colliding with normal categories,
  including placeholder-shaped baseline literals, while preserving sanitizer
  provenance across reordered baseline categories.
- Keep provider metadata attached to the invocation that produced it, including
  preflight and provider-error paths, without retaining prompts or source data.
- Detach handled OpenAI provider and validation failures from their original
  cause/context chains, and replace incomplete-response status text with a
  fixed bounded local error.
- Reject advisor formulas with string constants, unknown or incompatible
  references, and protected targets; enforce fixed post-solve type and privacy
  checks before generated rows reach publication adapters.
- Run generator MCP over the bounded stdio transport with fresh shared request
  budgets, bounded final responses, and pre-materialization JSON structure
  limits.
- Restrict public artifact names to safe path components, neutralize
  spreadsheet formula markers in CSV cells, and replace formula diagnostics
  with fixed local reasons.
- Bound active MCP requests and shared Trino operations process-wide, return a
  fixed capacity error, and release admission state on every terminal path.
- Replace backend-controlled Trino failures with a fixed detached MCP error and
  expose catalog/schema discovery only through configured allowlists.
- Mask every string returned by the explicit opt-in `run_safe_select` surface,
  including names and addresses missed by heuristic classification.
- Isolate semantic-provider calls behind a fixed deadline, require matching
  same-seed replay, and restrict string output to the `synthetic_` namespace.
- Publish files, folders, caches, and agent workspaces through one no-follow,
  descriptor-relative path policy that revalidates inode identity before
  replacement and cleanup.
- Publish single-entity manifests last, verify recorded artifact hashes before
  reporting completion, and require explicit overwrite approval for every
  replaced sibling artifact.
- Escape and bound untrusted CLI diagnostics, paths, provider metadata, and
  row-count labels, while preserving structured JSON errors and bounded
  canonical audit records.
- RC6 acceptance additionally requires source-free external advisor payloads,
  suppression of exact sensitive numeric profile metrics, semantically
  validated provider constraints, bounded generator MCP framing and JSON
  materialization, bounded active requests, explicit opt-in row privacy,
  semantic-provider and filesystem boundaries, safe CSV/artifact boundaries,
  escaped diagnostics, trusted release identity, and external acceptance
  evidence.

## [1.0.0rc5] - 2026-08-08

### Added

- Add bounded typed OpenAI advisor settings for model, reasoning effort,
  input bytes, output tokens, timeout, retries, and optional service tier.
- Add bounded in-memory OpenAI advisor run metadata for settings, sizes,
  latency, status, provider-reported retries, and token usage.
- Add a separate OpenAI relationship-candidate ranking adapter that accepts
  only bounded deterministic candidates and returns review-required proposals.
- Add explicit bounded fast, normal, and quality OpenAI advisor candidate
  presets without changing constructor defaults before benchmark evidence.
- Add a synthetic-only OpenAI advisor preset benchmark runner with explicit
  pricing inputs and redacted aggregate quality, latency, usage, and cost data.
- Expand the advisor acceptance runner to five synthetic profile shapes and an
  explicit bounded run count with p50/p95, error, retry, token, and cost metrics.

### Changed

- Use GPT-5.6 reasoning effort `none` for the fast advisor candidate while
  retaining the legacy typed `minimal` value for compatibility.
- Select the benchmark-backed fast advisor settings as the constructor defaults:
  4,096 output tokens, a 15-second timeout, and no SDK retries.
- Complete the 60-call RC5 advisor acceptance benchmark across five synthetic
  profile shapes with 100% validity and safety preservation, no errors or
  timeouts, and aggregate latency, token, retry-reporting, and cost evidence.

### Fixed

- Send the advisor's public free-form-compatible JSON Schema in non-strict mode
  and fail closed through local typed validation of every provider response.

### Security

- Bound JSON-RPC request IDs by their serialized UTF-8 size before they can be
  reflected in Trino MCP success or error responses.
- Replace oversized Trino MCP responses with a fixed bounded JSON-RPC error and
  reject transport-response limits too small to reserve that error.
- Cover wide-row database overflow and final JSON-RPC growth from nested
  metadata and escaping with explicit response-budget regression tests.
- Add typed cumulative profiled-column, invocation-deadline, and optional
  estimated-scan limits to the shared Trino invocation budget.
- Set benchmark-backed Trino invocation defaults of 100 profiled columns, 150
  statements, and 120 seconds.
- Enforce profiled-column, statement, deadline, and conservative scan estimates
  through one monotonic budget across nested Trino table profiling.
- Clamp Trino HTTP, execution, and run timeouts to the remaining invocation
  deadline and close active query resources when it expires.
- Add fail-closed environment configuration and scope documentation for Trino
  invocation column, statement, deadline, and optional scan limits.
- Bound each fresh local CSV-folder profile with typed deadline, sample, input
  byte, and cell limits, leaving no partial metadata cache after exhaustion.
- Count trusted instructions, untrusted metadata, structured-output schema,
  settings, and serialization in the OpenAI advisor request budget.
- Reject non-protocol JSON-RPC request IDs before dispatch and isolate active
  request budgets by exact serialized ID type and value.

## [1.0.0rc4] - 2026-08-02

### Changed

- Remove the `sample_rows_masked` Trino MCP tool, masking-service method, and
  query builder from the RC4 compatibility surface.
- Pin RC4 installation guidance and optional extras to `1.0.0rc4`, with a
  tag-matched clean-environment README smoke gate for the public wheel.
- Verify installed-wheel CSV and JSON quickstarts without optional integration
  dependencies, and isolate Trino-extra failures in a separate CI check.
- Document the exact aggregate-only default Trino MCP surface and classify the
  separately enabled safe-select rows as potentially containing source values.
- Define atomic visibility and process-interruption recovery separately from
  crash durability, with artifact fsync explicitly deferred until after 1.0.
- Define stable 1.0 promotion as the accepted RC4 production tree plus only
  reviewed version, changelog, and release-metadata updates; any code or
  dependency change requires another release candidate.

### Security

- Remove the row-returning diagnostic path instead of relying on heuristic
  masking to prevent unknown source literals from reaching MCP clients.
- Create a concurrency-isolated work budget for every Trino MCP invocation and
  reject canonical application arguments over 256 KiB before tool execution.
- Reject raw Trino MCP stdio payloads over 1 MiB before JSON-RPC argument
  parsing, without retaining the complete oversized frame in memory.
- Bound cumulative SQL and formula character work before Python/sqlglot
  parsing and before opening a Trino connection.
- Bound cumulative Python and sqlglot AST nodes and maximum depth before
  formula rendering, policy traversal, or Trino query execution.
- Bound cumulative explicit SQL projections before opening a Trino connection
  and fail closed when a projection wildcard has unknown width.
- Bound cumulative parsed SQL statements before opening a Trino connection or
  cursor.
- Consume Trino response metadata and rows incrementally against the shared
  byte budget before retaining a complete oversized result.
- Share one monotonic budget across nested table/column profiling and opt-in
  safe SELECT execution, stopping before later Trino work after exhaustion.

### Migration

- MCP clients that called `sample_rows_masked` must use metadata and aggregate
  profiling tools such as `describe_table`, `profile_table_safe`, and
  `profile_column`. The separate `run_safe_select` tool remains explicit
  operator opt-in and is not a source-literal-free replacement.

## [1.0.0rc3] - 2026-08-02

### Added

- Add a manual post-publish gate that verifies immutable GitHub Release, PyPI,
  documentation, and signed multi-platform GHCR artifacts, then exercises
  agent approval and audit verification from the public wheel.

### Changed

- Preserve public Python, CLI, MCP, artifact, error, and safety contracts while
  moving workspace, agent lifecycle, CLI, and Trino ownership behind typed
  application boundaries. No user migration is required.

### Security

- Enforce spec safety inside the agent approval service before calling an
  injected generation port.
- Reject symlinked agent workspace targets at the persistence boundary before
  creating plan staging artifacts.

## [1.0.0rc2] - 2026-08-01

### Fixed

- Publish release-candidate container images with their PEP 440 package version
  while reserving floating major, minor, and `latest` tags for stable releases.

## [1.0.0rc1] - 2026-08-01

### Added

- Added a [disposable local Trino journey](examples/local_trino/README.md) that
  profiles the built-in synthetic TPC-H catalog through bounded operations
  before generating fresh rows.
- Added a [runnable stdio MCP journey](examples/mcp_stdio/README.md) using both
  installed servers, review-bound generation, and a disallowed Trino request
  rejected before network access.
- Added deterministic SQL `INSERT` export with quoted identifiers, escaped
  literals, manifest evidence, and a
  [runnable all-format example](examples/output_formats/README.md).
- Added [canonical dependency identities](docs/reference/dependency-compatibility.md)
  and a stable dependency fingerprint to generation-manifest reproducibility
  evidence.
- Added an offline `test-data-agent demo --output PATH` workflow using a
  bundled fictional fixture, deterministic seed, and atomic artifact publish,
  plus product-fit guidance comparing alternative test-data approaches.
- Added metadata-only effective generation and business-rule evidence to
  generation manifests, bound to exact spec and rule fingerprints.
- Added bounded numeric distribution scaling with fail-closed non-identity
  scaling for sensitive synthetic totals.
- Added domain-agnostic business-invariant coverage for component formulas,
  partitions, temporal windows, paired values, grouped totals, relationship
  coverage, and cross-table reconciliation across multiple domains.
- Added metadata-only temporal relationship candidates with normalized range
  overlap evidence and no provider-visible source date bounds.
- Added relationship-discovery coverage for compatible key types, normalized
  cardinality/null/distinctness evidence, and ambiguous low-confidence cases.
- Added metadata-only relationship candidate mining, provider ranking validation,
  and explicit human review records that cannot authorize generation.
- A runnable single-table CSV example now exercises explicit profiling, spec
  inference, deterministic generation, and independent validation.
- A runnable relational CSV example now verifies generated foreign keys,
  deterministic business rules, and multi-table validation.
- A runnable public Python API example now demonstrates metadata-only spec
  inference, seeded bundle generation, and independent validation.
- Provider-neutral relationship discovery candidate and proposal contracts
  restricted to bounded safe metadata and mandatory human review.
- Public relational-synthesis contract defining preserved graph, distribution,
  temporal, and business-rule semantics and explicit non-guarantees.
- Public conduct, support, governance, and code-ownership policies for the
  current single-maintainer project model.
- Generation manifests now record bounded reproducibility inputs and output
  SHA-256 evidence while distinguishing logical from cross-version byte-level
  reproducibility.
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

### Fixed

- Fixed ISO date columns being misclassified as phone numbers during CSV
  profiling.
- Validation reports now honor all `ValidationSettings` section toggles and
  `fail_fast`, and record the effective settings used.
- Container builds no longer default to version `0.8.1`, and publication now
  rejects image metadata that differs from the package version.
- `GenerationSettings.locale` now controls seeded Faker values, with clear
  rejection of unsupported locales.
- CSV and Trino profiles preserve low-cardinality frequency ranks with
  synthetic labels instead of exposing source category values.
- Incomplete staged generation and review bundles are removed when interactive
  cancellation interrupts writing or validation.
- Mid-write disk exhaustion removes partial staged folder, review, and
  single-entity output without publishing success metadata.
- Interrupted folder publication removes the renamed destination, while
  interrupted single-entity publication restores replaced files and removes
  partial new output.

### Security

- Advisor requests replace singleton categorical values with synthetic labels
  before a provider can receive the profile or baseline specification.
- Documented the public threat model, validation assurance levels, exact-row
  reuse detection limits, and the absence of statistical privacy guarantees.
- Trino SQL access is limited to validated read-only operations and dedicated
  bounded profiling; forbidden and non-allowlisted queries fail before a
  connection while allowlisted metadata and aggregate discovery remain available.
- Python, CLI, and generator MCP generation reject raw-looking sensitive
  categories, unsafe sensitive distributions, and privacy-policy opt-outs before
  creating artifacts or echoing rejected values.
- Masked Trino samples use opaque placeholders for rare free text and
  quasi-identifiers.
- MCP installations exclude the incompatible 2.x SDK until the transport
  migrates to its replacement API.
- JSON dataset inputs are bounded by row count, nested value count, nesting
  depth, and string value length before validation.

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

[Unreleased]: https://github.com/wa-pis/agent-paranoid-android/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/wa-pis/agent-paranoid-android/compare/v1.0.0rc6...v1.0.0
[1.0.0rc6]: https://github.com/wa-pis/agent-paranoid-android/compare/v1.0.0rc5...v1.0.0rc6
[1.0.0rc5]: https://github.com/wa-pis/agent-paranoid-android/compare/v1.0.0rc4...v1.0.0rc5
[1.0.0rc4]: https://github.com/wa-pis/agent-paranoid-android/compare/v1.0.0rc3...v1.0.0rc4
[1.0.0rc3]: https://github.com/wa-pis/agent-paranoid-android/compare/v1.0.0rc2...v1.0.0rc3
[1.0.0rc2]: https://github.com/wa-pis/agent-paranoid-android/compare/v1.0.0rc1...v1.0.0rc2
[1.0.0rc1]: https://github.com/wa-pis/agent-paranoid-android/compare/v0.12.0...v1.0.0rc1
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
