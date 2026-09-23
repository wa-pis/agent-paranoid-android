# Implementation Progress

## Authority And Target

- User authorized implementation, signed commits/push, sequential PR merges
  after CI/CD and independent review, and 1.6.0rc1 publication. No stable release.
- GitHub CLI checked: authenticated; repository ADMIN access. Homebrew git
  required because system git invokes unaccepted Xcode license.
- Branch: codex/1-6-policy-models, based on main 0c87702.
- Heartbeat automation active every five minutes; no duplicate/overlapping work.
- Use Caveman and Ponytail. Read this file first; do not rerun unchanged gates.

## Current Slice: Client Finding 19

- Added deterministic directory access-time regression tests. Baseline: 2 fail,
  9 pass. Shared publish_directory/replace_path compared complete stat objects.
- Fix compares directory identity; regular files retain identity, ctime_ns and
  size checks. Absent/present transitions remain checked. No overwrite expansion.
- Focused tests: 90 passed across path policy, I/O workflows/commands, workspace.
- Ruff passed; full production mypy passed (109 files).
- Path-swap tests cover source/destination directory and symlink replacements.
- Signed commits ed4a672 (plan) and 2569c3a (fix) pushed; PR #516 opened:
  https://github.com/wa-pis/agent-paranoid-android/pull/516
- PR #516 merged as 4d6310ad3ccae5abad8dec39e59dc2b17e52791d after green
  CI, Security, Containers, Documentation and independent AI review.
- Documentation inventory initially rejected the new active proposal; updated
  its explicit inventory and checks for the unfinished transformation plan.
- Documentation tests: 49 passed; Ruff and strict OpenSpec validation passed.
- 2026-09-24 heartbeat: current PR head c3f1308; documentation CI passed.
  CI/Security/Containers queued behind earlier runs; do not restart or push
  progress-only commits while those checks are pending.
- User explicitly authorized separate AI-reviewer subagents for PRs and final
  RC/release SHA reviews; automation updated. Stable remains unauthorized.
- Independent read-only reviewer Nietzsche (01a0cff7-6e28-7c72-8bb0-4a54f99bebfe)
  completed PR #516 exact c3f130896c0485b95c792dc8936affa5d0836d8e against
  d89dc4dd573c4e764cddd8eb1e053eb78aa42acb: no blocking findings; 71 checks
  passed. AI review, not human approval. Evidence:
  https://github.com/wa-pis/agent-paranoid-android/pull/516#issuecomment-5802473268
- Next defect confirmed on unpatched generator with fictional data: two distinct
  identifier fields produce equal row-wise values for both integer and string
  types (three rows, seed 7). synthetic_identifier ignores field identity;
  integer identifiers also ignore entity identity. No generator change yet.
- Repro explicitly uses PYTHONPATH=src (entity items). An initial standalone
  probe resolved the installed package instead and failed privacy validation
  for the longer fictional_items entity name; that run is not candidate proof.
  Pytest already sets pythonpath=[src, .], so prior pytest results are unaffected.

## Remaining Decisions And Work

### Local Publication Replay (2026-09-24)

- PR #516 c3f1308: CI Python 3.11–3.14, wheel checks, Security and container
  validation passed; independent review still pending. No merge performed.
- Built candidate wheel from c3f1308 using uv build --wheel --no-build-isolation;
  version intentionally remains 1.5.0 until release preparation. Installed with
  --no-deps into /private/tmp/apa-client-acceptance.xrueHB/candidate, reusing the
  development interpreter dependencies. This is not a clean dependency acceptance.
- Verified import resolves to that installed candidate path via PYTHONPATH.
- Reviewed original probe_output_contract.py before extracting it into isolated
  replay/baseline-replay directories below the same temporary root. No product
  monkeypatches. Replaced missing spec with identical fictional deal/id/amount
  fixtures, ten rows. Original script itself unchanged.
- Original probe: installed comparison package and candidate each ran 40 fresh CLI
  processes. Both: absent/empty/empty-overwrite 8 successes each; filled and
  filled-overwrite 8 exit-2 rejections each. Timing-dependent defect did not
  reproduce in this nondeterministic replay; deterministic unit regression is
  the before/after evidence, not these identical original-probe results.
