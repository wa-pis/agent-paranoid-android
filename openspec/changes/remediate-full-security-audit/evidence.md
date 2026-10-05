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

## Fresh full audit d4765cf

All original fix commits pushed:51929db,ad2f3a5,9a55501,6591b96,bb15941,153c566,5a8378d,784b1a6; documentation inventory correction d4765cf. Full release gate2994passed23skipped90.29%, strict docs passed.

Canonical scan:f929c897-48b4-406b-a746-90fd55dce79d. Report: `/Users/agrudin/.codex/state/plugins/codex-security/scans/agent-paranoid-android/d4765cf0fe92d10b458f08e2db282cd57901ba19_20261004T222737Z_q71xo249/report.md`. Independent141 production modules21scripts9CI full-file static review, parent source traces and synthetic bounded probes. Four medium findings: YAML alias expansion, direct generation allocation, folder combinatorial inference, Parquet profile nested expansion. No production/live/external-provider calls. All remain release blockers until fixed and freshly reviewed. Additional architecture worker initially unavailable; parent mapping substituted.

R1 verification:142tests in test_yaml_expansion_limits/test_io_commands/test_transformation_policy passed; Ruff and mypy serialization passed; strictOpenSpec passed. Fresh reviewer6regressions passed; total base syntax-node mismatch was assessed as outside documented alias-expansion charge, preserving alias-free specs with low dataset-cell limits. Original amplification and recursive-alias triggers reject before construction.

## Follow-up R2/R3/R4 candidate verification

Shared output estimate moved from I/O to generation and called before Faker/row creation. Direct generator, SQLexport and transformation synthesis regressions reject oversized allocation before generate_row; bounded seeded control passes. String construction caps length before join.

Formula/temporal/conditional/aggregate/relationship inference pass one explicit LocalProfileBudget. Candidate and row work uses cumulative max_business_rule_evaluations, and deadline checks include the captured MCP request. Empty-row candidate enumeration is charged too. Fake-clock confidence test stops after first row; exhausted wide profile publishes no cache. Ordinary first formula and confidence remain unchanged.

Parquet profile and dataset read reuse core Arrow leaf walking and batch counters. Tests reject nested leaf count, depth, string length, cumulative batches and retained dictionary logical expansion before nested Python conversion; ordinary bounded composite remains sensitive. No native decoder peak-RSS promise.

Checks:429focused generator/transformation tests;90Parquet/IO/architecture tests;72budget/Arrow tests;6direct/export/synthesis triggers. Expanded538-test run had537pass1Changelog duplicate/order failure; corrected existing Security heading and57docs/Parquet tests pass. Ruff src+new regressions, focused12module mypy and strictOpenSpec pass. Fresh candidate agent could not spawn (thread limit); parent performed separate read-only bypass/regression pass before final verification. No unresolved concrete candidate. Full gate/new exact-SHA audit still required.


## Fresh full audit b3045ee and R5 candidate

Full release gate:3019passed23skipped90.35%; strict docs passed. Scan
`603092fd-7dd0-4475-a9a9-1a7f9658f3ae` completed on immutable
`b3045ee55cfadf634f7443fd2c8800112993441e`:143production Python modules,
21scripts,9CI workflows,18executable examples and5acceptance programs reviewed.
Canonical report is retained in Codex Security. One medium/high-confidence
finding: native solver/post-solve validation lacks inner work/deadline checks;
negative business FK and aggregate scans have understated linear estimates.
Bounded fake-clock probe performed12date parses after the first expired parse;
4/8-row negative FK probes visited16/64parents for estimates8/16. No live data,
DB or external AI calls. Empty Arrow containers were rejected as a candidate:
the documented limit counts scalar leaves and makes no native-RSS guarantee.

R5 candidate adds cumulative rule iteration/expression accounting to the existing
explicit GenerationBudget, native preflight before row generation, actual-row
business preflight with mode-aware quadratic bounds, and shared budgets through
solver, mandatory/report validation and I/O callbacks. Direct APIs remain bounded.
Resource exceptions escape broad formula handlers. Fresh independent candidate
review confirmed one callback-arity regression; fixed independently selected
2/3positional argument shape and explicit keyword-only budget forwarding.
13new synthetic cap/deadline/direct/callback regressions pass. Earlier owning run
303passed4skipped with4test-double signature failures; test doubles now implement
GenerationBudget and explicit optional budget. Repaired52tests pass. Focused
24module mypy and Ruff pass. Full gate, final candidate verification and fresh
exact-SHA full audit remain mandatory; R5 is not marked complete yet.


Final focused verification:453passed4skipped in30.40s, including architecture,
documentation, native/business rules, expressions, I/O, batch transformation and
request budgets. Membership costs now charge the predicate width within the
same budget;41business/rule regressions pass after that adjustment.24module
mypy and Ruff pass.14new cap/deadline/callback regressions include the confirmed
original triggers and ordinary valid/seeded controls. Independent review's sole
callback compatibility defect was repaired. Full release gate and fresh full
exact-SHA security audit remain open.

