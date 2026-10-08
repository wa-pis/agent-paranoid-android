# Implementation Progress

## 2026-10-08: Local Onboarding Slice

- Isolated managed worktree: `/Users/agrudin/.codex/worktrees/mcp-client-rc2/agent-paranoid-android`.
- Branch: `codex/mcp-client-rc2`; baseline tag `v1.6.0rc1`, commit
  `68a20cf333b6d1bdbb02d36e64fb62ef929b2173`. Tag existence and version were
  inspected; public RC1 acceptance and signed-manifest verification remain open.
- Original checkout remains on the unrelated typed-Parquet branch; no edits
  to its runtime or another automation's schedule.
- Copied the approved proposal into this worktree and added the active-change
  documentation inventory entry.
- Added generator-only installation/configuration, fictional CSV, exact calls,
  human fingerprint review, completion summaries, and corrective recovery steps.
- Tool descriptions, real-SDK acceptance, version preparation and publication
  remain pending. No release readiness claim.
- Checks: strict OpenSpec and diff checks passed; documentation tests: 51 passed;
  strict MkDocs build passed; changed-file Ruff passed with cache disabled.
- Next: implement tool guidance and
  bounded real-client workflow coverage against the RC1 runtime.

## 2026-10-08: Tool Guidance And Real Client Slice

- Clarified existing plan/inspect/approve/recover descriptions; explicitly name
  human review, current fingerprint, summary-only results, recovery prerequisites
  and completed-state handling. Names and schemas unchanged; frozen description
  fixture updated deliberately and full public-contract comparison passed.
- Added actual SDK ClientSession + stdio subprocess acceptance using the real
  generator module, explicit source import root, fictional CSV and seed 81.
- Tests discover tools, plan without output, reject the old fingerprint after
  changing row_count, restore and re-inspect the fictional spec, approve,
  inspect completion, verify manifest/counts/validation, reproduce dataset
  bytes in a second workspace and check source-row disjointness.
- Fixture source email sentinels are absent from all captured tool responses and
  stderr. Test approval is automated fictional evidence, not manual acceptance.
- Client reads have a 15-second deadline; workflow has a 60-second deadline;
  SDK contexts manage normal session and subprocess teardown. Explicit failure/
  timeout teardown and interrupted recovery coverage remain pending.
- Updated roadmap and user-facing Unreleased notes without claiming publication.
- Focused MCP server/transport/SDK/client, contract and documentation checks:
  103 passed. Changed-file Ruff passed. No dependency changes.
- Next: real-client interrupted recovery and explicit teardown failure coverage,
  then final docs checks and focused signed implementation commit/PR. Public RC1
  acceptance, final-SHA manual client evidence and full release gates remain open.

## 2026-10-08: Interrupted Recovery And Teardown

- Parameterized the real SDK workflow with a test-only one-shot interruption of
  completion publication in the subprocess. Actual tools/core generation still
  run; this injected failure is fault-testing evidence, not manual acceptance.
- Inspection reports recovery_required/recover; recovery succeeds. Generated
  files retain identical bytes and modification timestamps across recovery.
- Normal, error and timeout client exits verify the server PID no longer exists.
  Async session and process cleanup remain bounded by outer deadlines.
- New unexpected-error sentinel exposed MCP 1 RuntimeError reflection. Extended
  shared transport redaction to runtime causes and exact known cleanup/limit
  types, retaining reconstructed safe diagnostics already used for SDK 2.
  Added OpenSpec scenario and changelog Security entry for this discovered gap.
- Existing wire test now runs unexpected-error/cleanup checks on both majors
  and explicitly binds subprocess imports to the candidate source tree. Initial
  failures identified installed-source drift and cleanup's non-RuntimeError
  inheritance; both regression cases now pass without removing sentinel checks.
- MCP SDK 1.28.1 local focused checks: 108 passed; changed-file Ruff passed.
  Full production mypy passed (150 files) before the final exact-type adjustment;
  repeat types on the final tree. SDK 2 run remains pending, not claimed passed.
- Next: SDK 2 compatibility, final focused types/docs validation, signed commit
  and PR. RC1 public acceptance, full release gates, final-SHA independent review
  and genuine manual assistant-client evidence remain pending.

## 2026-10-08: SDK 2 Compatibility And PR Preparation

- Isolated MCP 2.2.0 focused client/wire/transport run: 69 passed.
  SDK 2 changed timeout from timedelta to numeric seconds and model fields to
  snake_case; tests select the supported timeout shape and inspect isError via
  stable wire aliases. No production compatibility workaround was needed.
- MCP 1.28.1 client plus documentation rerun: 55 passed after test adaptation.
- Full source/tests/scripts Ruff passed; final production mypy: 150 files passed;
  strict MkDocs and strict OpenSpec passed. Existing 108-test SDK 1 focused
  evidence remains applicable to the transport runtime.
- GitHub has published non-draft prerelease v1.6.0rc1 (2026-10-08 01:16 UTC):
  https://github.com/wa-pis/agent-paranoid-android/releases/tag/v1.6.0rc1
  No open PR was returned during overlap check. Public verification and signed
  RC1 manifest acceptance still require separate inspection; existence is not
  proof of acceptance.
- Next: submit the focused signed PR, wait exact-head checks, run remaining
  release gates and obtain genuine manual client/final-SHA review evidence.
