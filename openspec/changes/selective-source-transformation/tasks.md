# Tasks: selective-source-transformation

## Current security/configuration checkpoint — 2026-10-05

Clean full source audit at `28aa253` and full offline gate: 3043 passed, 23 skipped; final release SHA still needs renewed review. Current GitHub PR602 is OPEN draft at `d104cab`, superseding older closed/ac7f status notes. Its checks do not establish current-branch approval. Configurable generator MCP deadline is implemented and verified; all-route 1M × 100 acceptance remains open. Required CI uses a disposable synthetic Trino service; clarification of the live-DB restriction is pending before CI dispatch. No current RC clearance/publication claimed.

## Corrected installed evidence checkpoint — 2026-10-04

Closed implementation PR602 is draft at ac7f76f; author registration switches
remain unapplied. Corrected isolated runtime3c00148 / installed wheel dd6b4ad2
has current-artifact evidence for twelve typed routes/36 refusals, explicit
temporal outputs, linked/composite keys/null mappings, interactive saved mappings
through CLI and SDK stdio, six-method auth contracts and PostgreSQL diagnostics.
See [current acceptance evidence](client-acceptance.md) and
[route evidence](route-workflow-acceptance.md); no additional tests ran for this
reconciliation. Older unchecked parent tasks below are acceptance gates, not
claims that every listed implementation is absent. Historical accepted-main
notes and earlier intake prerequisites are superseded only where dated current
evidence explicitly supplies the same requirement, never by inference.

Remaining local consolidation includes original-finding profiling/publication
boundaries and final documentation/contract disposition. Independent exact-SHA
clearance remains unavailable; activation, protected merge, final RC gates and
public artifact acceptance stay open. No private/live result, native timestamp
input, every-route scale or independent-review pass is implied.

## Owner-approved uniform mapping amendment — 2026-10-02

- [x] Record explicit owner decision and successor ADR-0029; source membership
  is not a mapping rejection, sensitivity is a value-free field note.
- [x] Remove text-only membership preflight without removing source/evidence
  canonicalization, direct preserve restrictions or receipt verification.
- [x] Track actually mapped cells through private CSV/SQL/Parquet execution;
  retain checks for synthesis/derive/preserve and malformed/absent evidence.
- [x] Add fictional mapping permutation/readback tests and candidate R2-2/3/4
  fixes with focused Parquet deadline/sensitivity and identity-cleanup tests.
- [x] Finish baseline/activation amendments and complete installed candidate
  acceptance for the changed contract without claiming private/live data passed.
- [x] Independently review finished exact changed SHA before public activation;
  final RC version review, GitHub checks and release remain separate gates.
  Evidence: ActivationSafety-R3 exact 911ade071e4a309ab3e3538dfe6c4a9f676624aa,
  installed registered-interface acceptance and merged PR #601. Subsequent SDK
  compatibility fixes remain part of final exact-RC review, not this closure.

## Accepted-main evidence reconciliation — 2026-10-02

Accepted main: 8670e562f50980cfd62678c6f0f51d4887cb8961. This inventory
consumes prior evidence; it is not a new test run or final RC acceptance.

- Basic twelve-route replacement workflow is recorded in
  [route evidence](route-workflow-acceptance.md). Null/empty, DECIMAL and temporal
  output unit checks exist in `tests/test_transformation_parquet.py` and
  `tests/test_transformation_sql.py`, but do not close the complete twelve-route
  typed/readback/publication matrix below.
- Resource defaults admit 1M rows and 100M cells, with explicit byte ceilings;
  `core/transformation_limits.py` defines session > profile > legacy > default
  precedence. Input/total-limit tests cover boundaries and configuration recovery.
  This is not measured 1M x100 acceptance or every-route scalability proof.
- Installed capability discovery now checks both public transformation commands
  and rejection of missing execution inputs (`scripts/check_installed_package.py`).
  Prior closed-engine unavailable-command evidence remains historical. Packaging
  and help discovery alone do not close skill-guided workflow acceptance below.
- Single-table SQL aggregate implementation and rejection tests are present;
  baseline/docs, independent safety evidence and remaining acceptance must be
  reconciled separately before closing the second aggregate task.

