# Tasks: selective-source-transformation

## Current security/configuration checkpoint — 2026-10-06

Complete canonical source audit at composed `6ef55a1`:193 executable files,
zero confirmed findings, no deferred coverage; offline gate3113passed19skipped.
Fresh isolated installed development-wheel acceptance:12 typed routes,
36 CLI refusals and3temporal tests passed on Python3.11; see route evidence.
These are prospective activation checks, not final versionedRC clearance.
All-route1M×100, full client/documentation acceptance and real release gates
remain open. Required CI uses disposable syntheticTrino; explicit clearance
of the no-liveDB restriction is pending before dispatch. No branch PR or
current requiredapproval established. Historical PR602 checks are not approval
of this branch. Final release SHA needs its own checks and independent review.

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
  - [x] Complete the private fictional 12/12 route scale matrix with full readback and cleanup; see sql-scale-acceptance.md and current-candidate-acceptance.md. This closes supplied-fixture scale work only; configured owned transport and the final installed release artifact require their own acceptance.
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
  - [x] Reconcile baseline/docs and fictional accepted/rejected adapter coverage:
    baseline `openspec/specs/sql-query-source-profiling/spec.md` and Trino guide
    define policy1.1; `test_allowed_aggregate_sources`,
    `test_aggregate_expansion_keeps_rejection_boundary`, column authorization
    and AST budget tests are included in exact268efc9a fullgate3158passed.
    Complete whole-source scan e01b29fa covers this composition with no findings.
    Public activation/final versioned SHA acceptance remains open.

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
- [x] Separate shared transformation/validation from CSV-specific parsing and
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
  - [x] Independently review this development/activation clarification.
    Historical clarification reviewed at0e7dee5 in mergedPR576; see progress.md
    and issuecomment5837209533. This does not certify current activation SHA.
- [ ] Finalize versioned field policy, CLI/API and mixed-origin artifact schema.
- [x] Specify exact decimals, precision/scale/rounding/overflow, approximate
  DOUBLE conversion and CSV round trips; preserve existing schema compatibility.
- [x] Define fixed-snapshot/replay semantics, mapping domains and state cleanup.
- [x] Define financial tolerances, impossible-replacement behavior and safe
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
- [x] Reproduce/fix 22: allowed AND/OR/nested predicates on both SQL adapters;
  retain forbidden-function, authorization and budget negative controls.
- [x] Reproduce/fix 25: all generation entrances honor documented explicit/omitted
  mode and ratio precedence; effective spec/manifest/report/exit reflect execution.
- [x] Reproduce/fix 20: doctor retains failed checks, distinguishes missing extras
  from capability failures and gives safe recovery hints without backend text.
- [ ] Consolidate 21's October 2 approved six-method auth/secret-indirection
  implementation, local CLI opt-in and installed evidence into the final candidate;
  complete exact-SHA safety review before public activation. No live access.
  - [x] Renew local installed auth/OAuth constituents on exact268efc9a:
    auth plus decimal-profile24passed; OAuth6passed including verified installed
    subprocess pipe refusal. Six-method configuration and how-to reconciled.
    Complete scan e01b29fa covers composition; remote auth and final versioned
    activation remain unverified, not inferred from these local checks.
- [x] Integrate 23 into exact-decimal contract and carry precision/scale through
  agreed profile/spec/generation/transformation/exports without float
  intermediates; internal formulas are excluded by the owner scope correction.
- [x] Consolidate 24's declared Parquet physical/readback evidence with 25's
  October 2 invalid-result/exit decision; retain fail-closed incompatible typed output.
- [ ] Consolidate 26's October 2 approved unknown-metadata and bounded-sensitivity
  implementation/evidence; finish final-candidate CLI/API compatibility gates.
  - [x] Renew installed unknown-metadata and bounded-sensitivity constituent:
    exact268efc9a/wheel430e0405, source-adapter Parquet selection11passed0.27s;
    Python3.11 candidate-only imports. Profiling guide reconciled; see current
    candidate acceptance. Final versioned interfaces remain open.