- Metadata verification found the pre-existing installed package is 1.4.0,
  NOT 1.5.0. The script's hard-coded 1.5.0 banner is misleading. Therefore the
  comparison run is diagnostic only; required affected-baseline 1.5.0 replay
  remains pending in a separately installed target. Do not call it accepted.
- Candidate wheel SHA256: 77a15df3854f2f18b1917f21169fd8d65d10ad34037774754513cf849b1f96a3.
  Original probe SHA256: 33dafc8ac55f4e0cb230e399aa206da2bc2fd2fbe2c22270cb37171208399f71.
- Supplementary candidate checks explicitly asserted exit code, CSV shape and
  ten rows for successes; rejections preserve old.csv and create no deal.csv.
  All five cases passed, subprocess timeout 30 seconds. The original probe's
  artifact-only success accounting remains insufficient on its own.
- No private client data tested. Full installed-candidate acceptance pending.

- Transformation runtime not implemented. Safety-policy exception must be scoped
  explicitly and independently reviewed with tests; existing generation stays
  source-free. Do not silently allow sensitive preservation.
- Client script replay and all other findings: see client-acceptance.md; not
  yet completed. Missing private inputs are unverified, never passed.
- Profile/inline YAML/CSV mapping, wizard, agent parity, Decimal and source
  adapters remain pending. Latest voice decisions recorded in plan/tasks/design.
- Shared mapping required within a linked dataset; independent runs may differ.
  Explicit shared mapping across separate runs is opt-in, not a universal mandate.
- External script/API substitution is unapproved future TODO. Future integration
  feedback has not arrived; do not invent it.
- Finish full documentation reconciliation and installed candidate/client tests,
  independent exact-SHA review, release gates and public acceptance before closing.

## Next Action

Identifier-domain fix signed and pushed as 74e8671ec123c6bc92e94564e12cd88828268cb4:
PR https://github.com/wa-pis/agent-paranoid-android/pull/517.
Sorted entity/field domains,
disjoint integer residue classes, synthetic-prefixed string encoding. No new
dependency or privacy bypass. Two baseline regression failures reproduced;
127 focused tests now pass (domains, generation contracts, pipeline, dataset
spec, safety), including negative/zero/positive seeds, reordered fields/entities
and declared FKs. Mypy passed for the changed generator. Changelog and relational
contract document fixture compatibility and lack of cross-spec mapping stability.