## Owner-approved capacity and actionable limits — 2026-09-28

- [x] Private replacement-only CSV installed-wheel acceptance300,000 x50:
  15M cells, full ordered readback, column/global precedence, no cascade,
  manifest/provenance and cleanup; see [evidence](csv-scale-acceptance.md).
  Public/multi-route and1M x100 acceptance below remain open.

- [x] Private installed PostgreSQL-result worker → review → CSV acceptance
  300,000 x50 with fictional injected driver, full readback and cleanup;
  independent transformation limits and bounded row groups. See
  [evidence](postgres-scale-acceptance.md). No live DB/public activation claim.

- [ ] Support target 1,000,000 rows x100 columns across transformation routes;
  audit hidden constants, byte/time ceilings and SQL aggregate-budget coupling.
  - [x] Replace fixed generator MCP 120-second deadline with finite operator configuration shared by transport/services; verify startup/invalid settings. Validation: 192 focused tests passed; Ruff, server mypy, both strict OpenSpec checks and strict documentation build passed. Parent boundary review confirmed a shared captured finite deadline, unchanged default/byte caps, and value-free startup errors. Full release gate and independent audit must cover the final candidate SHA.
  - [x] Make CSV acceptance byte/time ceilings explicit; 10 × 3 smoke and five invalid-budget startup checks passed. Target fixture exceeds the old fixed 512MiB; target proof remains open.
  - [x] Installed private CSV 1M × 100 passed at b49ceed: 100M cells, complete readback/provenance/cleanup, 1188.870s, explicit 1GiB / 3600s. See csv-scale-acceptance.md.
  - [x] Installed fictional PostgreSQL worker → CSV 1M × 100 passed at 611b781: 100M cells, complete readback/provenance/cleanup, 1412.882s, explicit 1GiB / 128MiB capture / 3600s; ordinary profiling caps unchanged.
  - [x] Encode Parquet in 1024-row groups, preserving global timestamp offsets and one-shot source checks: 208 passed / 4 skipped owning regressions, mypy, Ruff, strict OpenSpec/docs; 2051 × 3 CSV → Parquet complete readback smoke passed. Target format proof remains open.
  - [x] Installed private CSV → Parquet 1M × 100 passed at 15cd2d4: 100M typed cells, complete readback/provenance/cleanup, 1488.050s, 17,398,511 output bytes.
  - [x] Installed private CSV → SQL artifact 1M × 100 passed at 2d878f7: all ordered INSERTs/cells/framing/readback/provenance/cleanup, 1435.367s, 2,140,502,692 bytes; no SQL execution.
  - [x] Installed private Parquet → CSV 1M × 100 passed at b5640de: complete 100M-cell readback/provenance/cleanup, 1375.641s, 600,500,900 bytes. Matrix now records 5/12 private fictional target routes.
  - [x] Installed private Parquet → Parquet 1M × 100 passed at cc3aedb: full 100M-cell typed readback/provenance/cleanup, 2169.105s, 17,398,511 bytes; current private fixture matrix 6/12.
  - [x] Prepare fictional supplied Trino-result harness through common authorization/capture, without network adapter/server/worker claims; three 2051 × 3 output smokes and PostgreSQL compatibility smoke passed. See sql-scale-acceptance.md; target proof stays open.
  - [x] Installed private Parquet → SQL 1M × 100 passed at 92bb1b6: full 100M-cell ordered SQL artifact/provenance/cleanup, 3398.476s, 2,140,502,692 bytes; no SQL execution. Current private fixture matrix 7/12; queue is running PostgreSQL → Parquet.
  - [x] Installed fictional PostgreSQL worker → Parquet 1M × 100 passed in b249699 queue: typed 100M-cell readback/provenance/digest/lifecycle/cleanup, 1602.427s, 17,493,375 bytes. Current private matrix8/12; PostgreSQL → SQL running.
  - [x] Installed fictional PostgreSQL worker → SQL 1M ×100 passed in b249699 queue: 100M-cell ordered SQL text/provenance/digest/lifecycle/cleanup,1575.730s,2,240,002,792bytes; no SQL execution. Current private matrix9/12; fictional Trino result → CSV running.
  - [ ] Complete remaining route scale acceptance; configuration alone is not proof.
