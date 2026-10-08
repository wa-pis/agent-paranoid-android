# Tasks: mcp-client-workflow-1-6-rc2

## 1. Baseline And Contracts

- [ ] Identify the reviewed `1.6.0rc1` baseline and outstanding blockers without
  changing or bypassing the selective-transformation policy gates.
- [x] Map existing MCP descriptions, response contracts, recovery states, and
  SDK tests; identify the smallest missing product and verification pieces.

## 2. Assistant Onboarding

- [x] Add a generator-only quickstart with MCP-extra installation, an absolute
  executable path, workspace configuration, and fictional input preparation.
- [x] Add exact planning, inspection, human-review, approval, and completion
  examples with explicit count, seed, format, and expected metadata fields.
- [x] Document optional Trino handoff separately and link existing setup guides.
- [x] Document missing dependencies, path errors, stale review, interruption,
  state-driven recovery, and fixed transport errors with corrective next steps.

## 3. Tool Guidance

- [x] Clarify existing planning, inspection, approval, and recovery descriptions;
  preserve names, schemas, safety enforcement, and explicit human approval.
- [x] Update frozen description fixtures and focused public-contract tests.

## 4. Executable Acceptance

- [x] Add a bounded real-SDK stdio client test for discovery and the full local
  planning-to-completion workflow, without network or provider credentials.
- [x] Verify no output before approval and reject a stale reviewed fingerprint.
- [x] Verify counts, validation, manifest provenance, explicit-seed replay,
  no source-row reuse, and summary-only responses without source sentinels.
- [x] Exercise interrupted approval and state-driven recovery; confirm published
  outputs are retained without regeneration and errors/logs remain redacted.
- [x] Verify clean session/subprocess teardown on success, failure, and timeout.
- [ ] Record a manual assistant-client run with a fictional fixture, actual
  client/version, exact candidate SHA, human review, and artifact verification.

## 5. RC2 Preparation And Release Gates

- [x] Update roadmap, relevant documentation, OpenSpec, and concise user-facing
  changelog entries for the delivered improvements.
- [x] Run focused MCP, contract, safety, and documentation checks; record results.
- [ ] Run `scripts/check_release.sh`, `mkdocs build --strict`, and the supported
  Python/MCP compatibility matrix on the final reviewed candidate.
- [ ] Prepare `1.6.0rc2` version metadata only once prior candidate blockers and
  required acceptance checks are resolved; keep version sources synchronized.
- [ ] Obtain independent exact-commit review and all release gates; record
  Ubuntu preflight digests and the acceptance manifest per `docs/release.md`.
- [ ] Tag and publish only as separately authorized release work; verify public
  package/container artifacts and record immutable release evidence afterward.