- [x] Reconcile refreshed 1–19 evidence: missing date bounds, SQL diagnostics and
  scan costs, formula dependencies, publication/overwrite and utility boundaries.
  Evidence: client-acceptance.md per-finding disposition register and dated
  corrected/current installed bindings. Monthly fidelity deferred; internal
  formulas excluded by owner; statistical utility/live costs/private inputs
  unverified. Closure is reconciliation, not blanket client or RC acceptance.
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
- [x] Implement consistent key mapping; internal derived-value computation is
  excluded by the latest owner clarification (existing checks below historical).
  - [x] Reject malformed/aggregate derive expressions and dependency disagreement
    through bounded shared parsing before review/save; no evaluation yet.
- [x] Implement scoped typed substitution dictionaries, unmapped-value policy,
  one-pass semantics, collision checks and restricted local mapping handling.
- [x] Supersede the historical source-membership ban with owner ADR-0029:
  actual explicit mappings may permute source values in local output only.
  Identity-pair rules, unmatched-preserve receipts and source-free disclosure
  checks remain; executable mapped-cell coverage and exact-SHA R3 evidence apply.
- [x] Expose substitution as a specification-level action separate from synthesis;
  test saved wizard-policy parity with noninteractive CLI and Python execution.
- [x] Expose substitution, mapping references and unmatched-value handling in
  the versioned data behavior profile; test save/load and profile-to-spec
  round trips, conflict rejection and separation from observed evidence.
- [x] Add a profile-review wizard that saves explicit field decisions; bulk
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
- [x] Add a bounded, value-free system comment for each reviewed field: likely
  data meaning, sensitivity rationale and uncertainty from safe profile
  evidence. Display it with the suggestion and explicit operator decision in
  the wizard and local CLI; never turn default `sensitive=false` into automatic
  preservation. Save and bind the exact reviewed comment/evidence to approval;
  test unknown/conflicting cases, redaction, stale snapshots and save/load
  parity with the noninteractive policy.
- [x] Validate every final row and declared cross-row relationship before
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
- [x] Cover nulls, duplicates, zeros, rounding, composite keys, multiple mapping
  domains, deterministic replay and infeasible constraints.
- [x] Cover schema drift, sensitivity conflicts, leaks through reports/errors,
  provider isolation, budget exhaustion and output rollback.
- [x] Prove existing aggregate-only/source-free CLI, Python and MCP contracts
  remain unchanged with executable regression tests.
  Current exact268efc9a fullgate3158passed includes CLI parser/contracts, direct
  privacy and MCP service/transport regressions; installed registered-interface
  inventory7passed verifies explicit prospective common addition. See
  [current candidate acceptance](current-candidate-acceptance.md). This closes
  this compatibility constituent, not versioned/public release gates.
- [x] Document user workflow, limitations, residual privacy risk and migration.
  2026-10-07 reviewed docs/reference/cli.md common-profile workflow and
  docs/concepts/safety-model.md: exact saved-byte review, fresh digest after
  edits, separate local preservation receipt, agent consumption only, gated
  registration, mixed-origin privacy limits and migration from shipped1.5.0.
  Strict documentation build already passed after these documentation changes.
  Whole-repository consistency and final release acceptance remain separate.
- [ ] Audit all repository documentation for consistency: README, quickstarts,
  CLI help/reference, Python/MCP contracts, source adapters, configuration,
  privacy/security, architecture, manifests/reports, troubleshooting, examples,
  roadmap, OpenSpec baselines, changelog and release guidance. Update every
  affected page, preserve historical evidence as historical, and explicitly
  distinguish shipped from planned behavior.
  2026-10-07 consistency constituent: reviewed roadmap and compatibility
  inventory, plus transformation-boundary sections in output review, application
  boundaries, MCP design and MCP how-to. They distinguish ordinary synthetic
  manifests from gated mixed-origin output, local receipt issuance from MCP
  consumption, and historical review from final activation clearance. No
  contradictory activation claim found in these sections; whole-doc audit
  and executable-example acceptance remain open.