- [x] Expose/document effective run/session and saved-profile resource settings,
  ranges and precedence without increasing source-free disclosure budgets.
- [x] Preserve typed value-free limit errors through core, adapters, worker,
  CLI/Python/MCP: requested vs observed, limit, units, configuration origin,
  working session instructions and actual profile key; no partial publication.
- [x] Verify boundary/one-over/config-precedence/recovery cases and complete
  fictional 300,000 x50 end-to-end acceptance with measured resource evidence.
  Evidence: input/total/output limit tests, SDK compatibility/typed diagnostics
  in PR #601, current configuration reference, and the two installed scale
  checkpoints above. Public twelve-route refusals supplement them; no new scale
  rerun, hard-RSS promise or final RC artifact acceptance is implied.

## Authorized SQL aggregate follow-up — 2026-09-28

- [x] Implement owner-approved single-table SUM/COUNT/MIN/MAX/AVG and optional
  GROUP BY, preserving column/table allowlists, sensitivity and resource budgets.
  Executable evidence: `tests/test_sql_query_source.py` aggregate accepted/rejected
  shapes, column authorization and AST budgets for both adapters; implementation
  and docs are on accepted main. No live backend claim.
- [ ] Amend SQL baseline/docs; prove accepted and rejected shapes for PostgreSQL
  and Trino with fictional tests; independently safety-review the exact SHA
  before public activation. No internal formula engine or live DB access.

## Owner scope correction — 2026-09-28

The owner clarified that aggregates belong to allowlisted, bounded SQL queries
executed by the database. Transformation consumes their result tables; aggregate
columns are ordinary input fields. An internal formula engine, SQL-to-formula
translation, recomputation of financial totals/balances and nullable-formula
semantics are NOT required for 1.6.0rc1. Earlier text implying that requirement
was an assistant scope expansion and is superseded by this correction, not a
record of owner authorization. Existing private derive code/tests are historical
implementation evidence, not release gates or authorization for public activation;
existing source-free generation remains unchanged. Key mapping, one-to-one rows,
exact numeric types, sensitivity controls and SQL budgets remain in scope.

Budget-aware continuation: [remaining-work reconciliation and next complete
deliverable](resumption-plan.md). Existing checkboxes retain their acceptance
meaning; the reconciliation does not mark partial implementations complete.

## Specification

- [x] Record owner-confirmed independent input/output format contract (2026-09-27).
- [ ] Separate shared transformation/validation from CSV-specific parsing and
  rendering, retaining existing CSV regression evidence.
- [x] Implement input adapters for CSV, Parquet and separately authorized bounded
  Trino/PostgreSQL query results; no SQL-file import or real DB access in tests.
  Captured-result envelopes are implemented; capture stays private. Native type
  exclusions in policy-contract remain explicit, including timestamps/nested data.
- [x] Implement independently selected CSV, Parquet and SQL-script output
  adapters; bind format/dialect settings to approval; never execute output SQL.
- [x] Verify all 12 input/output combinations with fictional data, common field
  policy semantics, logical readback, decimal/null/date fidelity and atomic
  publication failure checks. Query fixtures do not count as live acceptance.
  Installed --public typed route matrix plus36 stale-digest/budget/overwrite
  refusals: [evidence](route-workflow-acceptance.md). Explicit textual DATETIME
  output has separate three-route evidence; native timestamps remain unsupported.
  No all-format scale, arbitrary crash/race recovery or twelve-route SDK claim.

- [x] Record one-to-one rows and explicit reference-field preservation.
- [x] Record financial replacement, zero/rounding equality exceptions and
  declared dependencies.
- [x] Separate the proposed transformation surface from existing generation.
- [x] Define safety approval gates and acceptance scenarios.

## Before Implementation

