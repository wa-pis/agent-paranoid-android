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

The package release candidate is `1.0.0rc2`. `1.0.0rc1` completed package and
GitHub publication but was superseded after GHCR rejected its PEP 440 version
as a SemVer tag. Assign work to the release where it forms
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
- [x] Run isolated wheel and container workflows across supported Python
  versions and architectures.
  - [x] Build and install the base wheel on Python 3.11 through 3.14 while
    retaining the full optional-profile smoke on Python 3.14.
  - [x] Validate hardened runtime health for every target on AMD64 and ARM64.
- [x] Complete a dependency, license, security, and container-image review with
  no unresolved release-blocking findings.
  - [x] Block container publication on fixable High or Critical vulnerabilities
    found in each native CLI and MCP target.
  - [x] Fail closed on unknown or unapproved licenses across locked application,
    optional, development, and documentation dependencies.
  - [x] Record scanner evidence and explicit owner/revisit dispositions for all
    remaining Scorecard maturity and single-maintainer governance findings.

Exit criteria:

- Installation, quickstart, agent approval, generation, validation, and audit
  verification pass from published-style wheel and container artifacts.
- Resource limits fail closed and leave no successful-looking partial output.
- Documentation covers the normal workflow and the most likely recovery paths.

### Remaining Execution Plan To 1.0

The implementation scopes for `0.13.0`, `0.14.0`, and `0.15.0` are consolidated
into `1.0.0rc1`. Finish the release stage in this order:

1. [x] Merge each completed active OpenSpec delta into its canonical capability
   and archive its proposal and task evidence.
2. [x] Confirm that no active OpenSpec change outside the 1.0 baseline requires
   deferral.
3. [x] Reconfirm the active OpenSpec set after the planned public-readiness
   changes below; every remaining change must be implemented, assigned, or
   explicitly deferred before the RC is published.
4. [x] Run a fresh full security audit, resolve every Critical and High finding,
   and record owners and dispositions for accepted Medium or lower risks.
5. [x] Review README, documentation, migration guidance, examples, package
   metadata, support policy, SBOM, provenance, signatures, and release notes as
   one public-readiness gate.
6. [x] Complete public `1.0.0rc2` acceptance.
   - [x] Publish the candidate and run installation, `doctor`, demo generation,
     validation, documentation, package-attestation, and container-signature
     checks only against its public artifacts.
   - [x] Run agent approval and audit verification from the exact public
     package or container artifacts.