- [ ] Execute documented examples on fictional fixtures and validate links,
  documentation tests and strict documentation build before the candidate.
  2026-10-07 reconciled existing exact268efc9a full-gate log: all five
  tests/test_live_examples.py cases and44 documentation tests passed. Reviewed
  CSV, relational CSV, output-format shell launchers, Python API script and
  their README workflows against those assertions; SQL is generated, not
  executed. Reused completed evidence without rerunning unchanged tests.
  Installed final-version examples and remaining documentation audit stay open.
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

2026-10-05 prospective registration full offline gate started in isolated
candidate sr4ui81v, base1d2a9a3 plus three registration patches. Fourteen
public contract fixtures regenerated only there; existing disclosed factory
fixture adaptation retained. Active branch/main untouched. Lint/types/compile,
dependency checks and preliminary privacy/SQL tests pass; full3075-test suite
running, both DB integration flags0. Session10127; candidate-state.json and
full-gate.log in isolated root retain progress. Do not duplicate this run or
claim final exact-SHA clearance; inspect terminal result first next heartbeat.

2026-10-05 prospective full gate completed with2stale contract failures,
3050passed23skipped90.50%coverage180.38s. Failures: expected MCP inventory
omitted common_transformation; application-boundary docs omitted prospective
names. Corrected only isolated expected test/docs/fixtures;53focused tests
pass. Operational budgets, schema freshness, quickstart and strict docs pass.
Tail-run first failed due to missing original physical tmp-path normalization;
restored original pwd -P, path guard unchanged, rerun passed. Product unchanged.
Proposed registration-contract-activation.patch retains these fixture/docs/test
changes for coherent future activation; active branch inventory remains closed.
Logs: focused-contract-repair.log,remaining-gate.log,schema-quickstart-gate.log
under sr4ui81v. This is reconciled prospective gate evidence, not a green
single final-SHA gate or independent safety clearance.

2026-10-05 coherence preparation: refreshed CLI/OAuth proposal patches with
context, avoiding --unidiff-zero. Four proposals apply sequentially with
standard git apply to current9e7d8cb archive; coherent copy at
/private/tmp/apa-coherent-registration-hjd3v1ez, pointer
/private/tmp/apa-coherent-registration-current.json. Contract/docs53tests pass
from candidate root. Initial invocation from active worktree read its relative
fixtures and failed2checks; corrected cwd, no guard changes. Proposed public
registration remains inactive. Next: freeze complete prospective source identity
and obtain independent full-source review before activation; final RC gates stay
open. Existing prospective gate evidence is retained without repeated scale runs.

2026-10-05 post-fix coherent test preparation: patch regression now roundtrips
already composed or closed MCP source, retaining assertions at both real
strict factory calls. Startup deadline fake factory explicitly accepts the
new strict_arguments keyword.37closed-baseline patch/server tests and Ruff pass.
No product guard or public registration changed. Next candidate includes all
R7/R8/R9 fixes and four registration/contract proposals before final checks.


2026-10-06 prospective common registration source audit complete at exact
6ef55a1d86e377ee442199fee60cec6b57c8b9a7: independent whole executable
baseline193files, canonicalcoverage complete, deferred0, confirmedfindings0;
scan54cfdefc-304e-4131-a379-396572e8d4c5. Full synthetic offlinegate
3113passed19skipped90.54%. Canonical report reference retained in
remediate-full-security-audit/tasks.md. This completes source security evidence
for the four composed activation proposals only; installed client acceptance,
documentation reconciliation, final versioned identity and real release gates
remain distinct. Future batch validation is tracked in roadmap, outside RC scope.