Internal groundwork (not end-to-end feature acceptance): private action/mapping
models, column coverage/identity checks, strict inline primitives/dates, bounded
CSV snapshots/parsing and integer normalization have landed through PR #528.
An inactive safety amendment and private receipt helpers have landed; public
execution remains unavailable. Review [the boundary](safety-boundary.md) before
enabling the CSV vertical slice. Private implementation and isolated fictional
tests precede final implementation review; activation follows passing end-to-end
safety tests and independent review, not the reverse.
The user selected trusted local CLI operator approval; equal-privilege agent
impersonation is outside that deployment boundary. This selects transport, not
approval of any dataset or completion of the safety amendment below.

The preceding paragraph records the historical pre-activation checkpoint.
PR #601 subsequently registered reviewed CLI/MCP execution after R3 and required
gates. Final RC release remains distinct; old pending wording does not undo
that accepted activation or imply final release acceptance.

See [milestones](plan.md) for the approved order and release scope. Safety-policy
amendments still require scoped review and executable checks before activation.

- [ ] Review the new trust boundary and approve a scoped amendment to
  AGENTS.md, project safety policy and affected baseline specifications.
  - [x] Record owner decision separating closed development/tests from activation.
  - [ ] Independently review this development/activation clarification.
- [ ] Finalize versioned field policy, CLI/API and mixed-origin artifact schema.
- [ ] Specify exact decimals, precision/scale/rounding/overflow, approximate
  DOUBLE conversion and CSV round trips; preserve existing schema compatibility.
- [ ] Define fixed-snapshot/replay semantics, mapping domains and state cleanup.
- [ ] Define financial tolerances, impossible-replacement behavior and safe
  aggregate disclosure. Keep user decisions above unchanged.

## Implementation And Acceptance

### Refreshed client intake (2026-09-24)

Details, ordering and decisions: [feedback v2](feedback-2026-09-24-v2.md).
This intake checklist predates the corrected installed evidence checkpoint above.
Current-artifact results and disclosed gaps are recorded in client-acceptance.md;
unchecked composite gates do not mean that all constituent checks remain unrun.
In particular, corrected-wheel doctor/mode, predicate/units, exact DECIMAL,
Parquet, auth, query/category budget, publication and linked-route evidence must
not be rerun solely because these historical intake boxes are still unchecked.
Final compatibility/clearance and unavailable private/live claims remain open.

- [ ] Inspect new/changed harnesses; record package/version/SHA or wheel hash,
  extras, probe hashes and safe isolated baseline/candidate execution plans.
- [ ] Reproduce/fix 22: allowed AND/OR/nested predicates on both SQL adapters;
  retain forbidden-function, authorization and budget negative controls.
- [ ] Reproduce/fix 25: all generation entrances honor documented explicit/omitted
  mode and ratio precedence; effective spec/manifest/report/exit reflect execution.
- [ ] Reproduce/fix 20: doctor retains failed checks, distinguishes missing extras
  from capability failures and gives safe recovery hints without backend text.
- [ ] Consolidate 21's October 2 approved six-method auth/secret-indirection
  implementation, local CLI opt-in and installed evidence into the final candidate;
  complete exact-SHA safety review before public activation. No live access.
- [ ] Integrate 23 into exact-decimal contract and carry precision/scale through
  agreed profile/spec/generation/transformation/exports without float
  intermediates; internal formulas are excluded by the owner scope correction.
- [ ] Consolidate 24's declared Parquet physical/readback evidence with 25's
  October 2 invalid-result/exit decision; retain fail-closed incompatible typed output.
- [ ] Consolidate 26's October 2 approved unknown-metadata and bounded-sensitivity
  implementation/evidence; finish final-candidate CLI/API compatibility gates.
- [ ] Reconcile refreshed 1–19 evidence: missing date bounds, SQL diagnostics and
  scan costs, formula dependencies, publication/overwrite and utility boundaries.
- [ ] Extend candidate matrix to findings 1–26 and section E safeguards; record
  unavailable private/live cases honestly. Full scope and final RC gates unchanged.

### Existing transformation and release requirements

- [x] Reconcile every client finding against [client acceptance](client-acceptance.md),
  with disposition and executable evidence; do not treat supplied fix prompts
  or monkeypatches as approved implementation instructions.
