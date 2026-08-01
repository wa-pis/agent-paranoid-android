# Tasks: 1-0-0-rc1-security-hardening

## P0 — release blockers before `1.0.0rc1`

- [x] Define and implement `assert_spec_safe()` for every `DatasetSpec`.
- [x] Enforce the spec safety gate in direct Python generation, bundle
  workflows, CLI, agent, and generator MCP paths.
- [x] Reject raw sensitive/unknown categorical values and unsafe sensitive
  distributions before row generation or artifact publication.
- [x] Add regression tests for manually constructed and malicious on-disk
  specs through Python, CLI, and MCP.
- [x] Make unrestricted Trino execution private and route all external calls
  through safe query validation or dedicated bounded methods.
- [x] Add mocked-cursor tests proving unsafe SQL is rejected before execution.
- [x] Verify that safe metadata and aggregate profilers still work through
  dedicated internal query builders.

## P1 — product semantics required before final `1.0.0` or explicitly accepted by an independent reviewer

- [x] Define the relational-synthesis contract: preserve FK graph shape,
  distribution/order-of-magnitude shape, temporal dependencies, and executable
  business invariants without copying source rows.
- [x] Define safe relationship-discovery input metadata and provider-neutral
  proposal contracts for AI-assisted FK, temporal, formula, and aggregate-rule
  discovery.
- [x] Combine deterministic candidate mining with AI ranking/proposals and a
  human review step; AI output must never directly approve generation.
- [x] Add relationship tests for compatible key types, cardinality, nulls,
  distinctness, temporal ranges, and ambiguous/low-confidence candidates.
  - [x] Cover key compatibility, cardinality/null/distinctness evidence, and
    unresolved ambiguous low-confidence candidates.
  - [x] Cover bounded temporal-range evidence and overlap.
- [x] Add domain-agnostic aggregate and business-rule tests for grouped totals,
  component formulas, partitions, coverage, temporal windows, paired values,
  and cross-table reconciliation. Include financial/accounting as one fixture,
  not as the product's assumed domain.
  - [x] Cover component formulas, partitions, temporal windows, and paired
    values across logistics, scientific, service, and inventory fixtures.
  - [x] Cover grouped totals, coverage, and cross-table reconciliation,
    including one financial/accounting fixture.
- [x] Preserve relative distributions and order of magnitude while allowing
  synthetic scaling of sensitive totals; record the effective rule set.
  - [x] Add bounded numeric scaling that preserves relative shape and numeric
    types, and reject identity scaling for sensitive numeric distributions.
  - [x] Record the effective generation and business-rule set in the manifest.

- [x] Implement `ValidationSettings` semantics, including `fail_fast`, or
  remove unsupported settings from the public contract.
- [x] Wire `GenerationSettings.locale` into Faker and add locale contract tests.
- [x] Define logical versus byte-for-byte reproducibility and record the
  required runtime, dependency, serializer, locale, and output evidence in the
  manifest.
- [x] Harden profile and Trino category handling: suppress raw categories by
  default, replace endpoint-preserving masks, and add rare-text/quasi-ID tests.
  - [x] Replace raw CSV and Trino category values with ranked synthetic labels.
  - [x] Replace endpoint-preserving masks and add rare-text/quasi-ID tests.
- [x] Document the exact-row limitation and the absence of statistical privacy
  guarantees.
- [x] Publish a threat model for source data, PII, secrets, prompt injection,
  provider and artifact boundaries, and resource exhaustion.
- [x] Distinguish deterministic validation, heuristic safety checks, complete-row
  reuse checks, and operator privacy review without implying certification.
- [x] Expand mypy coverage to the full production package and resolve optional
  `pyarrow` typing and duplicate script-module configuration.
  - [x] Add the CSV profiler to strict mypy coverage.
  - [x] Add I/O and Parquet adapters with an explicit untyped `pyarrow` override.
  - [x] Cover the remaining production modules and duplicate script modules.
- [x] Remove `0.8.1` container defaults or derive them from package metadata;
  add a release drift check.
- [x] Verify release tags point to the verified merge commit and publish
  reproducible security evidence with run IDs and artifact digests.

## P2 — RC disposition required; implementation may follow the RC

- [x] Add bounded JSON row/cell/nested-value validation.
- [x] Add `CODE_OF_CONDUCT.md`, `SUPPORT.md`, `GOVERNANCE.md`, and `CODEOWNERS`.
- [x] Improve GitHub About metadata, README positioning, comparison guidance,
  and the one-command golden-path example.
- [x] Add runnable, CI-verified synthetic examples for single-table CSV,
  relational CSV, local Trino, MCP, Python API, and all supported output
  formats; include one rejected unsafe request and release-style smoke runs.
  - [x] Add the single-table CSV profile/spec/generate/validate journey.
  - [x] Add the relational CSV relationship/rules journey.
  - [x] Add the public Python API generation/validation journey.
  - [x] Add Trino, MCP, and export journeys.
    - [x] Add the CSV, JSON, SQL, and optional Parquet export journey.
    - [x] Add the MCP stdio journey with a rejected pre-network Trino request.
    - [x] Add the local Trino journey with the synthetic TPC-H catalog.
- [x] Defer the oversized agent and Trino orchestration split to the post-1.0
  application-boundaries change; no concrete RC security blocker requires it.
- [x] Defer public good-first-issue/help-wanted backlog creation to post-1.0
  community work after the stable contract baseline is published.

## RC evidence and release gate

- [x] Update `scripts/check_release.sh` with direct API privacy and SQL-boundary
  tests.
- [x] Run the complete unit/property/contract suite with coverage at or above
  the configured threshold.
- [x] Run lint, full-package typing, compile, dependency/license/security,
  documentation, wheel, and container gates.
- [x] Run the workflow from published-style wheel, PyPI, GitHub Release,
  documentation, and GHCR artifacts.
  - [x] Add a manual post-publish workflow that verifies immutable package,
    documentation, attestation, signature, and container-runtime evidence.
  - [x] Run the workflow for `v1.0.0rc2` and record its run URL, exact commit,
    package hashes, and three image digests.
- [ ] Re-run the full security review against the exact RC commit and record
  every remaining P2 or lower finding with owner, rationale, and revisit date.
- [x] Verify at least one end-to-end AI-assisted discovery flow with a local
  fake provider and prove that no raw source rows enter the provider request.
- [x] Allow only release-blocking fixes after `1.0.0rc1`; no new features.