2026-10-06 remaining-client reconciliation:20 and25 reproduction/fix tasks
closed from existing explicitly installed doctor/mode evidence in client-acceptance.md,
plus current author-source full gate3122passed23skipped at04704cd. No unchanged
tests rerun or historical artifact relabeled finalRC. Doctor dependency/capability
injections remain disclosed; real remote failures unverified. Final activated
package/extras matrices and21/23/24/26 consolidation gates stay open.
Current author-source clean scan67934951-4755-41b7-aa9b-26925754ed17 at04704cd
is separate from older prospective runtime6ef55a1; it does not certify activation
patches or a future versioned candidate. Next create coherent current prospective
activation package, consume only affected acceptance, then final release identity.

2026-10-06 activation patch reconciliation: removed the obsolete invalid_ratio
0→0.0 fixture hunk, already present after R15 contract refresh. Added archive-based
regression applying all four activation patches to current source; 2 tests pass.
Runtime activation, installed acceptance and final RC gates remain pending.

2026-10-06 post-seed prospective activation: four patches compose over f48677f;
source checks52passed/1skipped and isolated offline development-wheel checks
52passed. Exact wheel hash and limits retained in client-acceptance.md.
Final activation/source identity, remaining client gates and RC release gates open.

2026-10-06 same post-seed development wheel: installed typed/publication/policy
suite56passed4.44s; public twelve-route synthetic acceptance passed with exact
readback and36CLIrefusals. See client-acceptance.md; final candidate gates open.

2026-10-06 installed activation safeguards: 507 tests passed26.82s for snapshot,
decisions, report, execution, total limits, mappings, approval and source adapters
on the post-seed development wheel. System-comment task reconciled with bounded
allowlisted comments, explicit wizard decisions and approval snapshot binding
(test_transformation_approval.py::test_review_comment_and_profile_evidence_are_snapshot_bound;
policy redaction cases and current full author-source gate). This closes the
comment implementation requirement, not activation or final RC certification.

2026-10-06 remaining intake reconciliation:22 reproduction/fix closed using
existing both-adapter boolean-predicate/forbidden-function regressions consumed
by the clean04704cd full gate (no unchanged rerun).23 integration and24 physical/
readback+mode consolidation closed by the same installed post-seed wheel's
56 typed/policy tests,52 mode/boundary/SDK tests and12 public typed routes.
This is executable implementation/intake evidence, not final RC acceptance.
21/26 retain their explicit final-source safety/compatibility requirements.

2026-10-06 retained target queue reconciled: all five completed; historical
private fictional1M×100matrix12/12. Trino CSV1879.813s,Parquet1582.527s,
SQL1533.779s; full readback/provenance/digest/cleanup. See hashed logs/state
in sql-scale-acceptance.md. No repeat or new/runtime/publicRC claim; parent
public/final-source capacity gates stay open.

2026-10-06 installed batch/actual common acceptance recorded in client-acceptance.md:
176passed4skipped7TTYfailures; actualcommon18passed4TTYfailures; authorized
TTY/stdio-onlyrerun12passed resolves all failures without code adaptation.
Finalsource/releasecertification remains pending.

2026-10-06 supported key/final-row/edge-case requirements reconciled: shared
domain scalar/composite keys and full final schema/constraint/relationship
validation precede publication independently of optional validation flags;
installed batch results and507 execution/mapping/approval checks retained above.
Installed registered interfaces+linked domains+fictional finance9passed10.97s,
1 historical inventory assertion deliberately deselected (current golden
contracts checked separately). RealTTY allowed; no guard patches/liveDB/AI.
This closes supported implementation coverage, excludes internal formulas per
owner, and leaves final contracts/docs/activation/capacity/RC gates open.

2026-10-06 policy/profile/wizard implementation reconciled: BehaviorPolicy0.1
separates substitute from synthesize; saved BatchProfile0.1 retains explicit
policy/mapping/generation references and validation spec, without changing
observed evidence. Installed batch suite consumes save/load/conflict, decision
wizard, blank-policy SAVE/reopen and execution parity; actual common creation
checks and9 registered/linked/finance cases supplement it. Unknown/sensitive
fields require explicit decisions; receipts and drift guards stay independent.
These implementation tasks close; common public activation/final contracts
and exact-source review remain their own open gates.