- [ ] Locally replay reviewed client scripts against isolated baseline and
  installed candidate-branch packages; record per-requirement before/after
  results, disclosed harness adaptations and genuinely unverified private cases.
- [x] Support inline YAML and local CSV mappings with equivalent validation;
  keep external script/API execution an unapproved future TODO.

- [x] Implement bounded local CSV transformation with explicit field actions.
- [x] Make the first CSV replacement primitive unconditional exact-text
  file-wide and per-column lookup tables (`true -> false`, `001 -> 1`) with
  one-pass matching, duplicate-key rejection within each table and no type
  inference. Apply column match before file-wide match, then declared fallback.
  Keep preservation/unknown-value gates.
  Add opt-in bounded local dry-run/trace with row, column, scope, rule ordinal and
  status, plus counts, but no literals or value hashes; test trace/execution
  consistency and value-free errors on fictional data.
  - [x] Record column-over-global precedence; no cascade (owner decision).
  - [x] Replace current overlap rejection consistently in matcher, preflight and
    trace; add focused tests before claiming the new behavior is available.
- [ ] Implement review/validate/execute parity for supported agent interfaces
  with bounded structured responses and no source-row disclosure; only the
  interactive local CLI may mint preservation approval receipts.
  - [x] Materialize prospective actual common CLI/MCP composition only in an
    isolated source copy; preserve main registration and independent-review gate.
  - [x] Prove installed common profile creation/reopen, CLI schema1.0 and runtime
    flags, controlling-TTY receipt issuance, CLI/MCP retained consumption,
    direct/fallback preservation, safe rejections and full fictional readback.
    Wheel dd6c0c6eb058ef65a6d0a0d33e1b1abba7158da6a648c91a01889ff1f06464a3:
    Python3.14/MCP2 focused18passed; same wheel Python3.11/MCP1 wire3passed.
    Subsequent OAuth-composed wheel9da73de5 explicitly revalidated actual common
    CLI/MCP21passed and unchanged ordinary contract inventory1passed; see progress.
  - [ ] Complete public contract/golden inventories and full candidate gates;
    obtain finished exact-SHA independent review before actual registration.
- [x] Add RC acceptance for skill-guided agents: discover both packaged
  `SKILL.md` files through a documented, runtime-neutral path; choose only
  capabilities present in the installed version; propose a safe workflow and
  use existing reviewed CLI/Python/MCP boundaries. Test fictional offline
  routes and unavailable-transformation rejection. Do not auto-register skills,
  add execution authority or mark this complete from packaging alone.
  Added installed offline guided-caller generation/transformation and actual
  baseline unavailable-command acceptance; see [evidence](skill-workflow-acceptance.md).
  This closes the added local harness/workflow, not final reviewed RC artifacts
  or an external model/integration benchmark.
- [ ] Implement separately authorized read-only SQL-result access; preserve
  SQL allowlists and budgets without broadening default profiling/MCP.
- [ ] Implement consistent key mapping; internal derived-value computation is
  excluded by the latest owner clarification (existing checks below historical).
  - [x] Reject malformed/aggregate derive expressions and dependency disagreement
    through bounded shared parsing before review/save; no evaluation yet.
- [x] Implement scoped typed substitution dictionaries, unmapped-value policy,
  one-pass semantics, collision checks and restricted local mapping handling.
- [x] Supersede the historical source-membership ban with owner ADR-0029:
  actual explicit mappings may permute source values in local output only.
  Identity-pair rules, unmatched-preserve receipts and source-free disclosure
  checks remain; executable mapped-cell coverage and exact-SHA R3 evidence apply.
- [ ] Expose substitution as a specification-level action separate from synthesis;
  test saved wizard-policy parity with noninteractive CLI and Python execution.
- [ ] Expose substitution, mapping references and unmatched-value handling in
  the versioned data behavior profile; test save/load and profile-to-spec
  round trips, conflict rejection and separation from observed evidence.
