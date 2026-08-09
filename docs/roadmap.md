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
- Default generator and default aggregate-only Trino MCP responses that return
  summaries and artifact paths, not dataset rows.

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

The active release candidate is `1.0.0rc6`. `1.0.0rc2` completed public
acceptance; `1.0.0rc3` added the contract-preserving application-boundary
refactor, and
`1.0.0rc4` completed public-index acceptance. `1.0.0rc5` closed the remaining
invocation, transport, advisor, and exact-publication acceptance findings and
is now historical; RC6 is the active candidate for stable promotion.
`1.0.0rc1` completed package and GitHub publication but was superseded after
GHCR rejected its PEP 440 version as a SemVer tag. Assign work to the release
where it forms
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
7. [x] Complete the [application boundaries refactor
   OpenSpec](https://github.com/wa-pis/agent-paranoid-android/blob/main/openspec/changes/archive/2026-08-01-application-boundaries-refactor/proposal.md)
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
   - [x] Split CLI composition and Trino policy, query, client, profiling, and
     masking responsibilities.
     - [x] Extract validated Trino connection and resource-budget configuration.
     - [x] Extract pure read-only SQL and allowlist policy.
     - [x] Extract non-executing Trino metadata and profiling query builders.
     - [x] Extract the bounded Trino client and resource-cleanup boundary.
     - [x] Extract allowlisted, aggregate-only Trino profiling orchestration.
     - [x] Extract Trino masking and source-free category summaries.
     - [x] Extract CLI installation diagnostics and capability smoke
       orchestration.
     - [x] Centralize CLI optional-extra discovery and installation errors.
     - [x] Extract review-first `agent-*` CLI command handlers.
     - [x] Extract dataset and utility CLI command handlers.
     - [x] Extract CLI application composition and command dispatch.
   - [x] Add architecture and direct-service adversarial tests while preserving
     every public Python, CLI, MCP, artifact, error, and safety contract.
     - [x] Add static dependency, policy-owner, transport, and cycle gates.
     - [x] Complete cross-boundary direct-service adversarial coverage.
       - [x] Reject symlinked workspace targets before plan staging.
       - [x] Reject unsafe specs before injected approval generation.
       - [x] Reject unsafe SQL before injected Trino access.
       - [x] Reject unsafe provider payloads before review persistence.
     - [x] Document internal ownership migrations and retained compatibility
       entry points.
   - [x] Run the full typing, lint, compile, test, package, documentation, and
     security gates, then archive the completed OpenSpec change.
     - [x] Record full local and exact-commit GitHub gate evidence.
     - [x] Confirm no canonical deltas are required and archive the completed
       change.
8. [x] Complete the [1.0.0rc4 privacy and invocation hardening
   OpenSpec](https://github.com/wa-pis/agent-paranoid-android/blob/main/openspec/changes/1-0-0-rc4-privacy-invocation-hardening/proposal.md),
   publish `1.0.0rc4` from the verified merge commit, and repeat
   public-artifact acceptance against that candidate.
   - [x] Remove `sample_rows_masked` from the Trino MCP server, masking service,
     query builder, and public compatibility exports. Do not retain a row
     diagnostic in RC4; require a separate OpenSpec for any future
     row-returning capability.
   - [x] Test the complete production-registered default Trino toolset through
     direct-service and transport boundaries, including serialized success,
     error, and audit payloads with typed source-literal sentinels.
   - [x] Add and enforce a shared invocation-level Trino work budget across
     nested profiling and query operations. Define separate raw transport and
     canonical application-input limits, fresh per-invocation lifecycle,
     concurrency isolation, non-resettable counters, and incremental response
     accumulation limits.
   - [x] Correct prerelease installation instructions to use the exact
     `agent-paranoid-android==1.0.0rc4` command and execute the README
     quickstart from a clean environment using that public artifact.
   - [x] Clarify that default aggregate-only MCP is source-literal-free while
     `run_safe_select` is a separate explicit opt-in and is not source-free.
     Remove stale `sample_rows_masked` documentation.
   - [x] Record the disposition of crash-durability/fsync work; it is not an
     ordinary stable-release blocker unless the product contract promises it.
9. [ ] Apply only release-blocking fixes found during RC4 acceptance, repeat
   the exact release gates, and publish `1.0.0` from the verified release
   commit.

The preferred release path is to consolidate the already completed `0.13.0`
through `0.15.0` scopes into the 1.0 release candidate after the OpenSpec and
security gates.
Do not create retroactive intermediate tags unless maintainers explicitly need
those public milestones. Version changes, release commits, tags, and publication
remain separate release-stage work.

### Product Validation Before Stable 1.0

**Goal:** verify that the frozen workflow solves a real development or analytics
problem before adding more platform surface.

Scope:

- [ ] Run the [Product Validation Pilot](getting-started/product-validation-pilot.md)
  with at least two people who own a development, integration-testing, analytics,
  or budgeting task.
- [ ] Use at least one relational input with declared or discoverable
  relationships and one business invariant that must reconcile.
- [ ] Record the input type, evidence coverage, participant task, time to first
  useful bundle, specification edits, validation failures, and unresolved
  assumptions.
- [ ] Confirm that participants can understand the review-first flow without
  treating AI hypotheses as facts or the output as a privacy certificate.
- [ ] Confirm that at least one generated bundle is used successfully in the
  stated target workflow, or document the concrete blocker and decision to
  change scope.

Exit criteria:

- The team can name the first target persona and repeatable use case.
- The normal path from schema/profile to validated output is understandable.
- The remaining work is prioritized by observed user friction or task value,
  not by speculative feature completeness.

### PostgreSQL Source Adapter Gate

For teams whose source system is PostgreSQL, stable `1.0` also requires one
documented direct database workflow. Trino remains an optional integration and
must not be a prerequisite for PostgreSQL users.

The implementation contract is the [PostgreSQL and multi-source
OpenSpec](https://github.com/wa-pis/agent-paranoid-android/blob/main/openspec/changes/1-0-0-postgres-multi-source/proposal.md).

The minimum PostgreSQL scope is:

- [ ] Add a separate optional `postgres` installation profile.
- [ ] Add a read-only connection with schema/table allowlists and bounded
  statements, bytes, columns, and wall-clock time.
- [ ] Extract tables, types, nullability, primary keys, foreign keys, and checks.
- [ ] Compute aggregate profiles for null ratios, cardinality, ranges, and safe
  distributions without returning source rows.
- [ ] Reuse the existing review-first and deterministic validation boundaries
  for relationship discovery and reconciliation checks.
- [ ] Add a synthetic PostgreSQL fixture and clean-environment acceptance path
  from profile to generated and validated output.
- [ ] Correct all user-facing documentation so DDL, ORM models, and direct
  PostgreSQL access are not presented as already-supported CLI inputs.

Do not expand this gate into arbitrary SQL execution, every relational database,
automatic ORM introspection, or mandatory AI/MCP support. AI may help rank
ambiguous relationships, but it is not part of the required generation chain.

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

### 1.0.0rc4: Privacy And Invocation Hardening

**Goal:** close the post-RC3 security and release-engineering findings before
the first stable compatibility baseline. RC4 is a required gate, not an
optional milestone after `1.0.0`.

Scope:

- [x] Complete and review the [RC4 privacy and invocation hardening
  OpenSpec](https://github.com/wa-pis/agent-paranoid-android/blob/main/openspec/changes/1-0-0-rc4-privacy-invocation-hardening/proposal.md).
- [x] Remove `sample_rows_masked` from the Trino MCP server, masking service,
  query builder, and public compatibility exports. Do not retain a row
  diagnostic in RC4; require a separate OpenSpec for any future
  row-returning capability.
- [x] Add adversarial regression tests over the complete production-registered
  default toolset through direct-service and transport boundaries. Check
  serialized success, error, and audit payloads with typed source-literal
  sentinels, including values that heuristic PII masking would not flag.
- [x] Introduce a common `QueryWorkBudget` for one MCP invocation with
  separate raw transport and canonical application-input limits, fresh
  per-invocation lifecycle, concurrency isolation, non-resettable counters,
  shared nested consumption, and incremental response-byte accounting.
- [x] Change prerelease installation guidance to the exact
  `agent-paranoid-android==1.0.0rc4` command, keep extras consistent, and run
  the literal README quickstart in a clean environment against that public
  wheel.
- [x] Reconfirm the dependency boundary: Trino is an optional integration.
  The base wheel and CSV/JSON workflow must install and run without `trino`,
  `sqlglot`, or the MCP SDK; Trino capability checks belong to the separate
  `trino` extra and must not become a base-install release gate.
- [x] Update MCP documentation and compatibility fixtures to distinguish the
  source-literal-free aggregate-only default from the separate opt-in
  `run_safe_select` capability. Remove stale `sample_rows_masked` references
  and do not describe row-returning output as source-free, PII-free,
  anonymous, or privacy-safe merely because heuristic masking was applied.
- [x] Document the durability boundary between atomic visibility, process
  interruption recovery, and crash/power-loss durability. Decide explicitly
  whether fsync is a post-1.0 improvement or a release requirement.
- [x] Run the direct API adversarial suite, Trino integration checks, typing,
  lint, compile, full tests, wheel/container checks, documentation build,
  security scans, and public package acceptance against the exact RC4 commit.

Exit criteria:

- No unresolved P0 or release-blocking P1 findings remain. Every lower-priority
  finding has an owner, disposition, and revisit trigger.
- Public `1.0.0rc4` artifacts install in a clean environment, the README
  quickstart succeeds, optional extras are verified, and the exact artifact
  version is reported.
- The base installation remains usable without Trino, SQL parsing, or MCP;
  the separate `trino` extra is installed and checked only for Trino workflows.
- MCP golden contracts, OpenSpec requirements, documentation, changelog,
  package metadata, attestations, and container tags describe the same RC4
  behavior.
- Stable publication is allowed only from the accepted RC5 production source
  tree plus a reviewed version/changelog/release-metadata-only diff. No
  executable production or dependency changes may be added between RC5
  acceptance and `1.0.0`; all final release gates must run again. The exact
  allowlist and new-candidate fallback are defined in the
  [release process](release.md#rc6-to-stable-promotion).

### Historical 1.0.0rc5: Public Release And Invocation Hardening

**Goal:** finish public RC acceptance and close the remaining response-size,
invocation-duration, and MCP documentation ambiguities before stable
promotion. RC5 is required if any RC4 public-artifact gate is incomplete or if
the new cumulative limits are not yet benchmark-backed.

Scope:

RC5 is historical and superseded for stable promotion. Do not add new RC5
work; the active final-candidate checklist is RC6 below.

- [x] Complete the [RC5 public release and invocation hardening
  OpenSpec](https://github.com/wa-pis/agent-paranoid-android/blob/main/openspec/changes/1-0-0-rc5-public-release-invocation-hardening/proposal.md).
- [x] Publish and verify the exact `1.0.0rc4` wheel and sdist on PyPI, a
  GitHub prerelease with checksums/SBOM/attestations, and the corresponding
  immutable release identity. Evidence: [RC4 published release
  evidence](release-evidence-1.0.0rc4.md).
- [x] Install the public RC4 wheel in clean environments and run the literal
  README `doctor` and `demo` commands for base, `[trino]`, `[mcp]`, and
  `[mcp,trino]`. Evidence: the [public profile smoke
  run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/30736848757).
- [x] Verify `--version`, `demo`, and `doctor` for every published wheel
  profile, recording package version, artifact hash, Python version, and
  extra profile in the [release evidence](release-evidence-1.0.0rc4.md).
- [x] Extend the public wheel matrix to `[parquet]`, `[openai]`, and `[all]`;
  verify the CLI, generator-MCP, and Trino-MCP container targets in their
  separate container matrix. Evidence: [public verification run
  #8](https://github.com/wa-pis/agent-paranoid-android/actions/runs/30737685272).
- [x] Re-run public documentation, package attestation, and upgrade-from
  `0.12.0` checks from published artifacts only. Evidence: [public
  verification run #9](https://github.com/wa-pis/agent-paranoid-android/actions/runs/30738435369).
- [x] Publish and verify the exact `1.0.0rc5` wheel, sdist, GitHub prerelease,
  checksums, SBOM, provenance, attestations, and clean-install matrix from
  the immutable RC5 tag. Evidence: [RC5 published release
  evidence](release-evidence-1.0.0rc5.md).
- [x] Split database-result and transport-response budgets. Enforce
  `database_result_bytes` incrementally while reading the cursor and
  `transport_response_bytes` after final MCP JSON serialization, including
  envelopes, keys, escaping, dictionaries, nested metadata, and other
  transport overhead. On overflow, return a small fixed error response that
  is reserved and proven to fit the transport budget.
- [x] Add cumulative invocation limits: `max_profiled_columns`,
  `max_invocation_seconds`, and, if measurable, cumulative estimated scan
  bytes. Start with `100` columns, `150` statements, and `120` seconds unless
  operational benchmarks justify different defaults; do not treat per-query
  Trino session limits as a substitute.
- [x] Document every application-level limit in the configuration reference,
  including defaults, environment names, failure behavior, and whether the
  limit is per query or per invocation.
- [x] Normalize all MCP documentation to distinguish default generator and
  default aggregate-only Trino profiling responses from explicit opt-in
  row-returning capabilities. Remove server-wide claims that imply every MCP
  response is source-free.
- [x] Add the [RC5 agent throughput and advisor budget
  OpenSpec](https://github.com/wa-pis/agent-paranoid-android/blob/main/openspec/changes/1-0-0-rc5-public-release-invocation-hardening/proposal.md):
  make local profile caching `auto` by default with an explicit `--no-cache`
  escape hatch, avoid the current two-pass CSV-folder profile where practical,
  and enforce a local profile deadline plus bounded relationship/rule samples.
- [x] Add bounded advisor presets and evidence: model, reasoning effort,
  prompt/input budget, output budget, timeout, and retry count must be typed,
  configurable, and visible in non-sensitive run metadata. Select
  fast/normal/quality defaults only after measuring proposal validity, latency,
  tokens, and cost on representative synthetic profiles.
- [x] Run the RC5 acceptance advisor benchmark with at least 20 runs per
  preset and at least five synthetic profile shapes, including p50/p95,
  timeout/error, retry, token, validity, safety, and cost measurements.
  Evidence: the [advisor benchmark](https://github.com/wa-pis/agent-paranoid-android/blob/main/openspec/changes/1-0-0-rc5-public-release-invocation-hardening/advisor-benchmark-evidence.md)
  records 60/60 valid and safety-preserving responses, zero errors/timeouts,
  and `$2.320800` total cost across all three presets.
- [x] Complete an independent security review of RC5 sanitization, request-ID
  lifecycle, and transport budget enforcement before RC5 acceptance. Evidence:
  [RC5 security review](https://github.com/wa-pis/agent-paranoid-android/blob/main/openspec/changes/1-0-0-rc5-public-release-invocation-hardening/security-review-evidence.md).
- [x] Ensure advisor byte/token accounting covers the complete provider request,
  not only the serialized `AdvisorRequest`; compact or partition oversized
  metadata rather than sending an unbounded multi-megabyte prompt.
- [x] Wire the provider-neutral relationship-candidate ranking contract to the
  optional advisor integration as a separate, review-gated operation. The model
  may rank deterministic candidates and explain bounded evidence, but may not
  invent fields, receive source rows, or modify `DatasetSpec` directly.
- [x] Repeat direct-service, transport, integration, package, documentation,
  security, and public-artifact gates against the exact RC5 commit. Evidence:
  [Release #17](https://github.com/wa-pis/agent-paranoid-android/actions/runs/31274057391)
  and [Verify Published Release #10](https://github.com/wa-pis/agent-paranoid-android/actions/runs/31274217410).

Exit criteria:

- PyPI and GitHub public artifacts are present, mutually identified by commit
  and version, and install successfully in clean environments.
- Final MCP JSON responses and bounded error responses cannot exceed the
  configured transport budget; database and transport budgets are reported
  separately in tests and diagnostics.
- A wide-table profile fails closed on cumulative columns, statements, or
  invocation time before unbounded work continues.
- Repeated local planning reuses a metadata-only profile cache, forced refresh
  works, and a profile fails closed on its deadline or sample budget.
- Advisor fast/normal/quality behavior is benchmark-backed, the full provider
  request and response are bounded, and latency/retry/token metadata contains
  no source values or secrets.
- Relationship ranking is candidate-only, deterministic-candidate-bound, and
  still requires explicit human review before any spec or generation change.
- Configuration reference, OpenSpec, MCP examples, README, and release
  evidence use the same default-vs-opt-in terminology.
- Stable promotion is allowed only from the accepted RC5 source tree plus a
  reviewed version/changelog/release-metadata-only diff.

### 1.0.0rc6: Final Release Candidate

**Goal:** make RC6 the single reviewed source tree for stable promotion after
closing the remaining privacy-boundary, provider-trust, transport, filesystem,
supply-chain, and public-review evidence gaps. RC6 remains active because no
`v1.0.0rc6` tag has been accepted yet; the current-tree security review adds
requirements to this candidate rather than creating an unnecessary RC7.

Scope:

- [x] Implement field-scoped, deterministic rare-category placeholders that
  avoid normal-category and placeholder collisions and preserve sanitizer
  provenance across reordered baselines.
- [x] Replace source-derived CSV-folder text categories with collision-safe
  ranked labels before caching or generation while preserving category counts
  and inferred conditional rules.
- [x] Sanitize source-derived advisor constraint predicates with the same
  field-scoped category map and reject unrepresented string literals.
- [x] Return typed per-call OpenAI completion metadata and attach the same
  bounded metadata to preflight/provider failures; keep the mutable last-call
  view legacy-only.
- [ ] Convert every ordinary SDK construction exception to the fixed local
  error, detach all provider exception chains, and keep dynamic Python exception
  class names out of public provider-call messages.
- [x] Add `trusted-local` and `shared-hardened` Trino deployment profiles;
  require a finite cumulative scan ceiling for `shared-hardened` and expose the
  effective policy in `doctor`.
- [x] Add focused tests for placeholder collisions/determinism, concurrent
  provider calls and failures, and fail-closed Trino profile configuration.
- [x] Make every categorical value in an external advisor request synthetic or
  non-reversible; heuristic PII detection is not an egress guarantee.
- [ ] Suppress exact sensitive numeric Trino extrema and percentiles through
  MCP, legacy conversion, and planning artifacts.
- [ ] Validate provider-added DatasetSpec constraints and run privacy/type
  checks after constraint solving, before output publication.
- [x] Make formula and validation diagnostics fixed-reason and source-free.
- [x] Apply bounded raw-frame, invocation, and final-response budgets to the
  generator MCP and enforce JSON structure limits before materialization.
- [x] Harden public artifact names and neutralize spreadsheet formula markers
  in CSV output.
- [x] Bound active MCP requests and shared Trino concurrency, release all
  request state on cancellation/disconnect/timeout/teardown, and return fixed
  bounded capacity errors.
- [x] Redact Trino driver failures and define the allowed catalog/schema
  enumeration metadata surface before it reaches MCP clients.
- [x] Define and enforce a separate privacy contract for opt-in
  `run_safe_select`, including names, addresses, and heuristic false-negative
  regressions.
- [x] Bound semantic-provider execution and cancellation, require deterministic
  replay or a seed-bound output fingerprint, restrict identity output to a
  synthetic namespace, and run post-generation privacy/type checks.
- [x] Harden filesystem publication and overwrite paths against symlink and
  TOCTOU races with descriptor-relative no-follow and inode revalidation.
- [x] Define completion/read-validation semantics and explicit approval for
  sibling-artifact replacement.
- [x] Escape and bound untrusted metadata, paths, and errors in CLI and logs.
- [ ] Move CI classification to trusted code, bind release publication to a
  signed tag and reviewed commit digest, and enforce a machine-readable RC
  acceptance manifest plus hash-pinned public profile installs.
- [x] Record deployed branch/tag rulesets, required checks, and PyPI Trusted
  Publisher approvals as external RC6 acceptance evidence.
- [ ] Record a publicly verifiable security review with reviewer identity or
  stable pseudonym, reviewed commit, date, scope, findings/disposition, and a
  signature or approval URL.
- [ ] Retag the fixed RC6 source tree and publish wheel, sdist, checksums, SBOM,
  provenance, attestations, signatures, documentation, and all supported wheel
  and container profiles.
- [ ] Install the public RC6 artifacts in clean environments and run the
  literal README `--version`, `demo`, and `doctor` checks, including base,
  `parquet`, `mcp`, `trino`, `mcp,trino`, `openai`, `all`, and all three
  published containers, plus the `0.12.0` upgrade check.
- [ ] Run the complete release, security, documentation, typing, lint, and
  test gates against the immutable RC6 commit before stable promotion.

Exit criteria:

- No unresolved release-blocking finding remains at any severity.
- RC6 public artifacts and documentation identify the same immutable commit.
- Stable promotion is allowed only from the accepted RC6 source tree plus a
  reviewed metadata-only version bump.

### 1.0.0: Stable Release

**Goal:** promote the verified RC6 baseline to the first stable compatibility
baseline.

Scope:

- [x] Complete and archive the [application boundaries refactor
  OpenSpec](https://github.com/wa-pis/agent-paranoid-android/blob/main/openspec/changes/archive/2026-08-01-application-boundaries-refactor/proposal.md)
  without changing public Python, CLI, MCP, artifact, error, or safety
  contracts.
- [ ] Promote the accepted `1.0.0rc6` commit without unrelated feature work.
- [ ] Apply only fixes proven necessary by RC6 acceptance and repeat the
  affected release gates.
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

- [ ] Resolve the four accepted Low [Known Issues](known-issues.md) in the
  first post-1.0 security-hardening release, or earlier if a documented revisit
  trigger occurs.
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