2026-10-06 specification/architecture reconciliation: current policy-contract
checkpoint separates input/shared validation/output using transformation_input,
transformation_execute/batch and transformation_output/parquet; CSV-named
private helpers stay internal. Declared DECIMAL/DOUBLE, snapshot/domain/cleanup
and infeasible replacement semantics specified and exercised by installed
typed/batch/publication evidence above. Internal financial formulas excluded
by ADR0026, no new tolerance requirement. Final public schema/activation/docs
and exactRC review remain open.

2026-10-06 safeguard coverage reconciliation: current author-source full gate
plus clean whole-source audit at04704cd, post-seed installed507safeguards,
batch and9registered cases cover schema/snapshot drift, sensitivity, disclosure,
provider isolation, budgets and atomic rollback for supported operations.
Generic arbitrary crash/race recovery remains unclaimed. HistoricalPR576
clarification review reconciled separately; parent complete-current-source
safety amendment and prospective common activation remain open.

2026-10-06 prospective common full gate at f13989c9660c62fe503387623738de2b5868b15c:
3126passed19skipped1warning90.54%,181.32s;1test failed because new patch
composition regression reapplied patches to an already composed archive.
No runtime failure. Fixed regression to reverse composed proposals first,
then reapply all four;2tests pass on closed source and2 on composed source,
Ruff pass. Full gate incomplete until corrected candidate checks complete;
no audit/version/publication clearance from this failed run.

2026-10-07 configured PostgreSQL driver increment: fixed trusted psycopg factory
resolves only inside the existing isolated capture worker. No caller-selectable
module/factory or environment-driven connection discovery; public wiring remains
closed. Invalid capture regression proves driver resolution never starts.
Synthetic isolation suite29passed28.03s; Ruff passed without cache. No live DB.
Runtime changed after268efc9a: its prior audit/gates do not certify this new SHA.

2026-10-07 closed PostgreSQL metadata increment reuses bounded read-only
PostgresClient and existing allowlisted column discovery. Source-id/adapter/table
refuse before connect; authorized no-row schema must match output aliases.
Synthetic success, schema drift and three pre-connect refusal regressions:
5passed0.27s; Ruff passed. No live DB/public registration; metadata-to-Arrow
conversion and owned-worker composition remain next, not complete SQL activation.

2026-10-07 PostgreSQL native capture-schema increment: explicit scalar types,
exact numeric/decimal(p,s) only at precision<=38, preserved widths/nullability;
unbounded numeric, unsupported arrays/JSON and timestamps reject without coercion.
8focused synthetic tests passed0.26s; Ruff passed. Closed helper only; real
no-row descriptions must retain numeric precision/scale before composition.
Timestamp support and worker-owned metadata/capture composition remain open;
no new public capability or final SHA acceptance claimed.

2026-10-07 PostgreSQL no-row descriptions now retain validated driver numeric
precision/scale, enabling exact capture-schema conversion without guessed bounds.
Absent shape stays numeric; malformed/incompatible declared shape rejects.
Client/query-source suites164passed0.78s; Ruff passed. Guide updated. Native
psycopg column precision/scale properties verified in installed SDK source.
Public SQL capture/owned discovery composition and final exact-SHA gates open.

2026-10-07 configured PostgreSQL worker now owns metadata discovery, exact schema
conversion and result capture under one supervisor deadline. Configured entry
ignores caller metadata; discovery reserves one statement for capture and freezes
resolved columns through existing validation. Synthetic composed capture and
isolation/query suites81passed28.72s; final one-read cleanup regression1passed.
Initial composition failed on init=False resolved_columns; repaired using the
existing validated constructor. No live DB, public registration or RC clearance.

2026-10-07 owned metadata lifecycle acceptance: blocked metadata FETCH and
schema drift both fail without a snapshot and leave no test-owned child;
normal composed capture still passes.3focused tests passed2.45s; Ruff passed.
No DB/provider calls or repeated scale tests. Public wiring remains open.

