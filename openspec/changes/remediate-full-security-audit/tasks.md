# Security remediation and conditional RC

## Audit baseline

- [x] Full security source audit at `33a9ebdc3d1d158984945c3053f866cdd20bbc8d`; nine source-validated findings.
- [x] Bounded offline probes for eight findings; no live/private data.
- [x] Owner authorized OpenSpec, fixes, automation, fresh audit and conditional RC.
- [x] Seal canonical audit report and copy stable report reference into evidence.
- [x] Validate this OpenSpec change strictly.

## Fixes (each requires regression, relevant docs and recorded checks)

- [x] F1: Trino rule residuals reject/suppress sensitive operands, including aggregate-mapping siblings.
- [x] F2: SQL local categories retain physical sensitivity/identifier lineage through aliases and inspect numeric content.
- [x] F3: OpenAI provider request masks every local category literal and matching predicate; restore valid field-scoped response labels locally.
- [x] F4: Folder profiling inspects canonical numeric forms before retaining numeric summaries.
- [x] F5: Cache identity/read authorization includes local-category policy; invalidate stale entries; test permission removal/change and predicates.
- [x] F6: Formula operators enforce operand/result work bounds before allocations, with safe numeric compatibility tests.
- [x] F7: Parquet dataset reads enforce actual decoded bytes, cell sizes and cumulative dataset cells before list conversion.
- [x] F8: Single CSV profiling honors inherited MCP deadline through final publication and fails without trusted partial output.
- [x] F9: Audit verification uses bounded line reads before parsing/authentication.
- [x] Commit/push only related changes and record exact fix SHAs.
- [x] Relevant CLI/MCP/direct-service regressions, lint/types, OpenSpec and documentation checks pass.

## Fresh full audit loop

- [x] Complete the full release gate on audit baseline `d4765cf` (2994 passed,23 skipped,90.29%; strict docs pass).
- [x] Independently audit entire immutable `d4765cf`, including all nine fix paths and siblings; four new medium resource findings.
- [x] R1: Bound expanded YAML alias nodes/bytes and reject cycles before model construction.
- [x] R2: Common deterministic generation allocation preflight for direct/export/synthesis callers.
- [x] R3: Bound cumulative folder inference evaluations and check deadlines inside loops.
- [x] R4: Bound Parquet profiling nested logical content before Python conversion.
- [x] Full gate at `b3045ee`:3019passed23skipped90.35%, strict docs pass.
- [x] Complete fresh whole-project audit `603092fd-7dd0-4475-a9a9-1a7f9658f3ae` on immutable `b3045ee`; one medium deterministic-rule resource finding.
- [x] R5: Bound native solver/validation and negative business-rule work across direct/workflow callers.
- [x] Full gate at `3d0289b`:3033passed23skipped, strict docs pass; fresh complete scan `aeca366b-900c-4314-a0cf-cc27f15169b1` found PostgreSQL TLS identity issue.
- [x] R6: Default PostgreSQL to full server identity verification; gate weaker direct/env/JDBC modes before credentials/connect, document migration and verify regressions.
- [x] Full gate and complete independent audit at `28aa253`:3043passed23skipped, strict docs pass; scan `5678a924-0708-46a5-9e57-a852f51946b4`, zero confirmed findings.
- [x] Validate all audit candidates and repair confirmed F1–F9/R1–R6 findings.
- [x] Record complete clean canonical source audit at `28aa253`; final release-SHA review and separate acceptance/release gates remain required.

## Conditional release

- [ ] Close remaining `selective-source-transformation` client/documentation/safety/activation acceptance tasks.
- [ ] Select unused `1.6.0rc1` or next RC; update version metadata/changelog/docs consistently.
- [ ] Review exact release SHA; complete release gate, strict docs and isolated package matrices.
- [ ] Merge through established process with green exact-main CI, Containers, Documentation, Security and required GitHub approval.
- [ ] Record Ubuntu-derived wheel/sdist hashes and exact accepted commit in valid signed acceptance manifest.
- [ ] Set accepted-source variable and push allowed signed immutable RC tag.
- [ ] Verify GitHub Release, PyPI, signed GHCR images, portable provenance and successful Verify Published Release.
- [ ] Record public evidence; stop automation after success. Stable remains unauthorized.