Documentation checks: 49 passed; focused Ruff passed. Independent AI reviewer
Ohm (01a0d003-3a99-7522-bfb1-09dec23d3067) reviewed exact 74e8671 against
4d6310a and found P1 reversed FK-chain regression plus P2 nullable reorder
documentation mismatch. Merge blocked. Added regressions (two failed before fix),
ordered relationship writes by exact parent-field dependencies using stdlib
TopologicalSorter, narrowed nullable replay wording. Focused 81 tests, Ruff and
mypy passed before adding a cycle/rejected-edge regression. Re-review required
on amended head. Signed a2868b4 pushed; Ohm re-review requested, do not duplicate.
Final domain/documentation tests: 59 passed (includes cycle/rejected-edge case).
CI on a2868b4 failed doctor and wheel smokes: existing inferred cyclic graphs
were incorrectly rejected. Local follow-up restores legacy input-order handling
for cyclic graphs with unchanged final validation; acyclic chains remain ordered.
Do not merge a2868b4. Reviewer notified; updated-SHA review needed after fix.
Public baseline 1.5.0 installed successfully in temporary baseline-1.5.0 target;
actual script replay against that target remains pending.
Follow-up ad81e3a signed/pushed: 98 domain/CLI/solver tests passed, Ruff clean.
Ohm requested to review newest head (same reviewer, no duplicate agent).
Ohm blocked ad81e3a despite green CI: unrelated cycles disabled chain ordering;
nullable-FK final values also excluded from reorder guarantees. Reproduced the
mixed graph failure. Follow-up collapses cyclic components only, topologically
orders component dependencies, retains legacy order inside components. Docs now
limit identifier stability to initial generation before relationship assignment.
Signed 3add995 pushed; 139 focused tests, mypy and Ruff passed. Ohm re-review
requested on this head; do not duplicate or merge before disposition and CI.
Public 1.5.0 baseline replay completed with verified import/version: 40 cases,
same outcome as candidate publication replay (24 successes; 16 intended nonempty
directory rejections). No timing failure reproduced; deterministic atime tests
remain regression evidence. Private inputs and full clean acceptance still pending.
PR #517 merged as 40fd4d0c252bfafa397538a85b71b3605c1adbd9 after all CI passed
on 3add995 and Ohm independent AI re-review found no outstanding issues.
Review evidence: https://github.com/wa-pis/agent-paranoid-android/pull/517#issuecomment-5802899834
Independent checks: 269 tests, 1,200 graph probes, 48 mixed graph permutations.
Next: repeated identifier profiling (client finding 8), inspect cardinality
evidence and preserve safe synthetic repeats rather than inventing uniqueness.
Confirmed adapter-to-generator repro with fictional aggregate profile: events,
100 rows, integer run_id, approx_distinct_count=4, no top_values. Adapter marks
is_identifier=True and synthetic_identifier distribution; generation emits 100
distinct keys. No source rows involved. Root path: legacy_profile adapter ->
infer_dataset_spec -> synthetic_identifier; metadata currently lacks repeat pool.
Asked product choice for count scaling: retain four distinct synthetic keys or
scale distinct ratio (40 keys for 1000 rows). Await answer before choosing that
new default; one-to-one transformation is unaffected. No runtime changes yet.
Broader transformation remains unfinished.

## Pending User Decisions (Do Not Re-ask Every Heartbeat)

- Repeated-key scaling: fixed distinct pool vs proportional distinct count;
  asynchronous question sent, no answer yet. Do not invent the default.
- Identifier/semantic conflict: confirmed synthetic string identifiers with
  phone, email and ssn semantics all fail post-solve privacy validation. Asked
  approval for a narrowly anchored synthetic_<integer> namespace for identifier
  fields regardless of semantic format, retaining sensitivity and source checks.
  This is a safety-contract change; no implementation before answer, executable
  regression tests, OpenSpec/docs and independent review. Alternative is genuine
  reserved semantic-format output with uniqueness/capacity constraints.
- Other independent work remains available: full script acceptance adaptations,
  type-contract specification, documentation and untouched client findings.

## Publication Acceptance Adaptation

- Added tests/test_client_publication_acceptance.py to the existing pytest suite,
  preserving all five directory/overwrite cases. Verifies subprocess import root,
  exit codes, ten-row CSV schema/content and existing-file preservation; bounded
  subprocesses, temporary fictional fixtures, no product monkeypatches.
- Source checkout: 5 passed; Ruff passed. Installed 1.5.0 baseline: 5 passed;
  installed publication candidate: 5 passed. Existing candidate target is publication SHA
  c3f1308, not latest identifier changes; do not mislabel it final 1.6 acceptance.
- Pending product questions do not block this independent acceptance work.
- Signed 3217b3dbefcb15e234cc42f8e72ee4bac57b6219 pushed; PR #518:
  https://github.com/wa-pis/agent-paranoid-android/pull/518
- Independent AI reviewer Darwin (01a0d027-9fee-7422-b0a1-05eec800b579) found
  no blockers on 3217b3d; P3 bytecode writes outside temp directories. Set
  PYTHONDONTWRITEBYTECODE=1 for both subprocesses; five tests and Ruff passed.
  Prior CI green. Request final-SHA confirmation after push; no runtime/policy
  changes in this slice.
- Follow-up afd6beb signed/pushed; Darwin final-SHA confirmation requested.
  Wait for fresh CI and review before merge; do not start duplicate review.
- Completed: Darwin confirmed no outstanding findings on afd6beb; all CI green.
  PR #518 merged as 5aaa2013cea4b21884bc78ff003d0edaa915a976.
  Evidence: https://github.com/wa-pis/agent-paranoid-android/pull/518#issuecomment-5803308782