2026-10-07 owned metadata now returns its validated query identity; capture
requires that same fingerprint before opening the result stream. A changed
query file with the same output names rejects before result access.16focused
metadata/worker/query-binding tests passed2.55s; no live DB. Public activation
and final exact-SHA audit/gates remain open.

2026-10-07 configured-entry regression verifies supplied source/output metadata
is discarded before supervisor dispatch while explicit request/config/policy
remain bound; driver factory cannot be selected by caller.1passed0.30s/Ruff.
No live driver call. Temporal native input support and Trino-owned capture are
still missing constituents; no final public SQL acceptance claimed.

2026-10-07 closed native UTC timestamp substitution now preserves microseconds
through typed query capture, source profile, exact mappings and CSV readback.
PostgreSQL aware native datetime accepts only UTC microsecond Arrow schema;
naive/no-zone metadata and other timestamp encodings remain rejected. Native
preservation remains blocked; no timezone guessing or new public registration.
Reuse comparison recognizes equivalent aware instants, rejects naive matching.
SQL capture/isolation86passed30.87s; final timestamp2passed0.27s/Ruff.
Initial end-to-end test exposed missing DATETIME mapping allowlist; repaired in
shared execution before accepting the result. Trino capture/public wiring open.

2026-10-07 Trino client now exposes an internal owned row iterator under the
same authentication, concurrency, time/scan/result budgets and cleanup. Existing
list-returning methods consume it unchanged; early exit closes the iterator,
cursor and connection, preventing post-context reads. Oversized driver batches
reject.21synthetic client tests passed/Ruff. No new caller SQL surface or live DB;
typed Trino capture composition/public registration remain next.

2026-10-07 closed Trino typed-stream increment uses shared bounded client and
shared strict PostgreSQL/Trino native-cell validation. Exact catalog/schema/
column scope and source identity check before connect; no wildcard inference or
result-row cap increase. Streaming chunks preserve schema/nullability and reject
coercion/drift; existing query time/scan/result work and cleanup remain active.
66synthetic query-capture/client tests passed0.89s; no live DB. Trino-owned
metadata/supervisor and public CLI/MCP composition remain unfinished.

2026-10-07 closed Trino metadata discovery now reuses allowlisted schema query,
shared statement/scan/result/deadline budget and trusted WHERE FALSE inspection.
Source/catalog/schema refuse before connect; output alias drift and unexpected
rows reject. Returned metadata is typed and bound to authorized query identity.
4synthetic tests passed0.58s/Ruff. No DB. Owned supervisor/continuous capture
budget and public registration still unfinished; not final SQL activation.

2026-10-07 closed Trino capture schema retains signed integer widths and exact
decimal128 precision/scale from owned no-row metadata. Unsupported composite,
binary, bounded-character and temporal declarations fail closed without driver
text; no guessed precision or timestamp truncation. Synthetic capture suite:
56 passed0.82s; Ruff passed. Log/private/tmp/apa-trino-schema.log. Owned Trino
supervision, continuous discovery/capture budget and public registration remain
open; this private mapper does not close the composite SQL activation gate.

2026-10-07 closed Trino composition now discovers metadata, freezes wildcard
authorization into explicit columns, builds native schema, binds capture to the
discovered query fingerprint, and consumes one invocation budget throughout.
Synthetic cumulative statement regression: three statements succeed; allowance
of two refuses capture rather than resetting after metadata. Shared capture and
Trino client suites79 passed0.61s/Ruff. Log/private/tmp/apa-trino-composed.log.
This cooperative driver composition still needs process-owned supervision and
public CLI/MCP registration; no live database, release gate or final audit claim.

