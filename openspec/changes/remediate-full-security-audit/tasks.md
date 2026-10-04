# Security remediation and conditional RC

## Audit baseline

- [x] Full security source audit at `33a9ebdc3d1d158984945c3053f866cdd20bbc8d`; nine source-validated findings.
- [x] Bounded offline probes for eight findings; no live/private data.
- [x] Owner authorized OpenSpec, fixes, automation, fresh audit and conditional RC.
- [x] Seal canonical audit report and copy stable report reference into evidence.
- [x] Validate this OpenSpec change strictly.

## Fixes (each requires regression, relevant docs and recorded checks)

- [ ] F1: Trino rule residuals reject/suppress sensitive operands, including aggregate-mapping siblings.
- [ ] F2: SQL local categories retain physical sensitivity/identifier lineage through aliases and inspect numeric content.
- [ ] F3: OpenAI provider request masks every local category literal and matching predicate; restore valid field-scoped response labels locally.
- [x] F4: Folder profiling inspects canonical numeric forms before retaining numeric summaries.
- [x] F5: Cache identity/read authorization includes local-category policy; invalidate stale entries; test permission removal/change and predicates.
- [ ] F6: Formula operators enforce operand/result work bounds before allocations, with safe numeric compatibility tests.
- [ ] F7: Parquet dataset reads enforce actual decoded bytes, cell sizes and cumulative dataset cells before list conversion.
- [ ] F8: Single CSV profiling honors inherited MCP deadline through final publication and fails without trusted partial output.
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