## Progress

2026-10-05: Implementation is queued through active thread heartbeat `apa-security-fixes-audit-rc` (every 30 minutes). The audit found defects; this document does not claim that they are fixed or that RC gates pass. Worktree: `codex/fix-transformation-review`. Preserve the separate main checkout.

2026-10-05 F9 completed: bounded4097-byte reads; LF/no-LF oversized rejection and exact4096-byte authenticated-record compatibility. `pytest tests/test_audit.py -q -p no:cacheprovider`:16passed; Ruff --no-cache passed; focused mypy passed; strict OpenSpec passed. Fresh independent bypass review found no issue. Remaining F1–F8 and release gates stay open.

2026-10-05 F4/F5 completed: reused canonical CSV privacy inspector; format5 cache binds sorted scopes and verifies stored permission; no metadata relabeling on hits.89focused profiling/category/budget tests pass from writable temporary cwd; Ruff, focused mypy and independent candidate review pass. Read-only worktree cache-permission failures were rerun from temporary cwd. F1/F2/F3/F6/F7/F8 remain; next priority Trino sensitive residuals. F9 commit51929db pushed.

2026-10-05 F1 completed: shared Trino builders reject sensitive-name formula target/dependencies and aggregate parent/numeric child values before execution; keep join keys and count semantics.109Trino builder/service/MCP tests passed; Ruff, focused mypy and fresh candidate review passed. Innocuous source names cannot establish content sensitivity; documented existing classifier scope.

2026-10-05 F2: direct source/output category eligibility is retained in the validated query; unannotated plans fail closed. Integer category contents use the existing sensitive-content detector.202 SQL source/profiling/temporal/category tests passed; Ruff and focused mypy passed.

Fresh independent read-only F2 candidate review found no concrete bypass or regression; reviewer independently ran181focused tests successfully.

2026-10-05 F3 completed: OpenAI/GigaChat share field-scoped request projection and local response restoration. Independent review identified tuple in_values bypass; JSON-mode normalization and transport regression close it.143 advisor/provider tests pass; Ruff/mypy and strict OpenSpec pass. F6/F7/F8 and fresh full audit/release gates remain.

2026-10-05 F6 completed: common evaluator checks operand/intermediate widths and sequence operation size before allocation; numeric/Decimal precision bounded.70focused expression/generation/constraint/business/exact-formula tests passed; Ruff and mypy passed. Fresh independent review found no surviving route (reviewer did not run tests; parent ran them with project Python). F7/F8 remain.

2026-10-05 F7 completed:256-row batch gates cover actual bytes, retained-dictionary logical expansion, nested cell/depth/size and cumulative mixed-format counters before to_pylist.100focused reader/CLI/limits/workflow tests, Ruff, mypy and strict OpenSpec pass. Fresh independent review clean; reviewer14tests plus bounded map/fixed-list/binary/null-dictionary probes pass. Native Arrow allocation limitation documented. F8 remains.

2026-10-05 F8 completed: captured invocation budget spans CSV rows/fields/finalization, row digests, generation and publication. Independent review reproduced post-replacement directory-fsync expiry; callback now checks completion and safely restores/removes the published profile. Bundle deadlines use existing rollback.299focused tests pass; final35atomic/deadline tests after backup-retention adjustment pass; Ruff/mypy/strict OpenSpec pass. All nine implementation fixes complete; full release gate and fresh exact-SHA audit remain mandatory.

2026-10-05 fresh audit: scan `f929c897-48b4-406b-a746-90fd55dce79d`, immutable `d4765cf0fe92d10b458f08e2db282cd57901ba19`;141 production Python,21 scripts,9 CI workflows reviewed independently. Four medium resource findings validated with bounded synthetic probes. Canonical report retained in Codex Security; RC blocked. Fresh read-only boundary investigator completed; no source edits by reviewer.

R1 complete: alias-reference expanded-node charge and scalar-byte graph accounting before construction; recursive references reject.142focused tests, Ruff/mypy/strictOpenSpec pass. Reviewer confirmed no unbounded DAG/cycle bypass. Alias-free syntax nodes are not charged against dataset cell allowance; bounded ordinary aliases and low-cell spec compatibility preserved.