2026-10-07 Trino metadata and typed capture now execute in an owned spawn
worker through the same extracted SQL process supervisor as PostgreSQL. Parent
accepts bounded IPC only after clean child exit; blocked metadata/row reads are
terminated and reaped; partial output and backend exception text cannot cross.
Configured entry imports the fixed optional Trino driver in the child, never
a user-selected factory. Synthetic Trino lifecycle + PostgreSQL lifecycle +
shared query suites108 passed35.98s; Ruff/diff checks passed. Evidence:
/private/tmp/apa-sql-owned-isolation.log. OS scheduling/reaping, worker RSS and
wire bytes retain documented limits; public CLI/MCP activation still open.

2026-10-07 owned Trino capture now has complete synthetic small-fixture
capture->profile->review->temporary publication readback for CSV, Parquet and
SQL artifacts. Explicit substitutions produce the exact expected two rows in
all formats; SQL is never executed; temporary roots are removed. Lifecycle +
three output regressions7 passed7.31s/Ruff. Log:
/private/tmp/apa-trino-owned-output.log. This closes the private owned-driver
output-path evidence increment only: public registration, full final-SHA gate
and independent audit remain open; no new large-scale replay or live DB.

2026-10-07 parallel focused source review of owned SQL at26180e7 found no
confirmed security finding; not a full final-SHA audit. Activation limitations:
Trino cumulative database-result budget stays4MiB, Trino timestamps unsupported,
and work-budget refusals currently become generic capture errors. Frozen1M
fixture evidence does not certify configured owned1M transport. Documentation
now distinguishes frozen268efc9a from current runtime; strict docs passed0.40s.
Root corrected four strict-type errors in streaming iterator/optional allowlists;
full mypy148modules passed,79focused regressions passed0.83s/Ruff. Public
registration and final release gates remain open. Parallel common SQL integration
is in progress and not included in these checks.

2026-10-07 owned Trino preserves typed QueryWorkBudgetExceeded through shared
capture and bounded fixed-field IPC, without serializing backend messages.
Synthetic refusal asserts cumulative statements3>2 and child reaping; isolation
and capture suites66 passed8.11s/Ruff. Log/private/tmp/apa-trino-typed-refusal.log.
Parallel integration still under development; full type gate pending its config
union fixes. SECURITY scoped mapping amendment matches owner ADR0029; strict
docs passed0.40s. Activation wording/actual registration reconciliation and
final exact-SHA safety evidence still required; no composite task closed.

2026-10-07 parallel SQL/common integration completed: trusted configured PG
and Trino capture bindings produce frozen envelopes in the owned temporary
common-profile workspace; existing candidate CLI/MCP review/validate consumers
read them without reconnecting. Frozen policy bytes are rechecked; cumulative
policy reads are bounded before allocation; shared total and every binding's
scalar/configuration limits preflight before any capture. Reviewer-found late
shared authorization P2 corrected and independently rechecked with no further
confirmed finding. SQL/scope authorization remains per adapter, not an all-input
no-connect guarantee.12focused tests passed0.67s,full mypy149modules/Ruff passed;
earlier combined241passed10skipped. Logs/private/tmp/apa-common-query-integrated.log
and/private/tmp/apa-common-query-final-mypy.log. Public registration/activation
and full final-SHA gates still open; no live DB or new scale run.

2026-10-07 actual CLI/MCP registration reviewed: existing single-source local
CLI and execute_transformation consumer are registered on author branch; common
saved profiles/configured SQL remain private. AGENTS/compatibility wording now
matches this scope rather than declaring all execution inactive. Strict docs
passed0.40s. Full current runtime gate started at7ad4da0, synthetic/offline only:
/private/tmp/apa-owned-sql-release-gate.log,session70761. No pass yet; subsequent
activation/final release identity still require their exact-source checks.

2026-10-07 prospective4patch composition fromexact7ad4da0 passed195unique
contract/common tests incl14goldens and controlling-TTY receipts. Sandbox-only
TTY refusals reran with terminal access. Compositiondigest
4b0a65ffb6f53fe4d7ba9b5e1c93b40f3afbff10cc7b56a27feadfa30ae6af2d;
/private/tmp/apa-current-activation-pointer.json. Authorregistrationuntouched.
Currentauthor fullgate firstfailed15doctor tests/3202pass23skip because root
strippedHomebrewPATH and psycopg could not import libpq; normalPATH import3.3.4
confirmed. Retry preservesPATH, session45225/log
/private/tmp/apa-owned-sql-release-gate-retry.log. Isolatedcomposition fullgate
nowdispatched separately; nofinalpass/audit/activationclaim.