Standalone supplemental R5 fix report (sealed baseline scan unchanged):
`/Users/agrudin/.codex/state/plugins/codex-security/scans/agent-paranoid-android/artifacts-6228a9da09a5649cfa26589ce21af5175a4b834568b9b1ae7462ed21d12ee674/artifacts/fix_report.md`.

## Fresh audit of 3d0289b and R6

Full offline release gate:3033passed23skipped, strict docs pass. Complete independent whole-source audit `aeca366b-900c-4314-a0cf-cc27f15169b1` at `3d0289b4fce8bd66a4b6b671c5fcbef104e2fece` found one high-severity, medium-confidence PostgreSQL server identity issue. Remote endpoint impersonation is required; no DB writes/admin grants or live MITM test are assumed. Historical hardening disposition was considered and does not supply explicit accepted-risk policy. Fake-driver probe confirms require/password forwarding without opt-in, no network access.

Canonical sealed report: `/Users/agrudin/.codex/state/plugins/codex-security/scans/agent-paranoid-android/3d0289b4fce8bd66a4b6b671c5fcbef104e2fece_20261005T044617Z_srnb8et2/report.md`. Code remains unreleasable until R6 verification and a new complete audit. Audit usage returned by plugin is cumulative rollout accounting:24,950,525 total tokens including24,029,440 cached input tokens; not isolated incremental audit cost.

R6 candidate verified:237+56owning tests passed; Ruff/2module mypy/strictOpenSpec/strictdocs passed. Fresh independent candidate reviewer68tests+24fake-driver mode cases passed. Implementation uses existing config validation before credential resolution, no driver fallback. No network/live handshake claimed. Full gate and fresh final-SHA audit pending.

## Clean exact-SHA source audit

`28aa2538d4e6bf8cda018c4fc4e3a45764780fcb`: full gate3043passed23skipped, strictdocs pass; clean complete scan `5678a924-0708-46a5-9e57-a852f51946b4`. Canonical report: `/Users/agrudin/.codex/state/plugins/codex-security/scans/agent-paranoid-android/28aa2538d4e6bf8cda018c4fc4e3a45764780fcb_20261005T052322Z_fufzvm3q/report.md`.143production modules,21scripts,9workflows,15executableexamples,5acceptance programs, shipped skills and full dependencygraph/1398artifact records reviewed; no missing implementation paths. Supporting prose/tests consulted, not every line reviewed. No live deployment/CVE or absolute-safety claim. Final coherent release candidate requires its own exact-SHA gate/audit.

Calibration addendum: previous PostgreSQL finding has high impact/medium likelihood, hence medium severity under the scan matrix; sealed prior report remains unchanged. Supplemental `artifacts/postgres_tls_severity_addendum.md` records this correction; fix obligation unchanged.

GitHub read-only reconciliation:main8670e56protected, activationPR601merged and ancestor of main/current branch. PR602 is OPEN draft atd104cab11edb12f3cf80b207b8a6bada66961712; earlier closed/ac7f notes are historical/stale. Its CI/approval is not proof for current branch; no PR exists for fix-transformation-review. Required CI starts disposable Trino with synthetic tpch.tiny; user clarification about live-DB prohibition is pending before triggering CI. No messages/comments/reviewer requests sent.

2026-10-05 capacity follow-up: installed private CSV target passed at b49ceed
(100M cells, 1188.870s); fictional isolated PostgreSQL-result → CSV target
passed at 611b781 (100M cells, 1412.882s). Both exact wheel/harness/budget and
full ordered readback/cleanup evidence are recorded in the selective-source
scale documents. No live DB/provider call, public activation or all-route
clearance. Full final-SHA gate/audit and required release gates remain open.
Next capacity inspection: `io/transformation_parquet.py` currently collects
all normalized rows before `Table.from_pylist`; target Parquet output has not
been tested. Inspect bounded encoding and temporal single-offset semantics
before any rewrite; do not repeat already passed CSV target runs.

2026-10-05 Parquet capacity correction: removed the encoder's second full
normalized row collection in favor of 1024-row ParquetWriter groups. Timestamp
offsets are validated in a constant-storage first pass without consuming the
one-shot source iterator; encoding performs full normalized/source validation.
208 owning tests passed, 4 optional cases skipped; two new regressions cover
batch lengths/full readback/late source mismatch and null-prefix/late offset
change. Ruff, owning-module mypy, strict selective OpenSpec and strict docs
passed. Synthetic 2051 × 3 private CSV → Parquet harness passed (0.144s).
Full target format acceptance and final-SHA gate/audit remain open.

