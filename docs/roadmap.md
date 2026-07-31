# Roadmap

The roadmap is ordered by safety and integration value, not by a fixed delivery
date.

## Implemented For 0.8.1

- AI prompts and integration documentation aligned with the implemented
  `DatasetSpec`, output-format, approval, and artifact-only MCP contracts.
- Independent installation smoke tests for the base package and the `parquet`,
  `mcp`, and `trino` extras.
- Dependency-count and wheel-size budgets that keep optional integrations out
  of the base installation.
- `all` documented as a development, demo, and container convenience.
- Strict type checking for the CLI and agent-facing interfaces, with typed
  plan and generation summaries.

## Implemented For 0.9.0

- Read-only workspace status for the review-first agent flow, including
  versioned JSON output for automation and AI clients.
- Narrow validated `agent-plan` input detection for CSV files, CSV folders,
  and safe profiles, with DatasetSpec inputs routed to `generate`.
- Concise metadata-only review summaries with fields, sensitive
  classifications, relationships, confidence, assumptions, and safety
  warnings.
- Stable versioned JSON results for planning, status, and approval, with
  typed errors and documented exit codes for automation and AI clients.
- Typed review and approval records with plan identifiers, profile/spec
  fingerprints, exact-hash confirmation, and persisted approval receipts.
- Explicit recovery for interrupted approvals, including a completion
  checkpoint, bounded artifact revalidation, and idempotent repeated approval
  without regenerating rows.
- Provider-neutral advisor JSON export and apply commands, with bounded input,
  fingerprint validation, recoverable persistence, and no model SDK in the
  base package.
- Self-describing advisor exchanges with immutable trusted instructions,
  explicitly untrusted request metadata, and generated proposal JSON Schema.
- An in-process `ExchangeDatasetAdvisor` adapter for structured-output clients,
  with defensive request copying and proposal validation at the provider
  boundary.
- A runnable reference agent that plans from safe metadata, invokes the
  provider-neutral advisor boundary, stops for human review, requires the
  exact reviewed fingerprint, generates, validates, and reports artifact
  metadata without dataset rows.
- Detailed read-only `agent-review` reports with field nullability, sensitive
  and identifier flags, semantic and distribution kinds, privacy defaults,
  relationships, and exact approval fingerprints in human and JSON forms.

## Implemented For 0.10.0

- Add the first provider-specific advisor example behind an optional extra,
  without increasing the base installation or coupling the deterministic core
  to one model vendor.
- Keep the provider boundary metadata-only and structured: no source rows, raw
  PII, credentials, generated dataset contents, automatic approval, or direct
  generation access.
- Document the provider-neutral Python protocol, versioned JSON wire format,
  trust-channel mapping, safety requirements, and contract-test expectations
  for additional adapters.
- Ship a runnable end-to-end provider example that uses safe metadata,
  validates structured model output, pauses for exact-fingerprint human
  approval, and reports artifact paths rather than rows.

## Implemented For 0.11.0

- Present one guided agent workflow across the CLI and documentation:
  `agent-plan` -> `agent-review` -> `agent-advise` -> `agent-approve`, with
  clear next-action guidance and actionable recovery errors.
- Add golden contract fixtures and compatibility tests for versioned CLI JSON,
  MCP responses, `DatasetSpec` schemas, advisor exchanges, and generated
  artifact metadata.

## Implemented For 0.12.0

- Separate CLI argument parsing, application dispatch, and human/JSON
  presentation behind the existing `test-data-agent` entry point.
- Separate generator and Trino MCP transport registration from application
  services and safety policy. Both transport registrations are complete.
- Preserve command names, help, exit codes, JSON and MCP schemas, artifact
  formats, and safety behavior through golden contract tests.
- Deliver the refactor as small independently reviewable changes; do not add a
  CLI framework, provider SDK, or base runtime dependency.

## Implemented For 0.8.0

- Separate minimal CLI, generator MCP, and Trino MCP OCI images.
- A least-privilege Compose deployment with non-root workers, read-only root
  filesystems, bounded resources, mounted audit secrets, and isolated
  generator networking.
- Multi-platform GHCR publication with BuildKit SBOM and provenance,
  GitHub attestations, and keyless Cosign signatures.

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