7. [ ] Complete the [application boundaries refactor
   OpenSpec](https://github.com/wa-pis/agent-paranoid-android/blob/main/openspec/changes/application-boundaries-refactor/proposal.md)
   as a contract-preserving stable-1.0 gate.
   - [x] Inventory and freeze the existing public and safety boundaries.
   - [x] Extract typed workspace persistence and staged agent lifecycle
     services.
     - [x] Publish plans and completion markers through a typed, atomic
       filesystem workspace store.
     - [x] Extract neutral agent contracts and the planning lifecycle service.
     - [x] Extract the metadata-only review lifecycle service.
     - [x] Extract the approval lifecycle service.
     - [x] Extract the recovery lifecycle service.
     - [x] Extract the metadata-only advising lifecycle service.
     - [x] Extract the status lifecycle service.
   - [ ] Split CLI composition and Trino policy, query, client, profiling, and
     masking responsibilities.
     - [x] Extract validated Trino connection and resource-budget configuration.
     - [x] Extract pure read-only SQL and allowlist policy.
     - [x] Extract CLI installation diagnostics and capability smoke
       orchestration.
     - [x] Centralize CLI optional-extra discovery and installation errors.
     - [x] Extract review-first `agent-*` CLI command handlers.
     - [x] Extract dataset and utility CLI command handlers.
     - [x] Extract CLI application composition and command dispatch.
   - [ ] Add architecture and direct-service adversarial tests while preserving
     every public Python, CLI, MCP, artifact, error, and safety contract.
   - [ ] Run the full typing, lint, compile, test, package, documentation, and
     security gates, then archive the completed OpenSpec change.
8. [ ] Publish a new release candidate from the verified refactor commit and
   repeat public-artifact acceptance against that candidate.
9. [ ] Apply only release-blocking candidate fixes, repeat the exact release
   gates, and publish `1.0.0` from the verified release commit.

The preferred release path is to consolidate the already completed `0.13.0`
through `0.15.0` scopes into the 1.0 release candidate after the OpenSpec and
security gates.
Do not create retroactive intermediate tags unless maintainers explicitly need
those public milestones. Version changes, release commits, tags, and publication
remain separate release-stage work.

### 1.0.0rc1: Release Candidate

**Goal:** rehearse the final release from frozen contracts without adding
features.

Scope:

- [x] Complete the [1.0.0rc1 security-boundary hardening
  OpenSpec](https://github.com/wa-pis/agent-paranoid-android/blob/main/openspec/changes/archive/2026-08-01-1-0-0-rc1-security-hardening/proposal.md).
  P0 findings are release blockers; P1 findings require closure or explicit
  independent-reviewer acceptance before the stable release; P2 findings need
  a documented disposition.
- [x] Enforce the spec-level privacy gate across Python, CLI, agent, and MCP
  generation paths, and enforce validated read-only SQL across direct Trino
  access paths.
- [x] Add direct API adversarial tests to the release gate; passing the current
  CLI/MCP workflow tests alone is not sufficient evidence for the RC.
- [x] Record reproducibility inputs, container/package version consistency, and
  security scanner evidence against the exact RC commit and published artifacts.
- [x] Formalize the reproducibility contract: distinguish same-environment,
  same-version, and cross-version guarantees; record package/Python,
  dependency-lock, locale, spec, rules, provider, and generator fingerprints
  in the manifest.
- [x] Define the dependency support contract with tested minimum and latest
  compatible versions, reasonable upper bounds, and explicit behavior changes
  that require a package release. Use the [dependency compatibility
  OpenSpec](https://github.com/wa-pis/agent-paranoid-android/blob/main/openspec/changes/archive/2026-08-01-dependency-compatibility-contract/proposal.md)
  as the implementation contract.
  - [x] Test minimum-supported and latest-compatible dependency profiles for
    Faker, Pydantic, PyYAML, PyArrow, sqlglot, and the Trino client where used.
  - [x] Record dependency identities, generator version, locale, seed, spec
    digest, and rules digest in reproducibility evidence.
  - [x] Add upper major bounds only after compatibility evidence justifies
    them; do not promise cross-version byte identity without tests.
- [x] Validate the core product workflow: bounded profiling → deterministic
  relationship candidates → AI-assisted proposals → human review →
  deterministic validation → synthetic generation.
- [x] Define and implement the Evidence-Bounded Synthesis Contract: separate
  `SourceBundle`, `EvidenceProfile`, `SemanticHypothesis`, and
  `ReviewedDatasetSpec`; preserve provenance, sampling coverage, confidence,
  assumptions, and unknowns instead of presenting inferred domain rules as
  facts.
- [x] Ensure AI can rank and explain evidence-backed hypotheses but cannot
  upgrade confidence, approve a rule, or authorize generation; deterministic
  validation and human review remain the authority boundary.
- [x] Preserve approved FK graphs, distribution/order-of-magnitude shape,
  temporal dependencies, and executable business invariants independently of
  domain or table names.
- [x] Demonstrate at least one domain-agnostic summary-table scenario where
  synthetic grouped totals, components, partitions, and cross-table formulas
  reconcile without copying source totals or rows. Financial/accounting data
  may be one fixture, not the product boundary.
- [x] Close or explicitly defer every active OpenSpec change.
- [x] Run the full security audit and resolve all Critical and High findings.
- [x] Separate structural validation from privacy assurance in user-facing
  output; document heuristic false negatives, quasi-identifiers, rare/free
  text, and explicit assurance levels without implying re-identification
  certification.
- [x] Publish a concise threat model covering source rows, raw PII, secrets,
  prompt injection, provider boundaries, generated artifacts, and resource
  exhaustion.
- [x] Complete the public product-clarity gate: functional subtitle and GitHub
  About/topics, an input → command → output README example, preserved versus
  not-preserved properties, an alternatives comparison, and a clear statement
  that CLI/library is primary while MCP and providers are integrations.
  - [x] Add an installed-wheel `test-data-agent demo --output PATH` workflow
    using only a bundled synthetic fixture; it must be deterministic, offline,
    optional-integration-free, and safe on existing or unwritable paths.
  - [x] Make the demo the first README workflow and show representative
    synthetic output plus preserved schema, nullability, shape, relationships,
    temporal, and executable business-rule properties.
  - [x] State explicit non-guarantees for raw-value copying, real PII,
    statistical anonymity, re-identification, and cross-version byte identity.
  - [x] Use the [installed demo and product clarity
    OpenSpec](https://github.com/wa-pis/agent-paranoid-android/blob/main/openspec/changes/archive/2026-08-01-installed-demo-and-product-clarity/proposal.md)
    as the implementation contract.
- [x] Publish runnable, CI-verified usage journeys built only from synthetic
  fixtures. Each journey must show its input, command or API call, generated
  artifacts, validation result, and the privacy boundary being exercised:
  - [x] Single-table CSV: profile → infer spec → generate → validate → export.
  - [x] Relational CSV folder: discover candidate relationships, review rules,
    generate multiple tables, and verify FK/business-rule reconciliation.
  - [x] Local Trino: start a disposable synthetic catalog, exercise bounded
    metadata/profiling tools, then generate without exporting source rows.
  - [x] MCP: configure and call generator and Trino servers against the same
    synthetic fixtures, including one rejected unsafe request.
  - [x] Python library: reproduce the CLI golden path with the public API and
    an explicit seed.
  - [x] Output formats: inspect CSV, JSON, SQL, and optional Parquet artifacts
    plus their manifest and validation report.
  - [x] Add one-command launchers and CI smoke tests that run the examples from
    an installed wheel or release-style container, not the source checkout.
- [x] Verify README, documentation site, migration guidance, examples, package
  metadata, SBOM, provenance, signatures, and public support policy.
  - [x] Keep `CHANGELOG.md` user-facing; move detailed OpenSpec, audit, and
    release-engineering evidence to canonical linked documents without deleting
    security history. Track this in the [release documentation hygiene
    OpenSpec](https://github.com/wa-pis/agent-paranoid-android/blob/main/openspec/changes/archive/2026-08-01-release-documentation-hygiene/proposal.md).
- [x] Publish and install the release candidate through the real GitHub,
  PyPI, documentation, and GHCR paths.
- [x] Finish end-to-end smoke tests only against the published candidate
  artifacts.
  - [x] Verify public installation, `doctor`, demo generation and validation,
    documentation, package attestations, and container signatures.
  - [x] Exercise agent approval and audit verification from the exact public
    package or container artifacts.

Exit criteria:

- Required CI, release, publication, installation, and smoke checks pass.
- The RC security-boundary hardening OpenSpec has no unresolved P0 task, and
  every remaining P1 or lower item has an owner, disposition, revisit date,
  and trigger.
- Any remaining Medium or lower security risk is documented with an owner and
  disposition.
- Only release-blocking fixes may enter after the candidate.

### 1.0.0: Stable Release

**Goal:** complete the contract-preserving application-boundary refactor, prove
it through a new candidate, and publish the first stable compatibility baseline.

Scope:

- [ ] Complete and archive the [application boundaries refactor
  OpenSpec](https://github.com/wa-pis/agent-paranoid-android/blob/main/openspec/changes/application-boundaries-refactor/proposal.md)
  without changing public Python, CLI, MCP, artifact, error, or safety
  contracts.
- [ ] Publish and smoke-test a release candidate containing the completed
  refactor before promoting the exact verified code to stable.
- [ ] Apply only fixes proven necessary by release-candidate testing outside
  the bounded refactor scope.
- [ ] Re-run every release candidate gate on the exact release commit.
- [ ] Publish signed and attested wheel, source distribution, documentation,
  and separate CLI, generator MCP, and Trino MCP container images.
- [ ] Verify PyPI and GitHub Release digests, public installation, `doctor`,
  quickstart, and container signatures after publication.
- [ ] Start the post-1.0 compatibility and deprecation policy from the published
  contracts.

### Post-1.0: Follow-up Architecture And Community

After the stable baseline, continue the remaining maintenance and community
work without reopening the completed 1.0 application-boundary gate:

- [ ] Define a typed error taxonomy and expand strict mypy coverage to the full
  production package, using narrow overrides only for external integrations.
- [ ] Add a public maintainership/governance model, support expectations,
  release cadence, design-decision log, issue labels, and `good first issue`
  guidance.
- [ ] Publish a small benchmark dataset, demo recording, and a technical note
  explaining how source-row copying is prevented and tested.

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