2026-10-05 installed private CSV → Parquet target passed at 15cd2d4:
100M cells, 1488.050s, 17,398,511 encoded bytes; full typed ordered readback,
mapping precedence, provenance/digest and cleanup. Owning publication/SQL
regressions: 326 passed. SQL fixed-fixture artifact readback added to the
same harness; 10 × 100 smoke and Ruff passed. No DB execution, no public
activation or final-SHA audit clearance is implied.

Current full offline release gate: exact5b49167;3052passed23skipped,
90.50%,181.51s. Log `/private/tmp/apa-current-release-gate-5b49167.log`;
coverage data `/private/tmp/apa-current-release-coverage`. Strict docs log
`/private/tmp/apa-current-release-doc-build.log`, site
`/private/tmp/apa-current-release-doc-site`; both strict OpenSpec checks passed.
Operational checks: profile0.443569s/2,349,310bytes, generation0.683175s/
2,580,524bytes, validation0.419112s/314,028bytes. Explicit disabled live DB
integration flags; all existing release-script stages passed.
PostgreSQL → Parquet target additionally passed in the b249699 queue:
100M cells,1602.427s,17,493,375 output bytes; recorded wheel/harness and
lifecycle/provenance/readback/cleanup evidence in sql-scale-acceptance.md.
Current private fixture matrix8/12. Fresh independent final-SHA source audit,
public/client acceptance and actual release gates remain open; past clean28aa
report is not proof of current/final SHA.

2026-10-05 post-fix independent audit completed and sealed: exact
2fcacae05ae9566e3a53aa69db24535463e12619, scan881daf8e.
193 executable/config paths fully reviewed by independent baseline; additional
SQL/support metadata inspected. Two open findings: R10 medium binary masking
and R11 low category prefetch allocation. No live DB/provider/production data.
Report: apa-postfix-coherent-kx37frd3/
2fcacae05ae9566e3a53aa69db24535463e12619_20261005T184956Z_katt3gji/report.md
under the Codex Security scan store. Category impact statically validated;
binary path reproduced with synthetic actual driver/MCP serialization.
Tests/inert prose/fixtures/upstream advisory coverage explicitly limited.
Plugin usage35,364,290total/34,352,128cached is cumulative rollout accounting,
not incremental cost of this scan. R10/R11 fixes and fresh exact-SHA audit
remain required; no RC clearance. Existing full gate was not repeated.

2026-10-06 R10 remediation verified: shared returned-value exact scalar
allowlist masks binary/unsupported leaves and nonnumeric map keys before
serialization. 116 focused masking/MCP server/SDK roundtrip tests passed;
Ruff, owning mypy, strict OpenSpec and diff check passed. New synthetic
regressions cover binary representations, nesting, map keys, unsupported
subclasses and preserved numeric/Decimal/temporal types. Independent
r10_review found no surviving safe-select bypass/regression. Historical
mask_row is a separate aggregate helper with no production safe-select
caller; it is not this returned-row control. No production/live DB/provider
execution. R11 and fresh composed exact-SHA full gate/audit remain open.

2026-10-06 R11 independent candidate review found no concrete surviving
bypass/regression. Owning mypy, strict docs/OpenSpec, diff check passed;
SQLGlot parses both PostgreSQL/Trino CASE statements. Validation is offline
SQL structure, caller rejection and existing synthetic profiler tests;
native database execution semantics not exercised under no-live-DB rule.
Keep R11 open until stronger offline rejection/compatibility regressions
and composed final gate are recorded. No release clearance.

2026-10-06 R11 offline remediation checks complete:61 focused tests
pass, including NULL projection rejection before publication for PGtable
and PG/Trinoquery with source mutation after summary. Existing string
category roundtrip/default metadata-only/count invariants remain covered.
SQLGlot parses both dialects; earlier58tests/Ruff/mypy/docs/OpenSpec and
independent reviewer clean for bounded driver-return control. Native DB
execution remains intentionally unperformed; full composed gate/audit next.

## R12 ordinary Trino category allocation (2026-10-06)

Fresh scan `e85d9c23-f678-4859-a2ab-fd121f4942c2` at immutable
`12528430e090060e6b79da1cf917e5044dfc2687` independently validates a
LOW conditional availability issue: normal table category query returns an
unbounded source string before driver/result-byte accounting. The frozen
scan remains open until its independent whole-source validation finishes.

Candidate bounds and returns the same VARCHAR representation in the shared
builder, preserving original grouping/counts. Oversized NULL sentinels reject
before summary classification/publication. Character ceiling reuses the
existing input-cell setting; UTF-8 ceiling is four times that setting.
Synthetic Unicode/empty/count controls and source-change sentinel regression
pass with nearest Trino tests:185passed. Ruff, owning mypy, strict MkDocs,
strict OpenSpec and diff check pass. Independent prepatch investigator
completed. Candidate reviewer spawn/reuse unavailable due host thread limit;
parent performed separate challenge pass, not independent approval. No live
DB/provider/production inputs; native engine semantics remain unexecuted.
This does not establish final release-SHA safety or release clearance.