## Reference AI Agent

Provide a practical AI-agent integration without coupling the deterministic
core to one model vendor:

- Define a provider-neutral advisor interface that accepts safe profile
  metadata and proposes structured `DatasetSpec` changes. The typed,
  fingerprint-bound core contract, recoverable workspace handoff, and external
  self-describing JSON exchange are implemented. The in-process exchange
  adapter, first optional OpenAI provider, and custom-provider guide are
  implemented; additional provider examples remain.
- Validate every model-produced proposal with Pydantic and the existing
  deterministic safety, generation, and validation layers.
- Keep model SDKs out of the base package; ship provider integrations as
  optional examples or separate extras only when they are useful.
- Ensure the model never needs raw production rows, raw PII, database
  credentials, unrestricted SQL, or generated dataset contents in chat.
- Treat table names, column names, descriptions, and safe distribution values
  as untrusted data and defend the agent flow against prompt injection.
- Include a complete reference flow that profiles, proposes a spec, requests
  human approval, generates, validates, and reports artifact paths and
  manifest facts. The runnable flow supports both a deterministic stand-in and
  the optional OpenAI provider while retaining the same approval boundary.

## Dependency Policy

- Keep the base runtime limited to dependencies required for deterministic
  generation and strict contracts. `Faker`, `Pydantic`, and `PyYAML` are the
  current direct baseline.
- Keep Parquet, MCP, and Trino support in separate extras. Do not require
  `PyArrow`, the MCP SDK, the Trino client, or SQL parsing for basic CSV/JSON
  generation.
- Keep model-provider SDKs in provider-specific extras. Installing or importing
  the base package must not require provider credentials or SDK modules.
- Do not replace maintained protocol or database libraries with custom
  implementations solely to reduce package count.
- Measure the base environment separately from development and `all` installs
  in CI, and document the installation cost of each optional capability.

## Version Plan To 1.0

The package is currently at `0.12.0`. Assign work to the release where it forms
a complete user workflow; do not bump the package version on every feature PR.
Version bumps, release changelog sections, and tags belong to separate release
pull requests.

### 0.13.0: Complete Negative Dataset Workflows

**Goal:** make controlled invalid datasets as deterministic and reviewable as
valid datasets.

Scope:

- [x] Support sum, count, and average cross-table reconciliation.
- [x] Distribute negative rows across supported field and row rules instead of
  repeatedly breaking only the first rule.
- [x] Generate coordinated foreign-key and aggregate-formula violations
  without corrupting unrelated rows.
- [x] Record expected and observed violations in bounded business-validation
  artifacts so users can distinguish intentional failures from generator bugs.
- [x] Add CLI and MCP examples that reproduce the same negative cases from the
  same spec, rule file, seed, mode, and invalid ratio.

Exit criteria:

- Every supported negative case is detected by deterministic validation.
- Negative artifacts remain explicitly separated and labelled as invalid test
  data.
- Existing valid, edge, and load-test behavior remains unchanged.
- Golden artifact contracts cover any report or manifest additions.

### 0.14.0: Freeze Public Contracts

**Goal:** define exactly what is stable for external users before the 1.0
compatibility promise starts.

Scope:

- [x] Publish a stability table for the supported Python imports, CLI commands,
  MCP tools, `DatasetSpec`, advisor exchange, and generated artifact files.
- [x] Freeze versioned JSON and MCP schemas with golden compatibility tests and
  explicit additive-versus-breaking change rules.
- [x] Inventory compatibility wrappers and command aliases. Mark retained
  surfaces as supported or deprecated with migration guidance; do not remove
  anything before its documented compatibility window expires.
- [x] Test that the current package reads reviewed specs and generated metadata
  fixtures from the previous feature release.
- [x] Document the support policy for Python versions, optional extras, and
  provider adapters.

Exit criteria:

- Every documented public surface has an owner, compatibility rule, and
  contract test.
- No unannounced schema, CLI help, exit-code, artifact-layout, or MCP tool
  changes remain.
- Experimental examples and provider integrations are clearly distinguished
  from the stable deterministic core.

### 0.15.0: Operational Readiness

