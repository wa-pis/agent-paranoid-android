# Tasks: 1-0-0-rc1-security-hardening

## P0 — release blockers before `1.0.0rc1`

- [x] Define and implement `assert_spec_safe()` for every `DatasetSpec`.
- [ ] Enforce the spec safety gate in direct Python generation, bundle
  workflows, CLI, agent, and generator MCP paths.
- [x] Reject raw sensitive/unknown categorical values and unsafe sensitive
  distributions before row generation or artifact publication.
- [ ] Add regression tests for manually constructed and malicious on-disk
  specs through Python, CLI, and MCP.
- [ ] Make unrestricted Trino execution private and route all external calls
  through safe query validation or dedicated bounded methods.
- [ ] Add mocked-cursor tests proving unsafe SQL is rejected before execution.
- [ ] Verify that safe metadata and aggregate profilers still work through
  dedicated internal query builders.

## P1 — required before final `1.0.0` or explicitly accepted by an independent reviewer

- [ ] Implement `ValidationSettings` semantics, including `fail_fast`, or
  remove unsupported settings from the public contract.
- [ ] Wire `GenerationSettings.locale` into Faker and add locale contract tests.
- [ ] Define logical versus byte-for-byte reproducibility and record the
  required runtime, dependency, serializer, locale, and output evidence in the
  manifest.
- [ ] Harden profile and Trino category handling: suppress raw categories by
  default, replace endpoint-preserving masks, and add rare-text/quasi-ID tests.
- [ ] Document the exact-row limitation and the absence of statistical privacy
  guarantees.
- [ ] Expand mypy coverage to the full production package and resolve optional
  `pyarrow` typing and duplicate script-module configuration.
- [ ] Remove `0.8.1` container defaults or derive them from package metadata;
  add a release drift check.
- [ ] Verify release tags point to the verified merge commit and publish
  reproducible security evidence with run IDs and artifact digests.

## P2 — RC disposition required; implementation may follow the RC

- [ ] Add bounded JSON row/cell/nested-value validation.
- [ ] Add `CODE_OF_CONDUCT.md`, `SUPPORT.md`, `GOVERNANCE.md`, and `CODEOWNERS`.
- [ ] Improve GitHub About metadata, README positioning, comparison guidance,
  and the one-command golden-path example.
- [ ] Split oversized agent and Trino orchestration modules where needed for
  maintainability without expanding the product surface.
- [ ] Create public good-first-issue/help-wanted backlog items.

## RC evidence and release gate

- [ ] Update `scripts/check_release.sh` with direct API privacy and SQL-boundary
  tests.
- [ ] Run the complete unit/property/contract suite with coverage at or above
  the configured threshold.
- [ ] Run lint, full-package typing, compile, dependency/license/security,
  documentation, wheel, and container gates.
- [ ] Run the workflow from published-style wheel, PyPI, GitHub Release,
  documentation, and GHCR artifacts.
- [ ] Re-run the full security review against the exact RC commit and record
  every remaining P2 or lower finding with owner, rationale, and revisit date.
- [ ] Allow only release-blocking fixes after `1.0.0rc1`; no new features.
