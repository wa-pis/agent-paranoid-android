# Full audit evidence

Runtime: `33a9ebdc3d1d158984945c3053f866cdd20bbc8d`; scan `7c5f98ba-72e6-4081-88a3-bee689b1d599`. Public/source baseline only. No private source rows, credentials or live access.

| ID | Priority | Finding | Offline proof |
| --- | --- | --- | --- |
| F1 | P1 | Trino exact sensitive residuals | fake singleton aggregate retained; zero-formula SQL source trace |
| F2 | P2 | Sensitive SQL column alias becomes local category | authorized synthetic bigint alias retained with sensitive=false |
| F3 | P2 | OpenAI transmits local category literals | fake SDK: default masked; local transmitted; store=false |
| F4 | P2 | Folder exponent identifier enters numeric statistics | exact fictional numeric bound retained; profile safety passed |
| F5 | P2 | Cache preserves categories after opt-in removal | current allowlist empty; original safe enum labels retained |
| F6 | P2 | Formula allocates before budget enforcement | instrumented multiplier 10^12 reached; no huge allocation; small control passes |
| F7 | P2 | Parquet decoded expansion/cumulative cells | encoded8246B, decoded2098176B, limit65536B; accepted256rows |
| F8 | P2 | CSV MCP profiling ignores invocation deadline | injected clock2s vs1s; success and profile publication |
| F9 | P3 | Audit verifier reads full oversized line before bound | independent static CLI-to-parser trace |

The source review covers all production Python modules and release scripts/workflows. Unit tests/docs/specs were supporting evidence rather than independently line-reviewed wholesale. No fresh complete test suite or vulnerability-feed dependency audit was executed during discovery. Earlier passing tests are not proof of remediation.

Canonical report sealed: Codex Security scan `7c5f98ba-72e6-4081-88a3-bee689b1d599`, `report.md`; nine findings (high1, medium7, low1), original immutable runtime SHA. Retained outside repository by Codex Security. Future runs must record the new exact SHA, test results and canonical fresh-audit report before release.

## F9 remediation

Shared `verify_audit_log` reads at most4097bytes before parsing. Synthetic LF/no-LF oversized records fail on first bounded read; exact4096byte authenticated records pass.16audit tests, Ruff, focused mypy, strict OpenSpec and independent read-only candidate review pass. No full release gate or fresh whole-project audit yet.

## F4/F5 remediation

Folder exponent and rounded identifier forms now produce masked patterns without extrema. Cache format5 binds exact sorted scopes, preserves duplicate identity, verifies stored scopes and rejects format4. Tests cover default/allowed/changed permission, order, mismatch, repeated legitimate reuse and canonical privacy.89focused tests passed from writable temporary cwd; Ruff/focused mypy passed; independent review found no surviving route. Whole-project re-audit and RC gates remain pending.

## F1 remediation

Direct service tests prove sensitive targets, zero-multiplied dependencies, and aggregate sum/avg/count sensitive value operands fail before fetch. Existing safe formulas, aggregates and join-key paths pass.109tests, Ruff, focused mypy and independent static candidate review passed.

## F2 remediation

PostgreSQL/Trino alias, identifier, quasi-identifier, cast and aggregate regression cases reject exact category query construction; direct benign aliases remain allowed. Unannotated plans reject before any category fetch. Synthetic numeric SSN, phone and card forms reject without value echo; small integers and booleans pass.202 focused tests, Ruff and focused mypy passed.

Fresh independent read-only F2 candidate review found no concrete bypass or regression; reviewer independently ran181focused tests successfully.

## F3 remediation

Both optional adapters import a dependency-free shared category projection. Original source literals, typed categories and matching predicates are replaced before transport; restorations are local and field-scoped. Fingerprints and caller input remain unchanged. Invalid restored OpenAI proposals are recorded as redacted invalid-response failures before completed metadata. Unknown categorical predicates reject before transport. JSON-mode normalization closes the independent review's tuple in_values bypass and preserves Pydantic JSON serialization.143 offline advisor/OpenAI/GigaChat tests passed, including actual fake transport assertions, string/integer/boolean/null forms, tuple predicates and redacted restoration failures; existing GigaChat reordering/collision/cross-field regressions remain green. No live provider call or fresh whole-project audit performed.

## F6 remediation

The shared ordinary evaluator checks built-in operands and intermediate results. String/byte repetition in either order and concatenation reject prospective oversized results before operators execute. Lists, tuples, bytearray and custom overloaded objects fail closed; integers/Fraction widths, Decimal coefficient/exponent/context precision and non-finite floats are bounded. Synthetic operator spies prove the original10^12repetition never reaches multiplication through direct evaluation, constraint generation/validation and business generation/validation; tests also cover negative/zero repetition, Unicode, nested expansion and numeric compatibility.70focused tests passed; Ruff/mypy passed; independent static review clean. A first run from temporary cwd failed one CLI fixture lookup; repository-cwd rerun passed. Per-operation bounds complement output/deadline budgets; no whole-project audit or release gate completed yet.

## F7 remediation

Shared DatasetSpec-oriented folder reader now uses256-row Arrow batches. It checks actual retained batch bytes before Python conversion, counts dictionary logical payload conservatively in the same cross-file byte allowance, and traverses Arrow scalar leaves without nested Python containers. Dataset rows/cells include all CSV/JSON/Parquet inputs. String characters, binary bytes and nesting are gated before to_pylist. Synthetic compressed/dictionary fixtures reproduce metadata-small decoded expansion and now reject; mixed-format and multi-file limits, typed/null/Unicode controls and forbidden conversion/whole-read spies pass.100focused tests passed; Ruff/mypy/strict OpenSpec passed; independent review found no bypass or regression and ran14focused tests plus bounded map/fixed-list/fixed-binary/null-dictionary checks. Native Arrow decodes a batch before inspection; this is payload accounting, not peak-RSS containment. Upstream Arrow rejected one nullable fixed-list probe before candidate logic; no candidate defect established. Whole-project re-audit and RC gates remain pending.

## F8 remediation

Ordinary CSV path accepts an explicit GenerationBudget and defaults to a local-profile deadline plus captured request deadline. Row-digest profiling and prepare_generation_budget retain the same inherited request clock. Existing checkpoints cover rows, cells, finalization and generation. Profile JSON serialization and atomic writer completion check deadlines; a same-directory rollback link preserves existing output after post-replacement directory-fsync expiry, while a new expired output is removed. Bundle replacement checks run within its rollback block. Synthetic fake clocks prove registered MCP/direct services reject during accumulation/finalization/serialization/file-fsync/directory-fsync and during generation/bundle publication, without trusted output; legitimate existing-file overwrite and no-budget CLI controls pass. Collision/concurrent-write checks preserve foreign files; a rollback failure retains its backup. Independent reviewer found the directory-fsync gap, reproduced it, and reported no other issue; dedicated first/second-fsync regressions close it.299focused tests pass; after final rollback-backup retention change35atomic/deadline tests pass. Ruff, focused mypy and strict OpenSpec pass. Cooperative checkpoints do not preempt active filesystem/parser work. Full release gate and immutable whole-project re-audit remain pending.

Full release-gate attempt at784b1a6: lint/types/compile/licenses/dependency compatibility/direct privacy checks passed;2993tests passed,23skipped,90.29%coverage. One documentation inventory assertion omitted the two still-open changes; corrected explicit expected inventory without closing audit/RC gates. Later operational/schema/smoke stages did not run in that failed attempt; complete rerun required.