**Goal:** prove the frozen product works reliably when installed and operated
outside the repository checkout.

Scope:

- [x] Add bounded performance and resource regression checks for representative
  multi-entity generation, validation, and profiling workloads.
- [x] Exercise cancellation, timeout, disk exhaustion, and interrupted-write
  paths and verify that partial bundles are never reported as successful.
  - [x] Remove staged folder and single-entity outputs on interactive process
    cancellation without publishing success metadata.
  - [x] Exercise mid-write disk exhaustion after a partial staged file exists.
  - [x] Exercise staged timeout cleanup across every generation output shape.
  - [x] Roll back folder and single-entity publication interrupted mid-commit.
- [x] Complete the `doctor` capability matrix for base, Parquet, MCP, Trino,
  and provider extras with actionable, secret-free recovery guidance.
  - [x] Run base generation and Parquet write/read smoke checks locally.
  - [x] Verify local generator MCP construction and tool registration.
  - [x] Add a local Trino parser and client-construction capability check.
  - [x] Add a local provider SDK and advisor-construction capability check.
- [ ] Run isolated wheel and container workflows across supported Python
  versions and architectures.
  - [x] Build and install the base wheel on Python 3.11 through 3.14 while
    retaining the full optional-profile smoke on Python 3.14.
  - [ ] Validate container targets on supported CPU architectures.
- [ ] Complete a dependency, license, security, and container-image review with
  no unresolved release-blocking findings.

Exit criteria:

- Installation, quickstart, agent approval, generation, validation, and audit
  verification pass from published-style wheel and container artifacts.
- Resource limits fail closed and leave no successful-looking partial output.
- Documentation covers the normal workflow and the most likely recovery paths.

### 1.0.0rc1: Release Candidate

**Goal:** rehearse the final release from frozen contracts without adding
features.

Scope:

- [ ] Close or explicitly defer every active OpenSpec change.
- [ ] Run the full security audit and resolve all Critical and High findings.
- [ ] Verify README, documentation site, migration guidance, examples, package
  metadata, SBOM, provenance, signatures, and public support policy.
- [ ] Publish and install the release candidate through the real GitHub,
  PyPI, documentation, and GHCR paths.
- [ ] Run end-to-end smoke tests only against the published candidate
  artifacts.

Exit criteria:

- Required CI, release, publication, installation, and smoke checks pass.
- Any remaining Medium or lower security risk is documented with an owner and
  disposition.
- Only release-blocking fixes may enter after the candidate.

### 1.0.0: Stable Release

**Goal:** publish the reviewed candidate as the first stable compatibility
baseline.

Scope:

- [ ] Apply only fixes proven necessary by release-candidate testing.
- [ ] Re-run every release candidate gate on the exact release commit.
- [ ] Publish signed and attested wheel, source distribution, documentation,
  and separate CLI, generator MCP, and Trino MCP container images.
- [ ] Verify PyPI and GitHub Release digests, public installation, `doctor`,
  quickstart, and container signatures after publication.
- [ ] Start the post-1.0 compatibility and deprecation policy from the published
  contracts.

### Required For Every Remaining Release

- `scripts/check_release.sh` and `mkdocs build --strict` pass.
- Supported Python versions, minimal installation, extras, wheel, and
  container checks pass where applicable.
- Fixtures and examples remain synthetic; generated manifests report
  `synthetic: true` and `source_rows_copied: false`.
- Trino operations remain read-only, allowlisted, bounded, and free of raw
  production rows.
- OpenSpec baseline, changelog, user documentation, and golden contracts match
  implemented behavior.
- The version tag is created only from the verified merge commit of the release
  pull request.

### Not Required For 1.0

- A hosted service, web UI, or desktop UI.
- Arbitrary SQL or unrestricted database access.
- Additional model-provider SDKs in the base package.
- Orchestrator templates beyond the existing Docker Compose deployment.
- Statistical aggregates whose semantics are not portable across supported
  engines, such as median and percentile reconciliation.

## Later

- Additional provider examples.
- Median and percentile cross-table reconciliation with explicit cross-engine
  semantics.
- Deployment templates for orchestrators beyond Docker Compose.