- [ ] Add a profile-review wizard that saves explicit field decisions; bulk
  acceptance must not bypass unresolved sensitivity conflicts or schema drift.
  - [x] Closed common CSV creation/decision/save/resume scenario: required seed,
    unknown/drop-only initial proposals, per-field action/sensitivity prompts,
    final SAVE and exact revalidation; configuration-only publication never
    copies sources or issues receipts. Installed common suite120passed8.90s;
    public common CLI/MCP registration and final safety gates remain pending.
  - [x] Unified closed CLI creation parser and real-PTY blank-policy wizard:
    explicit field decisions/SAVE, configuration-only save, reopened review,
    validate and retained execute. Installed development wheel6dcf2c0f scenario
    passed; this does not complete public registration or exact-SHA review.
  - [x] Existing valid-policy sensitivity editor: per-column prompts with system
    comments, no default/bulk answer, unchanged actions/mappings, snapshot drift
    rejection and atomic in-place save; no approval or execution.
  - [x] Add explicit selection/configuration of existing field actions, including
    inline/CSV/domain mappings and unmatched behavior; revalidate new references.
  - [x] Complete saved-policy parity with executable paths.
    Installed registered-interface acceptance exercises actual inline/CSV wizard
    saves followed by execution; public route acceptance supplements readback.
- [ ] Add a bounded, value-free system comment for each reviewed field: likely
  data meaning, sensitivity rationale and uncertainty from safe profile
  evidence. Display it with the suggestion and explicit operator decision in
  the wizard and local CLI; never turn default `sensitive=false` into automatic
  preservation. Save and bind the exact reviewed comment/evidence to approval;
  test unknown/conflicting cases, redaction, stale snapshots and save/load
  parity with the noninteractive policy.
- [ ] Validate every final row and declared cross-row relationship before
  atomic publication; reject conflicting policies.
- [x] Implement the owner-confirmed three-origin report (2026-09-28): replacement,
  synthetic, original, based on executed cell actions rather than value equality.
  Verify mapping/generation/preserve fallbacks, explicit formatting, nulls,
  dropped-cell exclusion and empty output; expose counts and proportions without
  values. Equality safety guards remain independent; origin is not anonymity or
  permission to preserve source data.
  Consumed existing `test_transformation_report.py`, executed-action synthesis/
  fallback/null/format/drop tests in `test_transformation_execute.py`, and installed
  manifest acceptance. Report reflects actions, not a claim of anonymity.
- [x] Add an end-to-end fictional finance fixture: preserved product/segment/
  bank combinations, replaced amounts, mapped identifiers and SQL aggregate
  result columns as ordinary inputs, without internal total recomputation.
  `finance-workflow-acceptance.py`: installed candidate1passed1.42s, bounded
  fictional driver stream through real SQL authorization, public CLI review/
  TTY approval/execute, exact decimal readback and missing-receipt rejection.
  No real SQL execution, private derive or final RC artifact claim.
- [ ] Cover nulls, duplicates, zeros, rounding, composite keys, multiple mapping
  domains, deterministic replay and infeasible constraints.
- [ ] Cover schema drift, sensitivity conflicts, leaks through reports/errors,
  provider isolation, budget exhaustion and output rollback.
- [ ] Prove existing aggregate-only/source-free CLI, Python and MCP contracts
  remain unchanged with executable regression tests.
- [ ] Document user workflow, limitations, residual privacy risk and migration.
- [ ] Audit all repository documentation for consistency: README, quickstarts,
  CLI help/reference, Python/MCP contracts, source adapters, configuration,
  privacy/security, architecture, manifests/reports, troubleshooting, examples,
  roadmap, OpenSpec baselines, changelog and release guidance. Update every
  affected page, preserve historical evidence as historical, and explicitly
  distinguish shipped from planned behavior.
- [ ] Execute documented examples on fictional fixtures and validate links,
  documentation tests and strict documentation build before the candidate.
- [ ] Obtain independent security review and complete the required RC/release
  gates before shipping. Do not mark this proposal implemented beforehand.