R2/R3/R4 implementation complete: generator shared output preflight plus pre-allocation string guard; one cumulative inference budget with captured MCP deadline across rules/relationships; shared Arrow logical checks before profile/read conversion.429focused generation/transformation tests,90Parquet/architecture tests,72budget/Arrow tests,6direct/export/synthesis triggers passed. Expanded run537passed with1Changelog-order failure; repaired and57docs/Parquet tests pass. Ruff,12module mypy and strictOpenSpec pass. Fresh candidate reviewer unavailable (agent thread limit); separate parent bypass/compatibility pass completed, including shared counters, dictionary/null/nested cases, helper callers and ordinary seeded output. Final full gate and fresh exact-SHA independent audit remain open.


R5 implementation verified:453owning-package tests passed4skipped;41rule/condition tests passed after membership-cost accounting;24module mypy, Ruff and strictOpenSpec pass.14new bounded synthetic regressions cover inner native/aggregate expiry, direct helpers, cumulative exhaustion, empty-row dense graphs, pre-generation native rejection, quadratic FK/aggregate estimates and callback compatibility. Fresh candidate reviewer found callback arity regression, now covered and corrected. No confirmed surviving rule-scan bypass. Full gate and a fresh complete audit of the committed final SHA remain required; no RC permission implied by these checks.

R6 investigation: fresh boundary worker unavailable (thread cap); separate parent pass traced direct/env/JDBC resolution and session validation before secret resolution. Existing allow_insecure is the shared exception control. Immutable full audit covers production, scripts, CI, examples, acceptance programs and dependency metadata; external dependency vulnerability/source review and live MITM are not claimed.

R6 verified:237 PostgreSQL/SQL-source tests plus56 CLI/transform-isolation/temporal tests pass; Ruff,2module mypy, strict OpenSpec and docs pass. Fresh independent candidate review passed68tests and24fake-driver mode/opt-in cases, no surviving bypass/regression. Secure default reaches driver as verify-full; weaker modes reject before password resolution/connect unless explicit local opt-in. No live TLS handshake claimed. Full gate and new exact-SHA full audit remain open.

2026-10-05 clean audit:143production Python,21scripts,9workflows,15executableexamples,5acceptance programs and shipped skills reviewed;237unique credited including structural lock metadata. No production/live/provider test or external dependency-CVE claim. Architecture worker unavailable; separate parent source mapping used. Plugin usage25,497,080total including24,680,576cached input is cumulative rollout accounting, not incremental scan cost. New capacity work must pass focused checks; final coherent RC SHA still needs full gate/audit.

2026-10-05 current offline gate at exact5b49167 after MCP deadline and
batched Parquet encoding:3052passed23skipped, one existing Pydantic warning,
90.50% coverage,181.51s. Lint/full production types/compile/dependency licenses
and compatibility/direct privacy and SQL boundaries/operational budgets/schema
freshness/quickstart all passed. Both strict OpenSpec changes and strict docs
passed. TEST_TRINO_INTEGRATION=0 and TEST_POSTGRES_INTEGRATION=0 explicitly;
no live DB/provider calls. This is not final release-SHA audit or exact-main CI
clearance. Eight private fictional100M-cell routes are now confirmed; four
remaining supplied SQL-result routes continue sequentially. Do not repeat
passed checks without a new code change or a required final exact-SHA gate.

2026-10-05 independent pre-activation whole-source scan started:
9e541ae6-3758-4101-9c75-a82a6f944303, immutable prospective Git SHA
f6d8ba7bb7ff18e69b3a846029db464ba946ab22,918tracked files, derived from
b7f743e plus four registration/contract proposals. Source root/pointer:
/private/tmp/apa-frozen-registration-bwrb7ii0 and
/private/tmp/apa-frozen-registration-current.json. Standard preflight ready
with worker-capacity warning; baseline frozen_registration_baseline running.
Extra focused worker spawn hit thread cap; parent handles boundary tracing.
Threat model retained through Codex Security managed artifacts. Scan discovery
incomplete; no clean finding conclusion or final RC clearance. Resume this same
scan/worker next heartbeat; do not start another scan or repeat capacity checks.
Active branch/main common registration remains closed; no release actions.
