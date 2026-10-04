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
- [ ] Commit/push only related changes and record exact fix SHAs.
- [ ] Relevant CLI/MCP/direct-service regressions, lint/types, OpenSpec and documentation checks pass.

## Fresh full audit loop

- [ ] Complete the full release gate on final source.
- [ ] Independently re-audit the entire final project at exact immutable SHA, including all nine fix paths and siblings.
- [ ] Validate every new candidate; repair confirmed findings and repeat affected tests and full audit.
- [ ] Record clean complete canonical audit; no open validated findings, deferred blocking candidate or skipped required checks.

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