2026-10-05 current common activation preparation: isolated source copy at
base1d2a9a3 is `/private/tmp/apa-current-common-candidate-sr4ui81v`, pointer
`/private/tmp/apa-current-common-candidate.json`. Zero-context legacy MCP patch
applied cleanly but misplaced its runtime strict_arguments addition after
MCP deadline changes; compile alone did not detect the semantic error.
Replaced proposed MCP patch with contextual factory-call hunks. New executable
`tests/test_activation_patches.py` applies it to current source and verifies
strict_arguments=True at both create_generator_mcp calls;1passed/Ruff pass.
Isolated current startup deadline regressions2passed with disclosed test-factory
adaptation (lambda accepts new registration keyword); separate actual-service
probe confirmed common-tool registration, strict=True and inherited1800s raw
transport deadline. No production guards were patched for acceptance. Actual
branch/main registration remains closed; inventories/full candidate checks and
finished independent source review still required before activation.

2026-10-05 current installed registration candidate acceptance: wheel SHA256
2f1b6cad280c5c160f4114373899e8b00d1a92e5d11c5fdda1e51fa4d03930c8,
base1d2a9a3 plus three proposed registration patches; still version1.5.0.
Creation/runtime/inventory and nonpreserving stdio18passed; four preserving
stdio cases failed in restricted sandbox before local confirmation. Unchanged
wheel retested outside /dev/tty sandbox restriction: all6stdio cases passed,
including direct/fallback preservation confirmations. No receipt/TTY guard
changed. Installed OAuth tests6passed, including piped browser opt-in rejection
before driver/artifact. Logs: isolated candidate acceptance.log and
stdio-escalated.log. These focused results do not authorize activation or
replace final whole-source audit, package/release gates. Private scale queue
still9/12: supplied Trino CSV route running, two subsequent formats pending.

2026-10-05 supplied Trino result → CSV target passed:100M cells,1879.813s,
600,001,000output bytes. Exact wheel/harness/budgets and limitations recorded
in csv-scale-acceptance.md. Private matrix10/12; Parquet running, SQL pending.
No live backend or public scale claim.

Current isolated installed wheel2f1b6cad additionally passed
scripts/accept_transformation_routes.py --public:12 small fictional routes,
actual transform-review/transform-execute CLI and workspace execution,
negative publication checks; no DB. Log: isolated candidate public-routes.log.
This supplements current common-tool acceptance; it does not exercise all
routes through transform-batch or establish public scale/activation clearance.

2026-10-05 target matrix11/12: supplied Trino result → Parquet passed100M
cells,1582.527s,17,493,375bytes; last SQL route running. Exact queue evidence
and limitations in csv-scale-acceptance.md. Current isolated installed
wheel2f1b6cad passed99additional wizard/configuration/receipt/linked-key/budget
boundary tests (88deselected,11.33s); no production guard changes, DB or AI.
Log: /private/tmp/apa-current-common-candidate-sr4ui81v/common-boundaries.log.

2026-10-05 private fictional capacity matrix12/12 complete. Final supplied
Trino result → SQL artifact100M cells passed1533.779s,2,240,002,792bytes;
no SQL execution. Queue terminal status passed/current=null. Exact hashes,
limits and scope in csv-scale-acceptance.md. Capacity parent remains open for
its public-interface and final-candidate acceptance constituents; no copied
clearance from historical audit or private scale runs.

Current installed wheel2f1b6cad:50mode/ratio, exact-decimal dataset/units,
Parquet profile and doctor contract tests passed9.65s, no skips; fictional
fixtures/fake dependencies only. Log: isolated candidate client-contracts.log.
Both OpenSpec changes validated strictly and strict docs built after completed
capacity evidence updates (/private/tmp/apa-final-capacity-doc-build.log).
These scoped results do not close final public-interface/source/release gates.

2026-10-05 current isolated wheel2f1b6cad client compatibility:60auth,
publication/physical-Parquet/golden-CSV/temporal tests passed5.37s;
134SQL source/adapter predicate, aggregate, category-lineage/authorization
checks passed0.36s. No live DB/provider calls. Existing offline MCP2.2.0
installation at /private/tmp/apa-mcp2-tests.OKtla3:7actual common stdio/inventory
checks passed9.66s, including preserving direct/fallback confirmations.
Logs in isolated candidate:remaining-client-contracts.log,sql-contracts.log,
common-mcp2.log. SDK1 and SDK2 evidence are distinct. Current composition
remains prospective, not activated or accepted as the final RC SHA.