2026-10-07 current author runtime release gate retryPASSED exit0:
3217passed23skipped/90.54%coverage199.19s; lint/fulltypes/compile/licenses/
compatibility/directprivacy/resource/schema/quickstart complete. Log
/private/tmp/apa-owned-sql-release-gate-retry.log. BothDB integrationsdisabled
locally; requiredsyntheticTrinoCI remainsfuturegate. No more unchangedruntime
replayneeded. Acceptance reconciliation: historicalscale/auth/metadata/harness
constituents have proof; remaining concrete runtimeblocker is publicconfigured
SQL references/capture contract, not anotherprivatehelper. Fourprospective
patches exposecommonconsumer only. Finalactivation,installedversionedartifact,
exactSHAaudit and requiredapproval remainopen.

2026-10-07 isolatedfullcomposition:3216passed23skipped90.53%/206.26s,one
harnessfailure because gitarchiveHEAD requiresGit metadata absent infrozen
copy. Existingreverse-patchlogicalreadyhandledappliedpatches; no runtimefailure
confirmed. Testnowcopiesonlyexactpatchtargets toownedtmp, preserving closed/
composedchecks; closed2tests passed/Ruff. Onlyfailedtest and unrunposttestgate
steps willrerun, not3216unchangedchecks. Finalcompositionidentity mustrecord
this test-only change beforeaudit; nofullgatepassclaimyet.

2026-10-07 resumed after interruption: isolated composition missing Git harness
repaired test passes2cases; operational/schema steps already passed. Initial
posttest smoke rejected /var symlink output. Only smoke rerun with resolved
/private temporary path passes exact flags/seed/rowcounts/validation and
dependency-manifest compatibility; output removed. Logs
/private/tmp/apa-current-activation-harness-retry.log and
/private/tmp/apa-current-activation-quickstart-retry.log. Runtime tests remain
3216pass23skip90.53%; no unchangedsuite replay. This closes split local gate
for frozen prospective composition plus recorded test-only repair, not final
versionedRC/sourceaudit. Public SQL reference integration resumed in parallel.

2026-10-07 configured SQL references prepared using existing administrator
environment config only; bounded workspace query snapshots feed one owned
common session. Closed CLI review is explicitly one-shot/expired on return;
MCP parent workspace resolves before capture.20synthetic tests passed0.84s,
fullmypy149modules passed/Ruff; focusedcontractreview no confirmedvulnerability.
Logs/private/tmp/apa-configured-query-preparation{,-mypy}.log. This is NOTfull
publicSQLlifecycle: selected parent output and localTTY receipt must remain
in the same owned capture session. Nextincrement implements one-invocation
CLI using existing receipt/publisher, without recapture or a new registry.

2026-10-08 closed CLI query-execute now parses bounded savedreferences and
completes one capture/review/localTTY receipt-if-preserving/validatedretained
publication innewparentdestination; rawsnapshots expirefinally. Actualargv
CSV/Parquet/SQL, receiptaccept/refuse and destinationrace regressions passed.
Trino capturecapacity now explicitlyscoped policy/sessionchecked rows+overflow
sentinel anddecodedDBbytes; metadataoriginalrowcap/profiledefaults/scan/time/
statement/transportlimits retained. Combined99passed1.46s/fullmypy149/Ruff,
independentreviewer21passed0.84s/noconfirmedscopedfinding; strictdocs0.40s.
Logs/private/tmp/apa-configured-sql-complete{,-mypy}.log. No1Mreplayneeded.
Publicregistration and MCPcross-requestreceipt/outputbridge remainopen; final
wholeSHAaudit cannotreuse these scopedreviews.