- Next independent slice: finalize typed transformation policy/mapping contract
  from approved design, with validation-only tests before any source-preserving
  execution. Pending scaling/semantic-policy questions remain unanswered; do
  not infer approval or silently alter existing source-free guarantees.
- Added policy-contract.md review draft: separate evidence/decisions,
  discriminated actions, private typed mapping pairs, schema binding and staged
  validation. No executable model or source-preserving path added yet. Model
  names/approval transport remain review items, not existing API promises.
- Next: independent design review of this draft against approved requirements;
  then implement structural validation only. Do not enable runtime preservation
  before the separately reviewed safety amendment.
- Draft signed/pushed as 224490386f96caa62287cb6dc4210c34ef39b7c7; PR #519:
  https://github.com/wa-pis/agent-paranoid-android/pull/519
  Independent design reviewer Rawls (01a0d039-9c2a-70b3-b12f-604b25add65a)
  running on exact SHA against 5aaa201. No duplicate review.
- Parser investigation: existing parse_dataset_spec_payload echoes unsupported
  version values and returns Pydantic validation errors. Do not route restricted
  inline mappings through it unchanged; private policy errors need bounded,
  value-free output and detached validation exception chains. Reuse model/version
  patterns, not this public aggregate-only error behavior.
- Rawls design review requested revisions: shared/composite mapping domains,
  content-bound approval for referenced inputs and full financial replacement
  semantics. Added explicit sections referencing the already approved design;
  no runtime permission or behavior change. Re-review pending on updated SHA.
- Signed a404c24 pushed; strict OpenSpec and diff checks passed. Rawls re-review
  requested on this SHA; do not duplicate. Next: disposition/CI then merge draft.
- Rawls re-review closed financial/identity gaps, found domain-reference option
  missing from action table/structural checks. Corrected exactly-one-of inline,
  CSV or domain reference; domain owns one concrete inline/CSV source. No runtime.
- Signed 2969e67 pushed; Rawls final delta confirmation requested. Strict
  OpenSpec/diff checks pass; wait for CI/review, no duplicate reviewer.
- Completed: PR #519 merged as 0c87702b21c4117af80f9f2a4064eaa934eee63b,
  final CI green and Rawls closed all design findings at 2969e67.
  Evidence: https://github.com/wa-pis/agent-paranoid-android/pull/519#issuecomment-5803650103
  Approval is for a design draft only, not runtime preservation/safety amendment.
- Next on codex/1-6-policy-models: implement internal structural models and
  value-free parser failures, focused fictional tests. No CSV/database reads,
  execution hooks, public CLI/MCP surface or preservation activation in this slice.
- Local first structural slice: core/transformation_mapping.py models inline
  tuple-pairs, CSV declarations and domain references as a discriminated union.
  Rejects unknown/conflicting variant fields, non-finite numbers and nested
  scalar values; preserves scalar kinds/null and private JSON round-trip. Repr
  excludes entries/paths/names. Parser raises fixed value-free error outside
  Pydantic exception context. No loading, binding, semantic validation or approval.
- Ten fictional focused tests passed; Ruff passed. Initial mypy required an
  explicit TypeAdapter annotation; corrected, mypy and diff checks now passed.
- Remaining for this slice: mapping shape/duplicate semantic checks belong to
  schema-bound preflight; do not call structural acceptance safe-to-execute.
- Added forged-model revalidation case; 11 tests, Ruff and mypy pass. Signed
  5a37288679d8bc8b500d6bcc036a87489af8125a pushed; PR #520:
  https://github.com/wa-pis/agent-paranoid-android/pull/520
- Independent AI reviewer Curie (01a0d051-3e2c-77b0-89b5-dd90445dfd2d) reviewing
  exact SHA against 0c87702. Next: CI/review; no duplicate reviewer or merge yet.
- Curie found Decimal->float coercion and retained ambient exception context.
  Both reproduced as failing regressions. Added exact builtin-scalar guard before
  union validation and explicit context detachment on the bounded error; no
  changes to public execution or policy. Latest follow-up awaits checks/re-review.
