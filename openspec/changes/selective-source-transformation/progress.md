# Implementation Progress

## Authority And Target

- User authorized implementation, signed commits/push, sequential PR merges
  after CI/CD and independent review, and 1.6.0rc1 publication. No stable release.
- GitHub CLI checked: authenticated; repository ADMIN access. Homebrew git
  required because system git invokes unaccepted Xcode license.
- Branch: codex/1-6-field-policies, based on main a4d404b.
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
- Signed 4abd9d0 pushed; 13 tests, Ruff, mypy passed. Curie re-review requested
  on newest SHA; wait for CI and disposition before merge, no duplicate reviewer.
- Completed: PR #520 merged as a4d404be183a00476dfb48640e96b4ae82aac109;
  Curie confirmed both findings resolved at 4abd9d0 and all CI green.
  Evidence: https://github.com/wa-pis/agent-paranoid-android/pull/520#issuecomment-5803898439
- Next: internal field-action union and versioned behavior-policy structural
  envelope, reuse mapping declarations and detached error boundary. No execution
  approval, file reads or source-preserving runtime enabled by parsing.
- Local field-policy slice implemented: five discriminated actions, explicit
  sensitivity declarations, unmatched reject/preserve/synthesize, versioned private
  envelope and named-domain resolution. Preservation declarations are not verified
  authorization; no schema binding, I/O or execution added. Contract note updated.
- Focused mapping/policy tests: 28 passed; Ruff, mypy and diff checks passed.
  Added missing-version, duplicate-domain and unmatched-preserve sensitivity cases.
  GitHub confirms no existing PR for codex/1-6-field-policies.
- Next: signed commit and independent exact-SHA review of this structural slice,
  then PR/CI. Do not mark execution or full behavior-profile support complete.
- Signed 16483bd2b14fdfaa99f53f8dacea39532ed270ca pushed; PR #521:
  https://github.com/wa-pis/agent-paranoid-android/pull/521
  Independent AI reviewer Curie (01a0d051-3e2c-77b0-89b5-dd90445dfd2d)
  reviewing exact SHA against a4d404b. Await review and CI; no duplicate review.
- Completed: PR #521 merged as e2e4194f678fa3ade149a9bbec2012cdb4b3bffe.
  Curie found no issues at 16483bd; 28 tests and additional invalid/forged,
  error-chain and round-trip probes passed. All CI complete and green.
  Evidence: https://github.com/wa-pis/agent-paranoid-android/pull/521#issuecomment-5804067734
- Next: schema-bound validation of complete field coverage and references;
  keep source reads, verified authorization and execution separate. Carry these
  uncommitted progress notes into the next focused branch without discarding them.
- Started codex/1-6-policy-binding from merged main e2e4194, preserving notes.
  Added local exact field-coverage check against existing DatasetProfile, with
  private bounded errors and reparsing of mutable profile contents. No new schema
  model or source reads. 32 focused tests, Ruff and mypy passed.
- This is only coverage validation, not complete schema binding: fingerprint,
  types, dependency references and sensitivity evidence still require work.
  Next: focused mutation/error-chain tests and remaining binding contract before
  commit/review. No PR yet; do not treat this partial helper as execution approval.
- Added mutation regressions for duplicate fields/entities, renamed entities,
  forged policies and ambient exception chains. 36 focused tests, Ruff, mypy and
  diff checks pass. Contract explicitly labels coverage as partial binding only.
- Next: finish schema identity/reference validation before publishing this branch;
  coverage checks alone do not justify a complete schema-binding claim.
- Added local derive-reference validation using stdlib TopologicalSorter:
  missing/dropped/repeated dependencies and cycles fail closed; no formula eval.
  Contract documents same-entity exact names and deferred formula agreement.
  40 focused tests, Ruff and mypy passed. Still uncommitted on policy-binding.
- Next: schema fingerprint/type-drift validation and sensitivity-evidence conflict
  checks, then independent review. Existing fingerprint utility lives in
  io/artifacts.py and hashes full profiles; do not confuse statistics/content
  identity with a schema-only fingerprint or import I/O into core.
- Preservation and unmatched-preserve now reject observed sensitive fields even
  when the policy declares non-sensitive. Two fictional regressions added;
  42 focused tests, Ruff, mypy and whitespace checks pass. Docs clarify profile
  trust and authorization remain separate. No execution path enabled.
- Next remains schema fingerprint/type drift, followed by review of the complete
  local binding slice. No active reviewer or PR for this uncommitted branch.
- Added versioned ordered column-schema fingerprint and validate_policy_profile;
  detects column name/type/nullability drift without hashing distributions or rows.
  Explicitly not identity of constraints, relationships, evidence or source data.
  Tests cover unchanged profiles, changed columns and statistics independence.
  46 focused tests, Ruff, mypy and whitespace checks pass.
- Next: signed commit/PR and independent review of this column-binding slice.
  Mapping type checks, formula semantics and snapshot-bound approval remain pending.
- Signed 9b816d4bdb76c3be6a6c1b2b5f1f5ed25dd34867 pushed; PR #522:
  https://github.com/wa-pis/agent-paranoid-android/pull/522
  Curie (01a0d051-3e2c-77b0-89b5-dd90445dfd2d) independently reviewing this
  exact SHA against e2e4194. Next: findings disposition and CI; no duplicate review.
- Curie found P2 private-value leakage through Pydantic serialization warnings
  for malformed nested profile values, including warnings-as-errors. Disabled
  serialization warnings at both private reparsing boundaries, retaining full
  validation. Four regressions cover both helpers and warning modes.
  50 focused tests, Ruff and mypy pass. Prior CI green; follow-up needs re-review.
- Signed 7a0255557875dacc4f1abab44c7f2dc6b343f294 pushed; Curie follow-up
  review requested. Wait for new CI and finding disposition before merge.
- Completed: PR #522 merged as 9e7661f1d0e2517e8f9a07321a0d0737f545006c.
  Curie confirmed P2 resolved with no new findings at 7a02555; final CI green.
  Evidence: https://github.com/wa-pis/agent-paranoid-android/pull/522#issuecomment-5804500374
- Next: typed mapping preflight (tuple arity, duplicate source keys and scalar
  compatibility) on a new branch from main. No active review; preserve local notes.
  This must remain separate from loading/source access and execution approval.
- Started codex/1-6-mapping-preflight from 9e7661f, preserving notes.
  Added inline tuple-width and exact typed duplicate-key checks. bool/int/float/
  string/null remain distinct before schema normalization; repeated null keys
  rejected. Many-to-one replacements are not rejected at this shape-only layer.
  56 focused tests, Ruff and mypy pass. No reads or runtime transformation.
- Next: schema-type compatibility and normalized duplicate checking before this
  slice is ready for commit/review; shape acceptance alone is not semantic approval.
- Existing schema validator uses permissive text coercion and date truncation;
  not suitable for explicit mapping semantics. Added strict primitive inline
  type/nullability checking without coercion. Null and empty string distinct.
  Temporal/decimal inputs fail closed here; their normalization remains pending,
  not silently borrowed from permissive profiling parsers. 65 focused tests,
  Ruff and mypy passed. No source or mapping-file I/O enabled.
- Next: review this primitive preflight slice and its explicit limitations;
  temporal/decimal normalization and CSV parsing require subsequent implementation.
- Signed 60e49e10b5c78982c77f2c8f3816ee1745815bf5 pushed; PR #523:
  https://github.com/wa-pis/agent-paranoid-android/pull/523
  Curie (01a0d051-3e2c-77b0-89b5-dd90445dfd2d) reviewing exact SHA against
  9e7661f. Next: review disposition and CI; do not duplicate active review.
- Completed: PR #523 merged as 7f828554e46ff5654a24b65d36c25b24437185c9.
  Curie found no issues at 60e49e1; 65 tests and 20 additional probes passed;
  all CI green. Evidence:
  https://github.com/wa-pis/agent-paranoid-android/pull/523#issuecomment-5804763752
- Next: strict date mapping support (no timestamp truncation or timezone coercion),
  then bounded local mapping-file loading. Decimal remains an end-to-end type
  contract, not a float conversion shortcut. No active reviewer; preserve notes.
- Started codex/1-6-date-mappings from 7f82855. Added DATE tuple validation using
  stdlib date.fromisoformat plus exact ISO round-trip. Rejects invalid calendar
  dates, compact/week dates, timestamps and whitespace on both mapping sides.
  Strings stay unchanged; DATETIME/Decimal still unsupported, no coercion/I/O.
  82 focused tests, Ruff and mypy passed; next signed commit and independent review.
- Signed 30b5c1223bec1c4bf609db3f0868361a184d4731 pushed; PR #524:
  https://github.com/wa-pis/agent-paranoid-android/pull/524
  Curie (01a0d051-3e2c-77b0-89b5-dd90445dfd2d) reviewing exact SHA against
  7f82855. Next: review disposition/CI; no duplicate review or merge yet.
- Completed: PR #524 merged as 462f9cafb8c35f5603301584de86f46079bcb081.
  Curie found no issues at 30b5c12; 82 tests and 50 additional probes passed;
  all CI green. Evidence:
  https://github.com/wa-pis/agent-paranoid-android/pull/524#issuecomment-5804898754
- Next: inspect existing bounded file/profile readers and implement private CSV
  mapping loading with explicit encoding/null tokens and strict header/row checks.
  Keep external paths/APIs unsupported and errors value-free. No active review.
- Reader investigation complete: io/path_policy.open_regular_file provides
  descriptor-relative no-follow traversal; core/limits exposes byte/row/column/
  cell ceilings. Existing io/readers.load_dataset_rows detects dialect/encoding,
  emits named errors and accepts loose DictReader rows, so cannot be reused as
  the private strict mapping loader unchanged.
- Next implementation: first a bounded CSV-bytes parser with explicit encoding,
  delimiter/null token, exact unique headers and row widths; then safe file adapter
  supplying one immutable byte snapshot. Reuse path controls, not public reader
  diagnostics. Check special-file opening before adapter integration: current
  open_regular_file opens before fstat and may block on a FIFO. No source files
  read or checks rerun during this investigation; working notes only.
- Started codex/1-6-csv-mapping-parser from 462f9ca. Added private bytes-only
  CSV parser: explicit UTF-8/BOM choice, delimiter/null token; exact unique headers,
  row widths, duplicate keys and byte/row/cell/field ceilings. Empty remains string;
  null token maps to None. Output restricted string/null pairs, no type inference.
  No filesystem access or execution path. Twelve fictional tests and Ruff passed;
  mypy initially requested entries annotation, corrected and mypy now passes.
- Next: deadline/column ceilings and dialect/configuration edge cases, contract
  documentation and independent review before connecting any filesystem adapter.
- CSV parser now requires the caller's existing GenerationBudget (no reset) and
  checks it before parsing, after header, per row and after mapping validation.
  Added explicit column ceiling. Fourteen CSV tests, Ruff and mypy pass.
  Deadline is cooperative around bounded decode/CSV/validation operations, not
  an interruptible hard timeout. Next: configuration/BOM/null/dialect edge tests,
  docs, commit and independent review. No file I/O adapter yet.
- Added BOM/delimiter/multiline/null-disabled and invalid configuration tests.
  24 CSV tests, Ruff, mypy and whitespace checks passed. Contract documents
  private byte-only scope, cooperative deadline, process CSV field ceiling and
  deferred typed numeric conversion/file adapter. Ready for independent review.
- Signed local commit 6984a1b4918239331742e3279c40545ac828a993 created.
  Curie (01a0d051-3e2c-77b0-89b5-dd90445dfd2d) review requested against
  462f9ca. Next: push/create PR while review runs; do not duplicate review.
- Pushed 6984a1b; PR #525 opened. Curie independent AI review found no issues;
  106 focused tests and 20 additional probes passed. Evidence:
  https://github.com/wa-pis/agent-paranoid-android/pull/525#issuecomment-5805152050
  Next: wait for CI, then merge if green. Review complete; no duplicate reviewer.
- Completed: PR #525 merged as d5675160d66c7790418906cc7d1046a0b254e7c0;
  all CI green at reviewed 6984a1b. Bytes-only CSV parsing is implemented, not
  filesystem loading, numeric conversion or transformation execution.
- Next: safe bounded file snapshot adapter. First resolve blocking special-file
  opens in existing open_regular_file; keep all parent-component no-follow
  protections. Add synthetic FIFO/symlink/byte-ceiling/error-chain regressions.
- Started codex/1-6-mapping-file-snapshot from d567516. Shared regular-file reader
  now opens O_NONBLOCK before fstat: a FIFO without a writer cannot hang opening.
  No-follow path checks unchanged. Traced callers in agent_planning/io.artifacts.
  Added isolated subprocess FIFO test with 5s timeout plus regular/symlink checks.
  21 path-policy tests, Ruff and mypy pass. No mapping-file adapter wired yet.
- Next: bounded private snapshot adapter and byte/error tests; review shared-reader
  change alongside it before merge. Preserve uncommitted notes and current changes.
- Added io/mapping_snapshot.py: explicit absolute root + relative path only,
  existing descriptor-relative no-follow opening, bounded chunk reads, shared
  deadline, pre/post descriptor metadata check, hash of returned immutable bytes.
  Restricted dataclass repr omits payload/hash; fixed detached errors.
  Six synthetic snapshot cases plus path-policy suite: 27 passed; Ruff/mypy pass.
- Next: deadline/mutation/parent-symlink tests and contract note, then independent
  review. Snapshot is not execution approval or an atomic database/file snapshot
  guarantee; caller must parse/use these returned bytes, never reopen by path.
- Added parent-symlink, expired-budget and real file mutation during read tests
  using the explicit clock dependency (no product monkeypatch). 30 focused tests,
  Ruff, mypy and whitespace checks passed; contract documents exact guarantees.
  Next: signed commit, independent read-only review and PR/CI before merge.
- Signed local 50c282f6de547f6e34094bf246768d5231ef9a21 created. Curie
  (01a0d051-3e2c-77b0-89b5-dd90445dfd2d) reviewing against d567516.
  Next: push/create PR, review disposition and CI. Do not duplicate active review.
- Pushed 50c282f; PR #526 opened with independent AI review evidence in body:
  https://github.com/wa-pis/agent-paranoid-android/pull/526
  Curie found no issues; 71 tests plus 160 boundary/failure probes passed with
  stable descriptor count. Review complete. Next: CI then merge if green.
- Completed: PR #526 merged as dd3b4f11d77b4533dcf0e5c2401742a5ef834d79;
  CI green on independently reviewed 50c282f. Snapshot adapter and nonblocking
  regular-file opening landed; transformation execution remains disabled.
- Next: connect snapshot bytes to CSV mapping parser with explicit settings,
  retain exact snapshot hash and enforce typed preflight without reopening.
  Numeric CSV conversion, Decimal and DATETIME remain explicit unfinished scope.
- Started codex/1-6-csv-mapping-loader from dd3b4f1. Added private orchestration:
  revalidate CSV declaration, read one bounded snapshot, parse its bytes, enforce
  typed mapping checks, retain snapshot hash in repr-hidden result. Limits and
  invocation budget explicitly passed; no path reopening or numeric coercion.
  Four integration tests, Ruff and mypy pass. No public CLI/MCP/execution wiring.
- Next: prove no reopen on path mutation plus shared-deadline/limit tests, docs,
  then signed commit and independent review. Current changes uncommitted.
- Added source-path mutation after snapshot capture, every explicit limit and
  deadline expiry between snapshot/parser tests via injected clock. Eleven loader
  tests, Ruff, mypy and whitespace checks passed. Docs record private/limited scope.
  Next: signed commit and independent review; no public execution enabled.
- Signed local c3e4a75e29ae7b8b3316c2263eceaefcda79d50c created; Curie
  (01a0d051-3e2c-77b0-89b5-dd90445dfd2d) reviewing against dd3b4f1.
  Next: push/PR and review disposition; do not duplicate active review.
- Pushed c3e4a75; PR #527 opened with full AI review evidence in body:
  https://github.com/wa-pis/agent-paranoid-android/pull/527
  Curie found no issues; 126 tests plus additional composition/error/deadline
  probes passed. Next: CI then merge if green; no active review to duplicate.
- Completed: PR #527 merged as a92587932c77a6f56797b850f3039f054d0d3e44;
  CI green on independently reviewed c3e4a75. Private string/date CSV loader
  integrated, no public transformation runtime or approval boundary enabled.
- Next: numeric CSV normalization contract/implementation, preserving strict
  inline semantics and detecting duplicate keys after conversion. Decimal must
  remain exact; no accidental binary-float financial path. No active reviewer.
- Started codex/1-6-csv-integer-mappings from a925879. Added explicit INTEGER
  CSV normalization: optional sign + ASCII digits, exact Python int, no float
  conversion. Reject whitespace, exponents, underscores and bool text. Re-run
  typed duplicate checks after conversion (+001/1 and -0/0 collide and fail).
  Loader wired to normalization; inline strictness unchanged. 42 focused CSV/
  loader tests, Ruff and mypy pass. Changes uncommitted, no reviewer active.
- Next: configuration/null/composite and deadline tests, contract documentation,
  then independent review/PR. Float, Decimal and DATETIME remain unfinished.
- Added composite string/integer/null and detached configuration/deadline tests.
  47 CSV/loader tests, Ruff and mypy pass. Contract documents ASCII integer syntax,
  post-conversion duplicates, Python digit ceiling and unchanged inline semantics.
  Next: commit, independent review and PR; no public execution enabled.
- Signed local 79f5b0e868ef7248012807c214310b69dcc8abf1 created. Curie
  (01a0d051-3e2c-77b0-89b5-dd90445dfd2d) reviewing against a925879.
  Next: push/PR, review disposition and CI. No duplicate reviewer.
- Pushed 79f5b0e; PR #528 opened with full independent AI review evidence:
  https://github.com/wa-pis/agent-paranoid-android/pull/528
  Curie found no issues; 138 tests and additional syntax/integer/duplicate/budget
  probes passed. Next: CI then merge if green; review complete.
- Completed: PR #528 merged as e540c2ad41919e37e4eb4e8ae79298f191776eba;
  CI green on independently reviewed 79f5b0e. Integer CSV mappings integrated.
- Next: reconcile remaining type work with plan/tasks before adding more helpers:
  Decimal financial contract, explicit float/boolean CSV parsing, DATETIME policy,
  private behavior-profile serialization and actual transformation safety approval.
  No active review; candidate release is not yet ready.
- Reconciled plan/tasks: helper PRs do not complete milestone 1 or CSV vertical
  slice. Started codex/1-6-transformation-safety-contract from e540c2a; added
  safety-boundary.md draft and explicit groundwork/status note in tasks.md.
  Draft scopes mixed-origin output, trusted user authority, snapshot binding,
  default-surface isolation and required executable evidence; AGENTS unchanged.
- Next: specify verifiable approval transport for review (opaque references are
  not authority), then independent boundary review before enabling preservation.
  No runtime changes or tests rerun in this documentation-only reconciliation.
- Inspected agent_approval.py: current reviewed-spec hash proves plan selection,
  not human identity. Same-privilege local agents can invoke identical CLI/files.
  Added explicit pending approval-transport decision to safety-boundary.md:
  trusted local operator (document same-privilege exclusion) versus separately
  controlled signing authority. Ask user before choosing this security boundary.
  No preservation execution or safety amendment activated. Other type/docs work
  remains possible; this blocks approval design, not all implementation.
- Strict OpenSpec validation and diff checks passed. Signed draft-only commit
  ff0f56f85470a29d39d2edb37d142413a0fd9a21 created; Curie independent design
  review requested (01a0d051-3e2c-77b0-89b5-dd90445dfd2d), no option selected.
  Next: review disposition and publish draft PR; user approval-transport answer
  still pending. This draft must not be treated as active policy authorization.
- Curie requested one clarification: copied originals versus independently
  computed equal values. Draft now explicitly retains approved zero/rounding and
  coincident derived-value exceptions without copy/skip fallback, with evidence
  requirement. Strict OpenSpec/diff checks pass. Approval options still unselected.
- Signed follow-up 7bccfc7b89d249dd0acc75a4d199b6e8940be6fe created; Curie
  delta confirmation requested. Next: publish draft PR and review evidence; no
  runtime enablement or decision on pending approval transport.
- Pushed 7bccfc7; PR #529 opened with independent draft-review evidence:
  https://github.com/wa-pis/agent-paranoid-android/pull/529
  Curie closed clarification, no new issues. Next: CI, then documentation-only
  merge if green. Neither approval option is selected; user answer still pending.
- Completed: docs-only PR #529 merged as 8bb1eac395b59d336670487219b87bc374549012;
  CI green on independently reviewed 7bccfc7. Safety boundary remains a draft,
  AGENTS/runtime unchanged; approval-transport decision still awaits user.
- Next independent work: private behavior-policy YAML serialization/round-trip,
  with bounded safe loading and detached errors. Do not implement or infer the
  pending preservation authority. No active reviewer; preserve local notes.
- Started codex/1-6-private-policy-yaml from 8bb1eac. Added restricted UTF-8
  policy load/dump reusing LimitedSafeLoader depth/alias bounds, duplicate/non-string
  key and YAML merge rejection, byte ceiling and shared budget; detached fixed
  errors. No file writes or approval enabled. Nine tests/Ruff passed; corrected
  loader override return annotation, mypy now passes.
- Next: output byte/deadline and nested-duplicate tests, documentation, independent
  review. Approval-transport user choice remains pending and is not inferred.
- Added nested duplicate-key, output ceiling, expired budget and forged policy
  dump regressions with detached errors. Thirteen YAML tests, Ruff, mypy and
  whitespace checks pass. Docs clarify restricted output and post-materialization
  size checking. Next: signed commit, independent review and PR.
- Signed local fa934608e671292ebc56175712ddf45097bad046 created; Curie
  (01a0d051-3e2c-77b0-89b5-dd90445dfd2d) reviewing against 8bb1eac.
  Next: review disposition and push/PR; no duplicate reviewer.
- Curie found P2: malformed standard YAML tags leaked constructor KeyError/
  AttributeError/TypeError instead of bounded errors. Added mapping-node shape
  guard and normalized those safe-loader constructor failures at load boundary.
  Four malicious-tag regressions; 17 YAML tests, Ruff and mypy pass.
  Next: follow-up exact-SHA review before publication/merge.
- Signed 61f74ef3a9f875513a3bb980ca728e8a191bd2fa created; Curie follow-up
  requested. No PR yet; next review disposition and push/PR. No duplicate review.
- Pushed 61f74ef; PR #530 opened with independent review evidence in body:
  https://github.com/wa-pis/agent-paranoid-android/pull/530
  Curie confirmed P2 resolved, no new issues; 17 tests/eight extra probes pass.
  Next: CI then merge if green. Authority decision remains pending.
- Completed: PR #530 merged as 39d10232a705f03f07880a2e434e244545635276;
  CI green on independently reviewed 61f74ef. Private YAML bytes round-trip landed,
  not file publication or execution approval. No active reviewer.
- Next: private policy file load/save using existing no-follow snapshot and atomic
  writer, owner-only permissions and source-free error wrapping. Keep pending
  authority choice unresolved; no preservation runtime activation.
- Started codex/1-6-private-policy-files from 39d1023. Added restricted root-relative
  policy load/save reusing bounded snapshot, YAML parser and atomic_binary_writer.
  Output owner-only mode; safe fixed errors, shared budget checked before publish.
  Five round-trip/permissions/failed-save tests, Ruff and mypy pass. No approval
  or public CLI/MCP activation. Changes uncommitted.
- Next: in-write deadline rollback and malformed-load/private-error tests, docs,
  then independent review. Save is an explicit replacement operation; old contents
  survive pre-publication failure, not an archival/version-history mechanism.
- Added pre-publication deadline rollback and missing/malformed/symlink load
  regressions, including detached errors under ambient exceptions. Nine focused
  tests, Ruff, mypy and diff checks pass. File contract documents post-rename
  fsync limitation; no approval or preservation runtime enabled.
  No existing PR for this branch. Next: signed commit and exact-SHA independent
  AI review before push/PR; approval-transport choice still pending.
- Signed a09664426c495e0aec352e331e6b4e900d21e65f created. Independent AI
  reviewer Curie (01a0d051-3e2c-77b0-89b5-dd90445dfd2d) assigned read-only
  file-persistence scope against 39d1023. Next: review disposition, then push/PR.
  Review active; do not launch a duplicate.
- Curie completed independent AI review of a096644 on 2026-09-24: no findings
  within scope; 56 tests and seven synthetic path/error probes passed. Pushed
  reviewed SHA and opened PR #531; full review evidence recorded in PR body:
  https://github.com/wa-pis/agent-paranoid-android/pull/531
  Next: CI, then merge if green and permitted by branch protection. No active
  reviewer; pending authority decision unchanged. No release tag created.
- Completed: PR #531 merged as bd76cb4bf74d29500fcf2f06387986b51e643a85;
  CI, documentation, container and security checks green on reviewed a096644.
  No branch-protection bypass. Private policy persistence integrated, no public
  transformation execution enabled. Next: reconcile remaining CSV scalar/type
  work with the approved contract before the next focused implementation slice.
  Approval transport remains an unresolved user decision; RC not ready.
- Started codex/1-6-policy-roundtrip-acceptance from bd76cb4. Reconciled plan,
  tasks and client acceptance: do not invent float/Decimal/timestamp conversion
  rules while their contract remains incomplete. Added four integrated fictional
  saved-policy inline-YAML/CSV parity cases: leading-zero string, empty/null,
  integer above binary-float exact range and leap date. Four tests, Ruff and
  diff check passed. Runtime unchanged; this is internal mapping acceptance,
  not execution/wizard/client-private acceptance. Next: negative parity cases,
  document scope and independent exact-SHA review. No active reviewer.
- Extended parity matrix to nullable/nonnullable fields and invalid leap dates:
  10 integrated tests pass; Ruff/diff checks pass. Client acceptance document
  explicitly limits evidence to private persistence and typed mapping validation.
  No product changes. Next: signed commit and independent exact-SHA AI review.
- Signed 756d394733fc1307ce71d1c77af3cb523d5ee510 created; independent AI
  reviewer Curie assigned read-only test/documentation scope against bd76cb4.
  Review active; no duplicate. Next: review disposition and push/PR.
- Curie completed independent AI review of 756d394 on 2026-09-24: no findings
  within scope, 10 tests passed, diff check clean. Pushed reviewed SHA; PR #532
  contains full review evidence:
  https://github.com/wa-pis/agent-paranoid-android/pull/532
  Next: CI then merge if green and allowed by branch protection. No active
  reviewer; no runtime or security-policy changes, RC not ready.
- Completed: PR #532 merged as 6a435db938e8ff43113e3f6f434fdd98f4363f42;
  all applicable CI/container/documentation/security checks passed on reviewed
  756d394. No protection bypass. Saved mapping parity evidence integrated.
  Next: address remaining client-finding dispositions using existing evidence
  before adding further helpers; unresolved authority/type decisions are not
  permission to enable transformation. No active review or release tag.
- Started codex/1-6-client-evidence-register from 6a435db. Consolidated existing
  client evidence for findings 1/8/9/19 and explicitly retained unverified status
  for the others. Distinguished deterministic regression proof from identical
  original-probe outcomes and historical installed candidate from final RC.
  Documentation-only; diff check passed, no unchanged tests rerun. Next: review
  register wording and inspect the original golden_run.py for a bounded fictional
  acceptance adaptation. Pending user choices remain unresolved.
- Read entire original golden_run.py from supplied archive before any execution.
  Found PATH-selected CLI, no subprocess timeouts, unconditional zero exit and
  recursive deletion of its existing work folder. Original not executed here.
  Added bounded fictional CSV profile/infer/generate subprocess adaptation with
  import-root verification, source-free category assertions, row/key/date/amount
  and validation-report checks. One checkout test and Ruff passed. Explicitly
  differs from original source-category-copy expectation; does not close that
  requirement or missing private snapshot/pair cases. Next: isolated installed
  baseline/candidate replay, document adaptation, then independent review.
- New golden CSV subset passed separately against installed public baseline
  /private/tmp/apa-client-acceptance.xrueHB/baseline-1.5.0 and freshly built
  /private/tmp/apa-golden-acceptance.P9Co9L/candidate. Production source unchanged
  at 6a435db938e8ff43113e3f6f434fdd98f4363f42; wheel label remains 1.5.0.
  Built via uv build --wheel --no-build-isolation, installed --no-deps --target;
  shared development dependencies, not clean-environment RC acceptance.
  Wheel SHA256 f4ec99405d10d9021f54b1909d55499f67ce9c92537d7648cf7ad900e8f31f14.
  Test SHA256 5fbdbc2eaf9352bf9e2003e15b9cf5674cbe06ae3c88c10c994f6c4a2d20036a.
  Each test verified subprocess import root; no monkeypatches/private inputs.
  Documented source-free adaptation and compatibility-only outcome. Next: signed
  commit and independent review of the test/register; original full replay pending.
- Signed 2e176d33802d09665ccede75ff162655b9f03435 created. Independent AI
  reviewer Curie assigned read-only CSV acceptance/evidence scope against 6a435db.
  Review active; no duplicate reviewer. Next: disposition, then push/PR and CI.
- Curie completed independent AI review of 2e176d3 on 2026-09-24: no findings
  in narrow scope. Adaptation passed checkout and both installed targets; hashes
  matched. Original script read, not executed; historical dispositions not
  independently re-proven. Pushed reviewed SHA, PR #533 contains review evidence:
  https://github.com/wa-pis/agent-paranoid-android/pull/533
  Next: CI then merge if green and branch protections permit. No active reviewer.
- Completed: PR #533 merged as dc68e44d5ef8711714e6abdbf5be29e86c0fc79c;
  all applicable CI/container/documentation/security checks passed on reviewed
  2e176d3. No protection bypass. Fictional source-free CSV acceptance integrated.
  Next: inspect untouched client finding 2 (distinct-cap uncertainty) and its
  existing focused tests before selecting a reproduction. No active reviewer;
  preservation authority and other pending product choices remain unresolved.
- Inspected finding 2 without rerunning existing tests: legacy CSV digest path
  has cap regressions, but folder schema FieldAccumulator returns unique_ratio
  1.0 after its 10,000-value cap if repeats occur only among untracked values.
  Unpatched fictional repro via PYTHONPATH=src, actual add/to_profile path:
  11,001 rows, 10,001 distinct, reported ratio 1.0 versus actual ~0.9091;
  overflow true, duplicate_seen false. No product monkeypatch or external input.
  This can nominate a false primary-key candidate (threshold 0.98).
  Next: deterministic folder regression and inspect consumers before choosing
  conservative uncertainty representation; preserve budgets and source-free mode.
- Started codex/1-6-distinct-overflow from dc68e44. Added real folder-path
  regression tests/test_schema_distinct_overflow.py; baseline fails as expected
  (unique_ratio 1.0). No production edits. Consumers include primary-key
  nomination and relationship-discovery evidence/confidence. FieldProfile has
  only a numeric unique_ratio, no uncertainty marker; silently replacing it
  with zero or a lower bound would mislabel evidence. Request product approval
  for explicit exact/lower-bound metadata and no automatic PK nomination from
  overflow evidence. Next: approved representation, focused fix/tests/docs and
  independent review. Current regression deliberately red, do not merge/release.
- User approved a separate transformation-report requirement on 2026-09-24:
  “Сохранено исходных значений: X%”, measuring actual unchanged source values.
  Recorded in design.md and tasks.md as unimplemented, with comparison-scope,
  denominator and disclosure requirements. This approval does not authorize
  preservation or resolve distinct-overflow uncertainty. No runtime changes;
  existing red regression and unrelated progress notes preserved. Validation:
  documentation-only diff whitespace check; no unchanged tests rerun.
  Next: settle the metric's executable comparison contract as part of the
  authorized transformation reporting slice; preservation authority remains
  a prerequisite to enabling execution.
- User explicitly approved both proposed requirements on 2026-09-24: personal
  human confirmation of concrete preservation columns/exact plan (no agent
  self-approval; sensitive/disputed columns blocked), and lower-bound uniqueness
  with no automatic primary-key nomination on distinct overflow. The approval
  transport still must meet the human-authority requirement; no silent adoption
  of the equal-local-privilege threat exclusion and no active safety exception.
- Implemented capped folder uniqueness fix in the working tree: additive
  unique_ratio_kind metadata (legacy default unspecified), downward-truncated
  lower bound, overflow excluded from PK/ratio-based identifier inference,
  relationship parent guard/child evidence omission and advisor propagation.
  Fictional focused tests: 17 passed; Ruff clean; mypy clean (4 source files).
  Profiling guide and design updated. No source-preserving runtime enabled.
  Next: independent exact-SHA review, then signed PR/CI; do not release this
  unreviewed working tree. Other existing dirty requirements notes retained.
- Signed commit 4fdf1f5fc256b9909056ceacbd97d16532a6952f created with
  normal configured Git hooks. Independent AI reviewer Curie assigned read-only
  review against dc68e44; review active, no duplicate. Next: resolve findings,
  record exact-SHA evidence, then push/PR and applicable CI before merge.
- Curie AI review of 4fdf1f5 (2026-09-24) found two P2 upgrade defects:
  additive unspecified metadata changed persisted-plan hashes; cache format 2
  could reuse stale false uniqueness/PK evidence. Disposition: fixed canonical
  profile hashing to omit only unspecified metadata; bumped folder cache to 3.
  Explicit measurement metadata remains fingerprint-bound. Added fictional
  persisted-profile hash and old-cache reprofile/round-trip regressions.
  Focused checks: 13 tests passed (overflow + agent review); Ruff clean.
  Next: signed correction and repeat independent review on current exact SHA.
- Signed correction 00d7aa797a2911f1cdaa59005f71b0982f04c305; mypy clean
  for both changed source modules. Curie repeat AI review active on this SHA,
  focused on both P2 dispositions and regression risk. No PR/push yet.
- Curie repeat independent AI review completed 2026-09-24 on 00d7aa7:
  both P2 resolved, no new delta findings; 90 tests and independent legacy-hash,
  evidence-binding/nonmutation probes passed. Not human approval. Reviewed SHA
  pushed; PR #534 records identity, exact SHAs, scope, findings/disposition and
  evidence: https://github.com/wa-pis/agent-paranoid-android/pull/534
  No active reviewer. Next: applicable CI and protection-compliant merge.
- PR #534 CI blocked on public-contract fixture drift across Python versions:
  advisor-exchange.json lacked three additive unique_ratio_kind=unspecified
  entries. Python 3.11: 1 failed, 1580 passed, 10 skipped. No runtime failure
  inferred from that snapshot mismatch. Updated only those three fixture fields;
  focused contract tests: 3 passed, diff check clean. Next: signed fixture fix,
  independent delta review on updated SHA, push and green CI before merge.
- Signed fixture correction ead682bd86a0e24a120f4c86a431f17009342359;
  Curie independent read-only delta review active. No duplicate reviewer.
- User clarified review scope: no AI review for every ordinary commit/PR;
  independent AI review only for final release-candidate SHA, plus separately
  required safety-policy review. GitHub protections still apply. Updated the
  heartbeat prompt accordingly and sent Curie a stop instruction for the
  unnecessary fixture delta review. Pushed ead682b to PR #534 for CI.
  Next: green CI/protection-compliant merge; do not add ordinary AI review gates.
- PR #534 merged as 0b7556ec29359d409d7aef55e977fe4711f482da after all
  applicable CI, Python 3.11–3.14, containers, documentation and security checks
  passed on ead682b. Normal merge with exact-head guard; no protection bypass.
  Client finding 2 capped-folder uncertainty corrected, upgrade regressions
  covered. Next: update client acceptance disposition and continue remaining
  confirmed client findings/CSV slice without ordinary per-PR AI review.
- Started codex/1-6-client-followup from merged 0b7556e, carrying existing
  progress notes unchanged. Updated client finding 2 disposition with scoped
  regression/CI evidence and explicit old-profile/private-input/RC limitations.
  Inspected finding 10: legacy date adapter retains missing min_date/max_date;
  ranged_datetime defaults missing endpoints to 2020-01-01/2025-01-01. This is
  code inspection, not a completed client reproduction or a new test pass.
  Next: trace planning/report disclosure and reproduce missing-bound behavior
  on fictional metadata before choosing the smallest corrective change.
- Finding 10 reproduced on unmodified 0b7556e via legacy fictional metadata,
  inference, real generation and plan warnings: DATE/DATETIME each generated
  three rows in the default period without date-fallback disclosure. New focused
  regressions failed twice on missing warning; complete-bound control passed.
  Added bounded generic review-plan warning (no source values/names), preserving
  generator behavior. Generation guide updated. Scope is review-first planning,
  not full output-report utility disclosure or final client acceptance.
  Next: focused checks, partial-bound/category controls, then ordinary PR/CI.
- Focused date-fallback/agent-review/public-contract checks: 10 passed;
  Ruff and targeted mypy clean; diff check clean. Working change not yet committed.
- Added partial-min/partial-max, categorical-date and identifier-path warning
  controls; all 7 date disclosure tests passed, Ruff/diff checks clean.
  No generation semantics or safety-policy changes. Next: signed PR and CI;
  final installed replay and broader output utility reporting still pending.
- Signed ddc6b94 pushed; PR #535 opened for date fallback plan disclosure:
  https://github.com/wa-pis/agent-paranoid-android/pull/535
  No ordinary AI review launched. Next: green applicable CI and normal merge.
- PR #535 merged as 1da23ad12146309e3f7f6435215864e7ddb89cd7: all 41
  reported checks completed with success or intentional skip, none failed.
  Normal exact-head merge; no protection bypass. Date fallback disclosure in
  review-first planning landed; no claim of complete finding 10 acceptance.
  Next: continue CSV transformation contract/remaining client evidence; resolve
  preservation authority transport before activating any source-preserving path.
- Started codex/1-6-csv-key-acceptance from 1da23ad, preserving dirty progress.
  Finding 4 fictional actual CSV -> profile -> spec -> generation probe:
  100 rows/four integer run_id values => zero top values, identifier=true,
  100 generated distinct keys; text equivalents => four synthetic top values,
  identifier=false, four generated categories. Source code unpatched; seed 7;
  PYTHONPATH=src .venv/bin/python /private/tmp/apa_repeated_csv_probe.py.
  Temporary fixture directories isolated and automatically cleaned; output only
  aggregate counts. This confirms numeric branch of finding 4 and disproves
  blanket missing CSV top_values; shares finding 8's unresolved scaling choice.
  Updated acceptance register; no runtime fix or private-client pass claimed.
  Next: executable regression once repeated-key scaling is selected; continue
  independent agreed work without silently choosing fixed/proportional defaults.
- User approved fixed distinct-key cardinality: four source keys remain a pool
  of four synthetic keys when output grows. Implementation in progress; no
  proportional scaling default. User also required automation to stop on blockers.
  Paused heartbeat automation because preservation approval transport remains
  unresolved; prompt now requires PAUSED plus actionable blocker notification,
  resumption only on user request. Direct work on approved repeated-key fix may
  continue; this does not enable source-preserving execution.
- Implemented the approved fixed repeated-identifier pool in CSV/folder/aggregate
  inference and the shared generator. No source literals or row mappings retained;
  existing disjoint identifier domains remain. Reject undersized explicit PK pools,
  exclude repeated folder keys from PK nomination, ignore censored CSV counts and
  invalidate stale folder caches (format 4). Old no-pool serialization unchanged.
  Focused pool/domain/overflow/contract tests: 43 passed. Targeted mypy (6 files),
  Ruff and diff check passed after correcting a serializer return annotation.
  Tests cover 2/100/1000 rows, deterministic keys, nulls, integer/string domains,
  near-unique repeated keys, censored counts, strict pool validation and roundtrip.
  Documentation/OpenSpec/acceptance updated; no private-input or installed-RC pass.
  Next: signed commit, ordinary PR/CI; no per-PR AI review. Source-preservation
  authority remains a separate unresolved gate. User now permits autonomous
  heartbeat resumption when its blocker is resolved and useful work is available;
  automation remains PAUSED, with the updated resumption rule saved.
- Additional existing CSV/domain-agnostic/generation-contract regressions:
  132 passed. Combined focused coverage this change: 175 tests passed.
- Signed c28ac5a4d9046e513b3f3799f9ac830dbca8b804 pushed; PR #536 opened:
  https://github.com/wa-pis/agent-paranoid-android/pull/536
  GitHub confirms documentation running and remaining jobs queued on that SHA.
  Next: inspect CI results, fix any regression, then normal exact-head merge.
  No duplicate tests or ordinary AI review launched. RC remains incomplete.
- Finding 7 timestamp subcase independently replayed through CSV profiling,
  inference and generation using an inspected fictional-only isolated probe:
  /private/tmp/apa_timestamp_acceptance.py (SHA-256
  22006c561a0ae2e48bfb62ccfcb2e008c8b6dc79c404a18ca33d66b4efb2ddab).
  Current c28ac5a and saved baseline 1.5.0 both retained time, +03:00 offset and
  bounds across 20 rows. Baseline import path and distribution version verified.
  Initial baseline/bin/python invocation failed because this is a target package
  directory, not a virtualenv; corrected PYTHONPATH with existing interpreter.
  No product monkeypatch, source/private input or external connection used.
  This is already-fixed timestamp evidence, not closure of monthly-date semantics
  or mixed profile/spec routing. PR #536 CI last observed 33 success, 4 skipped,
  4 running; no failures. Next: finish CI/merge, then address remaining subcases.
- PR #536 merged as ca6cb1233b6863d86bbc67a6f820ef9e28c76405 after
  all 41 checks completed: 37 success, 4 intentional skips. Exact-head normal
  merge; no GitHub protection bypass or ordinary AI review. Fixed-key cardinality
  is now on main. Source-preserving CSV execution remains gated by approval
  authority choice; sent the user the two concrete deployment options. Heartbeat
  remains paused. Next: remaining client routing/diagnostic cases while awaiting
  that decision; do not silently select a weaker authorization contract.
- Reproduced finding 7 mixed JSON routing through the real CLI with fictional
  profile-shaped inputs plus schema_version/privacy_settings/generation_settings.
  All three baseline checks failed on missing recovery guidance (exit 2 and no
  publication already correct). Added bounded static diagnostic explaining
  spec-key precedence, original profile artifacts and direct spec generation;
  explicitly warns against deleting privacy settings to force profile parsing.
  No routing behavior or safety policy changed. Focused diagnostics/adapters/spec
  contracts: 56 passed; Ruff/diff check clean. Automatic reinterpretation remains
  unresolved, not claimed fixed. Next: batch remaining safe diagnostics and
  acceptance evidence before the next PR; avoid another diagnostic-only micro-PR.
- Batched client diagnostics 11/16 with the mixed-JSON recovery hint. PostgreSQL
  connection errors now return only fixed typed-network/TLS or allowlisted
  SQLSTATE categories; unknown/wrapped errors remain generic. No backend text
  parsing, endpoint/credential disclosure, or exception-context retention.
  Verified SQLSTATE names against installed psycopg/errors.py. SQL JOIN/CTE
  rejections provide fixed shape-specific hints; accepted query policy unchanged.
  Injected fictional driver and local SQL tests only; no live databases or API.
  PostgreSQL client/profiler and SQL policy: 52 tests passed; targeted mypy/Ruff
  and diff check passed. JSON diagnostics/adapters/spec contracts: 56 passed
  in prior step. Documentation updated. Next: signed batch PR and CI; final
  installed-RC and real-driver connection behavior are not claimed verified.
- Signed 5cbe409 pushed; consolidated diagnostic PR #537 opened:
  https://github.com/wa-pis/agent-paranoid-android/pull/537
  Next: observe CI on this SHA and normal merge if green; no ordinary AI review.
- Finding 15 early-validation subcase reproduced: two fictional invalid category
  scopes reached PostgreSQL queries before failing. Reused the existing category
  query builder for preflight against explicit scopes before connection/query;
  wildcard scopes validate after bounded metadata expansion and before aggregates.
  No new allowlist permission, category limit, query execution or policy bypass.
  Existing profiler/query-builder suite plus two new boundary checks: 28 distinct
  tests passed (26 initial, then all 11 profiler tests after two added checks).
  Targeted mypy/Ruff and diff checks passed. No live DB used. Work remains local
  while PR #537 CI finishes (last observed 34 success, 4 skips, 3 running).
  Next: merge #537 if green, then carry this checked fix into the next branch/PR.
- PR #537 merged as 3caa3acc4b33251aa2997ab5e51f5c27d6241f34 after
  37 successful checks and 4 intentional skips. Exact-head normal merge.
  Category preflight carried to codex/1-6-category-preflight from that main SHA;
  existing local changes preserved. Next: signed preflight fix PR and CI.
- Signed 03f493c pushed; PR #538 opened:
  https://github.com/wa-pis/agent-paranoid-android/pull/538
  Next: CI, normal merge, then remaining client/CSV requirements. No full-scope
  acceptance or RC readiness claimed; preservation authority remains unresolved.
- Finding 10 table-profile root cause reproduced with fictional injected
  PostgreSQL aggregates through real profile -> spec -> generation: DATE and
  TIMESTAMPTZ discarded provided endpoints. First harness attempt misrouted a
  metadata query; corrected the fixture, then both regressions failed on absent
  range distributions. Added min/max to the existing column-summary query only
  for non-sensitive temporal columns; typed/order/timezone validation before
  retention, no extra query, no sample or real DB. Sensitive-name bounds blocked
  in profiler and builder; all-null columns retain no claimed bounds.
  Profiler/builders/initial temporal tests: 30 passed; expanded temporal suite:
  8 passed (36 distinct checks total). Mypy/Ruff/diff checks clean. Work local
  pending #538 CI; latest observed 33 successes, 4 skips, 4 running.
  Next: finish negative timezone checks and documentation/acceptance; merge #538
  when green before a sequential temporal-bounds PR. Query-source date profiling
  and final installed-RC acceptance remain separate, unverified requirements.
- Added and passed mismatched naive/aware timestamp rejection; temporal suite
  now has 9 cases, 37 distinct focused checks for this change. #538 has one
  remaining running check, 36 successes and 4 intentional skips. No CI rerun.
- PR #538 merged as 70ee64d023cbf2d5ed60401bda4ac11771886546 after
  37 successful checks and 4 intentional skips; exact-head normal merge.
  Temporal-bounds work moved intact to codex/1-6-postgres-date-bounds from main.
  User PostgreSQL guide now distinguishes observed table bounds, sensitive/all-null
  exclusions, invalid-bound failure and still-unverified query-source support.
  Next: signed temporal-bounds PR and CI; no source-preservation authority assumed.
- Signed de9724e pushed; PR #539 opened:
  https://github.com/wa-pis/agent-paranoid-android/pull/539
  Next: CI and normal merge if green, then remaining query-source/client evidence.
- User supplied refreshed handover archive and requested OpenSpec planning only.
  Recorded SHA-256 and intake in feedback-2026-09-24-v2.md; read new findings
  20–26, refreshed SQL/formula evidence and RC section E. Compared script hashes:
  golden/output-contract/fix-runner unchanged; fix-ab changed; five new scripts.
  No supplied scripts executed, private data imported, network/DB connected or
  runtime implementation changed in this planning turn. Current-code inspection
  recorded as leads, not reproduction evidence. Added work packages/dependencies,
  decision gates, 1–26 acceptance tracking and proposed specification scenarios;
  linked proposal/plan/tasks. Existing scope and source-preservation gate retained.
  Next: validate this OpenSpec plan, then fully inspect new harnesses and reproduce
  22/25 first; authentication, wider SQL and invalid-Parquet decisions stay gated.
- Planning validation passed: `openspec validate selective-source-transformation
  --strict`; git diff whitespace check clean. Runtime tests intentionally not
  repeated for this documentation-only intake. Plan remains local; no PR/merge
  or candidate release was performed as part of the new planning request.
- In the following goal continuation, PR #539 was verified green (37 success,
  4 intentional skips) and merged normally as
  4550f225263071dd51db728ee248d629ad798bb8. A subsequent `gh pr view`
  failed through the system git/Xcode license path; explicit Homebrew-git PATH
  confirmed GitHub state MERGED and exact merge SHA. The uncommitted v2 OpenSpec
  plan was preserved on codex/1-6-feedback-v2-plan from that main commit.
  Next: commit/publish the validated plan, then inspect the changed client
  harnesses and reproduce findings 22/25. Heartbeat stays paused while its
  preservation-authority blocker remains unresolved.
- PR #540 (new-feedback OpenSpec planning only) passed 8 checks with 14
  intentional skips and merged normally as
  ae105fa55d55a6e890d37314b02ce7eb8d963597. No runtime behavior changed.
  New branch codex/1-6-query-connectors began clean from that main SHA.
- Finding 22 reproduced on fictional SQL with installed sqlglot 30.13.0:
  AND/OR are `exp.Func` subclasses and eight PostgreSQL/Trino predicate cases
  failed as forbidden functions; two forbidden-function controls passed. Excluded
  only exact And/Or types from function check, retaining AST node allowlist,
  function allowlist and budgets. Parser/adapter focused suite: 37 passed,
  including fake-driver profile -> spec paths for both adapters. No real DB.
  Candidate dependency-lower-bound and installed-RC evidence remain outstanding.
- Finding 25 reproduced with the unmodified spec-input CLI on fictional fixture:
  explicit `--mode mixed --invalid-ratio 1` returned success while saved spec
  remained valid/0; manifest effective_rules matched that wrong execution.
  Asked user how explicit valid mode should treat a saved mixed ratio; no policy
  or publication-semantics change made pending that decision. SQL scope guide,
  focused Ruff/mypy/diff checks and strict OpenSpec validation passed. Next:
  commit/publish the finished connector fix, then mode parity after precedence
  is settled. Preservation authority remains separately unresolved.
- PR #541 passed 37 checks with 4 intentional skips and merged normally as
  b43005ee15bc47820cef8ad829fadd7b51df1f73. No ordinary AI review or
  protection bypass. Exact-head SQL fix is on main; branch
  codex/1-6-doctor-reporting began clean from that merge.
- Finding 20 confirmed in the current doctor service on fictional injected
  failures: installed-extra smoke wrongly advised reinstall, quickstart raised
  before returning any report, and a core import error echoed its raw message.
  Local fix distinguishes absent module from broken import, retains completed
  checks and structured JSON/exit 1 on quickstart failure, and gives fixed
  local-capability recovery guidance without exception text. Missing extras
  still retain pinned install guidance. Doctor/dependency focused checks:
  29 passed; targeted Ruff, mypy and diff checks passed after correction.
  Two fresh-process checkout-venv `doctor --json` runs returned exit 0 and
  identical 11-state reports; this is not installed-wheel evidence. No supplied
  client harness or real external service was run. Final diff and strict
  OpenSpec validation passed; next: signed PR/CI. Fresh-process installed-wheel
  doctor replay and full
  finding-20 acceptance remain pending.
- PR #542 completed 37 successful checks and 4 intentional skips, then merged
  normally as 47a1eb83d028713d8f3d3dc2e3d768bc9643f16b. No ordinary AI
  review or branch-protection bypass. Main was clean at that SHA.
- Built an offline wheel from 47a1eb83d028713d8f3d3dc2e3d768bc9643f16b
  using the existing hatchling environment (uv's default cache was sandbox-
  inaccessible). Wheel SHA-256:
  e356fff2dcb87ab1a03971991d7be10a10e7249c8b57c3467677201d348326e8.
  Installed it with `pip --target --no-deps` under a new private temporary
  directory; asserted package import resolved to that target, not the checkout.
  Two fresh-process wheel `doctor --json` calls returned exit 0 with identical
  11-state reports; one `doctor --require-extra parquet --json` returned exit 0
  and available capability. Dependencies came from the existing venv, so this
  is neither clean-environment nor final 1.6.0rc1 evidence. Wheel metadata still
  says 1.5.0; the source SHA and hash identify this interim build. No network,
  database, external API or production data used.
- Fully read supplied `probe_doctor_parquet.py` and `probe_parquet_types_ab.py`
  without execution. The former's fixed arm monkeypatches product code, emits
  raw exception text, lacks subprocess timeout and returns zero after failed
  iterations. The latter removes a fixed archive-relative output directory,
  selects CLI from PATH, lacks timeouts and can return zero without an artifact.
  Neither is approved as-is for candidate acceptance. Next: prepare bounded
  fictional, unpatched baseline/candidate adaptations; keep private/live cases
  unverified. A new sequential evidence branch holds this note only.
- Ran a bounded, unpatched fresh-process doctor adaptation against separately
  installed public 1.5.0 baseline and interim candidate at merge SHA 47a1eb8.
  Each subprocess import was proven to resolve inside its own installed target;
  both repeated `doctor --json` calls and both repeated
  `doctor --require-extra parquet --json` calls returned exit 0, structured JSON
  and identical reports (11 and 12 checks respectively). Each process had a
  30-second timeout and bounded captured output. This confirms only the healthy
  installed-wheel path with the shared development dependencies, not the
  injected failure path, clean-environment behavior, final RC, or original
  client probe (which was not executed). No DB, API or private data was used.
  Next: characterize finding 24 with a bounded fictional Parquet baseline/
  candidate probe, then settle the mode/type policy before implementation.
- Characterized findings 24/25 using the supplied Parquet probe's fictional
  spec extracted as data (the script itself was not run). With explicitly
  selected installed CLIs, proven import roots, 30-second subprocess timeouts,
  bounded output and an isolated no-symlink `/private/tmp` work folder, public
  1.5.0 baseline and interim candidate produced the same result: successful
  Parquet artifacts, `created_at` physically `string` despite declared `date`,
  `amount` `int64`; explicit `--mode negative --invalid-ratio 1.0` still reported
  effective `valid/0.0` in both manifests. The first attempt used the system
  temporary path, whose symlinked ancestor was correctly rejected by the
  product's no-follow filesystem policy; rerun used the canonical path.
  No client script, monkeypatch, live integration or private data was used.
  Next: implement the confirmed spec-input mode override after the pending
  precedence choice; design typed Parquet handling without silently coercing
  invalid heterogeneous values.
- Reconciled reproduced 20/22/24/25 evidence into `client-acceptance.md` with
  exact installed-package scope and explicit remaining gaps; no finding was
  marked finally accepted from a healthy-path or interim-wheel probe. Inspected
  all Parquet publication callers and confirmed a declared-schema fix must
  carry the reviewed DatasetSpec through both CLI and agent writers; direct
  row-only writer cannot infer all-null/date types reliably. No runtime or
  safety-policy change. OpenSpec strict validation and git diff check passed.
  Next: settle mode precedence and invalid heterogeneous Parquet policy, then
  make one focused schema/override implementation with physical-type tests.
- Completed static inspection of remaining refreshed `rc_anchor_check.py` and
  changed `probe_fix_ab.py` plus its runner before any execution. The fix arm
  monkeypatches product publication, recursively removes fixed output and lacks
  timeouts; anchor script returns zero despite drift. Original scripts not run.
  A read-only AST adaptation inventoried all 61 anchor tuples, then compared
  exact installed public 1.5.0 and interim `47a1eb8` package trees: 61/61
  same-line at baseline; candidate 41 same-line, 14 moved, 6 absent. This is
  navigation evidence only, not functional or final-RC acceptance. Added
  SHA-256 for all six new/changed probes and inspection boundaries to the v2
  intake. Next: re-anchor claims only on final installed RC; use existing
  unpatched, bounded publication acceptance instead of the monkeypatched
  `probe_fix_ab.py` arm. Continue independent client work while mode/Parquet
  product choices remain unanswered.
- Traced finding 25 end to end before editing: spec-input CLI defaults erase
  explicit-versus-omitted flag provenance; spec generation ignores mode/ratio,
  while business-rule adapter reads CLI defaults. Forwarding `negative` alone
  would expose the existing publish-with-exit-1 path for intentionally invalid
  rows. Kept that public contract unchanged pending the already-requested
  precedence/Parquet publication decisions. Independently measured finding 17
  with a fake-driver regression for PostgreSQL and Trino: three fields (two
  numeric) issue seven bounded schema/aggregate requests; one explicitly
  reviewed category adds one, default sends no category/raw-row request.
  `tests/test_sql_query_profiling.py`: 14 passed; targeted Ruff and diff check
  passed. This is not live scan-cost evidence and authorizes no SQL expansion.
  Next: resolve 25's mode and intentional-invalid publication contract; then
  implement it once across generator, business rules, manifest and exit status.
- PR #543 (`c422d1b`) passed 37 GitHub checks with four intentional skips,
  signed-commit verification and CLEAN merge state; merged normally as
  `c31b62d3156523513e2156f534b380f75c484a24`. No ordinary AI review or
  branch-protection bypass. The query-count test and refreshed harness/evidence
  register are on main; finding 17 live scan cost remains unverified.
- Inspected remaining finding-10 query-source path. A validated SQL projection
  may alias a sensitive source column to a benign output name; the current
  validated plan stores output fields but no source-field lineage. Adding
  temporal min/max based only on output names could disclose sensitive bounds.
  No query, policy or runtime change made. The preservation approval transport
  remains the release-critical decision; mode precedence, intentional-invalid
  exit/publication and heterogeneous Parquet choices are also unanswered.
  Next: obtain explicit decisions, then implement with executable safety tests
  and independent safety-policy review where the boundary changes. Automation
  remains paused; no RC tag or publication exists.
- The user selected trusted local CLI operator confirmation for preservation.
  Recorded the exact-plan/column prompt, fixed-byte receipt, default-agent
  exclusion and equal-privilege limitation in the safety boundary, policy
  contract, proposed spec, tasks and milestone plan. This is a product decision,
  not approval of any dataset or an enabled runtime exception. No source rows,
  private data, database or external API were used. GitHub PR listing was
  temporarily unavailable; local branch `codex/1-6-local-approval` starts from
  merged main `c31b62d` and contains only the documented decision plus this
  progress note. Next: strict OpenSpec/diff validation, then implement the
  interactive approval and exact-input verification with fictional executable
  tests before the scoped AGENTS.md/baseline amendment and independent safety
  review. Automation stays paused; no release tag or publication exists.
- PR #544 opened for signed `dee0bb84582784df42b133f8627bd239ad5453d8`;
  documentation-only checks passed (Python 3.11–3.14 and documentation, with
  expected skips). Independent read-only AI reviewer Codex (agent nickname Jason)
  (`01a0d4ff-6054-7643-a81f-9b81ec008d95`), 2026-09-24 19:59 UTC, found
  three contract ambiguities: digest-only review could hide effective actions,
  sensitivity evidence was not explicitly receipt-bound, and agent approval
  parity could imply receipt minting. Amended only the affected proposed
  contract to show value-free effective actions/fallbacks/status, bind reviewed
  evidence and exclude agent/MCP minting. These corrections require checks and
  same-reviewer re-review on the new exact SHA before merge. This is AI review,
  not human approval; no source-preserving execution is enabled.
- Same AI reviewer re-reviewed the corrected contract at exact
  `2bd910eea5f896f2d84c5916cd687b1afb842562` on 2026-09-24 20:02 UTC:
  all three findings resolved at proposal level; no new material safety issue.
  Read-only diff/ancestor/whitespace checks passed. This is not human approval
  and does not complete the runtime safety amendment or executable gates.
  Next: merge #544 only after the corrected head's green CI and GitHub
  protection checks; then implement local approval with fictional tests.
- PR #544 finished with 8 successful checks and 14 intentional documentation-
  only skips on head `201b3c3426bfe8a54a683b7f6d479c25aca11501`; GitHub
  verified the commit signature. Independent AI review evidence:
  https://github.com/wa-pis/agent-paranoid-android/pull/544#issuecomment-5821355214
  The PR merged normally as `62dde02113a1746ebc998a657613227648828ad0`.
  New branch `codex/1-6-local-approval-gate` starts from that main SHA, with no
  runtime edit yet. Next small step: design and test a bounded exact-byte
  approval request/receipt with value-free CLI display; do not publish a
  source-preserving execution path until the AGENTS.md/baseline amendment,
  executable safety tests and independent review are complete.
- Started private approval-material groundwork on the new branch: bounded,
  labeled exact-byte snapshot identity for review/policy/classification/source/
  mapping/generation-policy parts; deterministic order, duplicate/missing-part
  rejection and stale-byte comparison. Added a value-free bounded review
  renderer covering every field action, unmatched fallback and declared/
  observed sensitivity; mapping values and authorization references are absent.
  Fictional focused tests: 45 passed; targeted Ruff and mypy clean. No receipt,
  interactive CLI command, source read, execution hook or preservation path
  exists yet. Next: test local TTY-only confirmation and restricted receipt
  storage/verification against the same snapshots, then complete the scoped
  safety amendment before any source-bearing execution.
- PR #545 at signed `0ec342bc7c9be54a1fb0f702c0b22526355fb574` passed
  all 37 applicable checks (four intentional skips) and merged normally as
  `190905f27538f7b674f46161d259876024c130c7`. GitHub verified signature;
  no ordinary AI review ran. The first merge request was stopped by the local
  approval guard because `reviewDecision` was empty. Read-only ruleset #19376395
  confirmed zero required approving reviews and no required reviewers; the
  unchanged normal merge then succeeded. No protection setting was changed or
  bypassed. New branch `codex/1-6-local-receipt` starts at that main SHA.
  Next: implement and test terminal-only confirmation plus owner-only receipt
  over the existing private snapshot identity, with no execution/public agent
  path until the safety amendment and independent review are complete.
- On `codex/1-6-local-receipt`, added private approval-material preparation
  from bounded policy/profile bytes plus exact source/mapping/generation-policy
  snapshots. Unreferenced or missing external parts fail; review is generated
  from parsed actions, not a caller-supplied summary. Added local TTY-only
  confirmation, owner-only atomic receipt and same-snapshot verification;
  rejected input publishes nothing. Initial PTY test hung because its reader
  did not handle child exit; stopped only that pytest process and replaced the
  test with a bounded `pty.openpty` channel check, without product monkeypatch.
  No public CLI/agent endpoint or source-preserving execution is connected.
  Focused 55 tests passed, including missing/stale receipt, owner-only mode,
  rejected answer, non-TTY input and omitted/extra references. Targeted Ruff,
  mypy, strict OpenSpec and diff checks passed. Next: signed PR/CI for these
  private helpers, then source-snapshot/reprofile integration and scoped safety
  amendment before any runtime activation.
- Signed `d24adc3` pushed and PR #546 opened:
  https://github.com/wa-pis/agent-paranoid-android/pull/546
  Await GitHub CI/protection; do not repeat unchanged local checks or start
  overlapping work. No ordinary per-PR AI review requested. After merge,
  next small step is safe source snapshot loading and evidence revalidation
  against the same bytes before the safety amendment.
- PR #546 CI completed except for a separate GitHub Advanced Security CodeQL
  gate: it flagged the test's intentionally world-readable `chmod(0o644)`
  fixture, not the receipt implementation. Changed the negative fixture to
  group-readable `0o640`, which still violates the owner-only contract;
  focused receipt tests: 4 passed. Next: push this test-only correction,
  require the new exact head's green checks, then merge normally.
- Signed `5f9e0df` pushed to #546. CodeQL also flags group-readable
  `chmod(0o640)` in the negative test. Removed unsafe fixture chmod and
  extracted the same owner/mode predicate for pure tests against metadata
  values; receipt behavior unchanged. Focused receipt tests: 5 passed;
  targeted Ruff and mypy passed. Next: push this correction; wait for all
  checks on the new exact head before normal merge.
- PR #546 head `88eb4cc9f17eec32bb78f5a47a7a5a2ca6e01b77` was verified
  signed by GitHub; 37 applicable checks passed, four intentionally skipped,
  including both CodeQL gates green. Merged normally on 2026-09-24 as
  `468a701beeed841a0e0db96f2cf91a6f135a7e01`. New branch
  `codex/1-6-source-snapshot` starts from that merge. Added private bounded
  regular-file CSV snapshot loading and same-byte profiling using the existing
  CSV accumulator; revalidation requires exact DatasetProfile evidence match.
  No source-preserving execution or public entry point. Fictional focused CSV
  and snapshot tests: 21 passed; affected pipeline/approval/receipt tests:
  82 passed; targeted Ruff and mypy passed. Next: review source/evidence
  binding in the approval flow, finish scoped safety amendment and its
  independent review before any preservation execution is connected.
  After adding per-field/finalization deadline checks, 91 focused CSV tests,
  targeted Ruff and mypy passed.
- Signed `0887cc4` pushed and PR #547 opened:
  https://github.com/wa-pis/agent-paranoid-android/pull/547
  Await the exact head's CI and GitHub protection. Do not rerun unchanged
  local checks or start overlapping work. No ordinary per-PR AI review.
- PR #547 head `0887cc4855c7eb8ef207f32846292ceacaf6ded2` was verified
  signed by GitHub; all 37 applicable checks passed, four intentionally
  skipped. Merged normally on 2026-09-24 as
  `a8d8c73c4b8bfba4aa5b5341ec3de65dd84b1948`. New branch
  `codex/1-6-safety-amendment` starts there; no policy edit or runtime
  preservation path yet. Next: agree the exact scoped AGENTS.md/SECURITY.md
  and baseline-spec amendment, add executable boundary tests, obtain
  independent AI safety review of the final safety-change SHA before merge.
- Finding 22 was already fixed and merged through PR #541; no duplicate SQL
  work was started. On `codex/1-6-csv-approval-binding`, the private receipt
  boundary now reprofiles the exact source bytes in its approval request and
  requires exact reviewed evidence before either local issuance or receipt
  verification. It rejects multiple sources until explicitly supported;
  no public approval path or source-preserving execution exists. Fictional
  source/evidence-conflict and stale-byte tests: 16 passed; targeted Ruff and
  mypy passed. Next: signed PR/CI for this private guard, then continue other
  approved work while the scoped policy wording awaits user confirmation.
- Signed `0af394e` pushed and PR #548 opened:
  https://github.com/wa-pis/agent-paranoid-android/pull/548
  Await exact-head CI/protection; do not rerun unchanged local checks or start
  overlapping work. No ordinary per-PR AI review.
- PR #548 exact head `0af394eb0a78df384a0515c2e7f5561f6c88bfbf` was
  verified signed by GitHub; all 37 applicable checks passed, four intentionally
  skipped. Merged normally on 2026-09-24 as
  `e87eeedd99b8c21205f0a58b20ab20b6d74a5c72`. The receipt-bound CSV
  evidence guard is on main; source-preserving execution remains disconnected.
  Next: finish the explicit scoped safety-policy amendment and independent
  safety review, or advance another unblocked client requirement while owner
  approval of exact policy wording is pending.
- Offline installed-package A/B for finding 22 used only the reviewed current
  `tests/test_sql_query_source.py` boolean/forbidden-function selections and
  fictional temporary SQL; no product monkeypatch, DB, API or private data.
  Baseline installed public 1.5.0 (query-source module SHA-256
  `8489b216e11405b8e15949b624b88eb6e9d97a286e08d7e85146aef14066500a`)
  failed all eight permitted PostgreSQL/Trino boolean cases and passed both
  forbidden-function controls. Offline wheel built from exact candidate source
  `0af394eb0a78df384a0515c2e7f5561f6c88bfbf` (wheel SHA-256
  `7bb8aab4a47bf793bd637be53cde14e9092c69188375f4d17d8f6c7c5e54de8a`)
  passed all ten. Both imports resolved to separate installed targets; shared
  development dependencies included sqlglot 30.13.0. Wheel metadata still
  says 1.5.0; this is interim installed-wheel parser evidence, not clean-env,
  database integration or final 1.6.0rc1 acceptance. Next: retain this
  result for the final candidate matrix; do not rerun unchanged checks.
- Finding 20 installed-package quickstart failure replay used the public
  `TEST_DATA_AGENT_MAX_INPUT_ROWS=1` limit on the doctor's fictional two-row
  fixture, without product monkeypatch, external services or private data.
  Verified separate import roots: public 1.5.0 baseline at
  `/private/tmp/apa-client-acceptance.xrueHB/baseline-1.5.0` returned generic
  `invalid_input` and exit 2; interim candidate wheel from exact source
  `0af394eb0a78df384a0515c2e7f5561f6c88bfbf` at
  `/private/tmp/apa-sql-ab.EEQv6D/candidate` returned structured doctor JSON,
  ten available Python/dependency/extra checks, `quickstart=failed`, bounded
  `local generation failed`, and exit 1. This is local quickstart-failure
  evidence only, not a Parquet-capability failure, clean dependency install,
  client-probe execution or final 1.6.0rc1 acceptance. Next: obtain a safe
  isolated Parquet-capability failure replay, or advance another approved
  requirement; retain this A/B for the final candidate matrix.
- `TEST_DATA_AGENT_MAX_OUTPUT_BYTES` at 4096 and 16384 also failed the
  quickstart, so it cannot isolate the Parquet capability in this fixture;
  neither run is claimed as capability evidence. The acceptance-note edit
  passed `openspec validate selective-source-transformation --strict` and
  `git diff --check`. No runtime code changed or repeated gate suite ran.
- Private CSV mapping slice: declared approximate FLOAT text now
  normalizes through the same snapshotted mapping loader, rejects
  non-finite/overflow/underflow/ambiguous text, and detects source-key
  collisions after conversion. Exact financial DECIMAL still has no coercion
  path; no public execution or preservation permission was added. Fictional
  focused tests: 56 passed across mapping parser/loader; Ruff, targeted mypy
  and strict OpenSpec passed. Next: push a focused signed PR when GitHub is
  reachable; keep separate Parquet unknown-metadata compatibility choice
  pending user answer. No per-commit AI review.
- Signed `7648ead` pushed as PR #549, focused approximate-FLOAT CSV mapping
  and accumulated finding 20/22 acceptance evidence. Initial exact-head CI
  wheel checks failed the unchanged 256 KiB wheel budget: 262214 bytes versus
  262144 allowed (all four Python compatibility jobs and wheel smoke). No
  budget was raised. Removed redundant type checking and shortened private
  parser docstrings without changing numeric acceptance; local rebuilt wheel
  is 262114 bytes. Focused mapping tests: 56 passed; Ruff and mypy passed.
  Next: signed correction on the same PR, then require its fresh green CI;
  do not merge the failing head or request ordinary AI review.
- PR #549 corrected head `426e3084e4c3803d7d18f4fe2ef85f98c05db388`
  passed all 37 applicable CI/Documentation/Security/Containers checks;
  four release/docs-deploy-only checks skipped. All four Python wheel
  compatibility jobs and wheel smoke passed under the unchanged 256 KiB
  budget; GitHub verified the SSH signature and reported normal merge clean.
  No ordinary AI review was run. PR merged normally on 2026-09-24 as
  `1e366102d99ab0f76c44421327f59af7ca259a1c`; no tag or publication.
  Next: advance approved client and transformation work; Parquet unknown
  metadata public-schema choice and scoped preservation safety amendment
  still await explicit owner decisions. Existing 256 KiB wheel budget leaves
  only 30 bytes for this local build, so future feature work must either
  reduce packaged weight or obtain an explicit budget revision, not silently
  raise the limit.
- User approved revisiting the project wheel-size ceiling. Set the compressed
  wheel regression ceiling to 512 KiB, with an exact-boundary test; retain the
  separate optional dependency ceilings unchanged. This is a packaging budget
  adjustment, not a data-safety or runtime-budget change. Focused installed-
  package tests: 8 passed; Ruff, strict OpenSpec and `git diff --check` passed.
  Next: submit the signed change through ordinary PR/CI.
- Signed `595ee991ecd1dcc3d538498e032eafa4f5ed36cc` became PR #550;
  GitHub verified its signature, all 37 applicable checks passed (four
  publication-only checks skipped), and normal merge completed on 2026-09-24
  as `c03ae676e3b160bb2f68cefc44aaed5ef20ab803`. No release tag or
  publication. Next: continue the approved client/transformation scope from
  merged main; retain this outcome as acceptance evidence without a
  progress-only PR.
- Finding 25 next slice: traced saved-spec `generate` flags through CLI,
  Python bundle, generation, business rules, output spec and manifest.
  The CLI previously parsed mode/ratio then omitted both on the spec path;
  omitted flags now retain saved settings, explicit negative/mixed and
  ratio overrides reach the effective spec, and profile/CSV defaults remain
  valid/0. A saved nonzero ratio with explicit valid/edge/load_test and no
  ratio override currently fails closed pending the owner's precedence
  answer; supplying `--invalid-ratio 0` works. Fictional tests cover five
  modes, ratios 0/1, rows, spec, manifest, report, exit and Python copy
  isolation. This is not yet final finding-25 acceptance: fractional ratios,
  deterministic replay, intentionally invalid Parquet and installed-RC
  before/after remain. Focused CLI/workflow/rule/docs tests: 231 passed;
  Ruff, targeted mypy, strict OpenSpec and diff check passed. Next: sign a
  PR, then settle remaining precedence without changing the safety boundary.
- Signed `74fc41d90a7853907e87d91ae81369d93ee4db2e` became PR #551.
  GitHub verified its signature; all 37 applicable checks passed, four
  publication-only checks skipped. Normal merge completed on 2026-09-24 as
  `cc734a940fa16eb14c834a286fd8e734428254b6`. No tag/publication and
  no ordinary AI review. Next: resolve the explicit-valid/saved-ratio choice,
  complete finding-25 fractional/negative publication parity and isolated
  candidate replay; carry this progress note with the next substantive PR.
- Finding 24 typed Parquet work in progress: spec-backed bundle, single-file
  and agent writers now receive declared field types. Dates/timestamps are
  converted to Arrow temporal types; consistent timezone offsets, nullable
  and all-null/empty fields preserve physical schema. Mismatched types or
  mixed offsets fail before publication with bounded errors; the old
  untyped writer no longer silently stringifies mixed columns. Exact DECIMAL
  and the final intentional-invalid Parquet mode policy remain separate work.
  Affected writer/workflow/agent/CLI/docs tests: 233 passed; Ruff, targeted
  mypy, strict OpenSpec and diff check passed. A new fictional installed-CLI
  probe checks physical Arrow schema and typed readback. Public installed
  1.5.0 baseline failed only its `created_on` physical-type assertion
  (`string`, expected `date32[day]`); current source tree passed. Offline wheel
  built from main `cc734a940fa16eb14c834a286fd8e734428254b6` plus this
  worktree's edits (wheel SHA-256
  `631c32e3c02e7a079bf09e7b94a72eeb560d12977e2db26073b500e187a1f7da`)
  installed under `/private/tmp/apa-parquet-ab.hznvEt/candidate`; the same
  fictional CLI probe passed with a verified separate import root. This is
  shared-dependency interim wheel evidence, still version-labelled 1.5.0,
  not a clean-env or final-RC acceptance. Intentionally invalid Parquet
  policy approval and exact DECIMAL remain pending. After an added existing-
  artifact rollback case, 119 affected writer/workflow/CSV/client/docs tests
  passed; Ruff, targeted mypy, strict OpenSpec and diff check passed. Next:
  preserve the signed change as a draft PR for exact-head CI, but do not
  merge before the invalid-mode policy choice; do not claim full finding-24
  closure.
- Milestone local offline gates for the uncommitted Parquet candidate:
  `pytest -m 'not integration'` initially returned 1704 passed, 10
  deselected and two release-test subprocess failures because macOS system
  Git requires an unaccepted Xcode licence. Both failing tests passed when
  rerun with `/opt/homebrew/bin` first on PATH; no product change was needed.
  Full Ruff, package mypy (118 source files), strict MkDocs build, strict
  OpenSpec and diff check passed. This is not exact-commit CI or final RC
  acceptance. Next: run exact-head draft-PR CI and await invalid-mode Parquet
  policy choice before merge; do not repeat local gates unchanged.
- Exact DECIMAL ceiling selected for 1.6.0rc1 by owner-delegated decision:
  38 base-ten digits with scale
  0..precision, matching Arrow decimal128 and required fictional DECIMAL(20,2)
  and DECIMAL(38,16) examples. decimal256/76-digit support is deferred; values
  beyond this ceiling fail closed without FLOAT conversion or implicit rounding.
  A private exact integer-units parser/constructor and fictional boundary tests
  are staged in a dependent worktree; this does not yet provide end-to-end
  profile/generation/formula/export support or preservation authority. Twelve
  focused tests, Ruff, focused mypy, strict OpenSpec and diff checks passed. Next: carry
  precision/scale through a typed field contract and deterministic generation,
  then test Arrow readback; leave formula rounding as a separate decision.
- Added private exact seeded DECIMAL sampling from explicit inclusive textual
  bounds using integer units and Random.randrange; no float, source-row input,
  public field type or transformation execution. Rejects inexact/reversed
  bounds with value-free errors. Fifteen fictional focused tests, Ruff and
  focused mypy passed. Next: connect the exact representation to a complete
  typed field/generator/validator/writer path before exposing DECIMAL publicly.
- Dependent exact-DECIMAL slice now threads an explicit `decimal_range` through
  DatasetSpec 1.1, deterministic generation, schema validation, CSV/JSON,
  PostgreSQL NUMERIC and Arrow decimal128 exports. Versionless/1.0 specs retain
  legacy semantics. Fictional CLI proves DECIMAL(20,2) and DECIMAL(38,16)
  physical Parquet types and exact readback without float. Sensitive range and
  active constraints on DECIMAL entities fail closed; source profiling,
  financial formulas, preservation, clean-wheel and private acceptance remain
  unfinished. Full source-tree non-integration gate: 1730 passed, 10 deselected
  after updating two explicit schema-version assertions. Ruff, package mypy,
  strict MkDocs, strict OpenSpec and diff checks passed. Generated JSON Schema
  and contract fixtures were refreshed using the source checkout. An interim
  wheel built from this uncommitted worktree is 265978 bytes (<512 KiB), SHA-256
  `c9f5d4e4ea4bde7472fa55bed9313de0f299038a9cc18ff3df990cd8bd15c320`;
  separate --no-deps install passed the fictional CLI Parquet exact-readback
  probe with verified import root. Wheel still advertises 1.5.0 and uses shared
  development dependencies: not final 1.6.0rc1 clean acceptance. Next: finish
  direct exact-profile evidence and formula rounding, then arrange a PR after
  draft #552 resolves; do not rerun unchanged gates or claim finding 23 closed.
  Subsequent writer parity change accepts canonical exact decimal CSV text for
  PostgreSQL/Parquet export, rejecting injection and excess scale. Its 28
  affected tests, focused mypy and Ruff passed; the wheel and installed CLI
  probe above were rebuilt/replayed after this change. The 1730-test full gate
  preceded only this focused writer change and test additions.
- Declared-type profile slice: Parquet decimal128 and PostgreSQL/allowed-query
  numeric(p,s) now retain metadata-only precision/scale; no source values,
  exact extrema, added SQL permissions, or new DB calls. Direct inference of a
  runnable DECIMAL spec fails until the operator supplies reviewed exact bounds.
  Bare SQL numeric remains the existing approximate FLOAT path and is named as
  such in docs. Fictional Parquet, fake-driver PostgreSQL/Trino-query and
  contract focused tests: 92 passed. Full local non-integration gate: 1734
  passed, 10 deselected; Ruff, package mypy, strict MkDocs, strict OpenSpec
  and diff checks passed. A Trino query fixture with declared decimal(12,2)
  now correctly requires reviewed bounds instead of implicit FLOAT; its
  allowlist/no-SELECT-star checks remain in place. Next: cover CSV companion
  type/null/format metadata and decide exact formula rounding before claiming
  finding 23; no installed-RC, private or live-DB acceptance yet.
- Exact DECIMAL range enforcement: schema validation and typed Parquet now
  reject well-formed values outside reviewed inclusive `decimal_range` bounds;
  PostgreSQL SQL export inherits the schema check. Direct Parquet rejection
  preserves an existing artifact. Fictional focused checks: 61 passed across
  decimal, writers, SQL export, safety and Parquet acceptance; Ruff and focused
  mypy passed. `uv run` could not initialize its user cache in this sandbox,
  so checks used the existing project venv directly. Next: complete CSV
  companion type/null/format metadata; formula rounding remains a separate
  product decision. Do not infer preservation authority or final acceptance.
- Dependent draft PR #564 targets draft #552; its original exact SHA
  `c2c2911b4cc78e934ba47dfec49b4d5f0e037f1c` passed all 37 applicable
  CI checks (four publication-only skips). Independent AI safety reviewer
  Schrodinger, 2026-09-25, read-only scope `safety.py` DECIMAL paths and focused
  call sites/tests, found a high-severity numeric-string privacy bypass on that
  SHA: fictional phone/card-like fixed DECIMAL bounds and values could reach
  output. This is AI review, not human approval; evidence is on PR #564.
  Local follow-up rejects sensitive-looking bounds and native/CSV DECIMAL
  values, including SQL export with optional privacy reporting disabled. New
  fictional negative tests plus control passed (33 affected tests); full
  non-integration gate 1738 passed, 10 deselected; Ruff, package mypy (119
  files), strict MkDocs, strict OpenSpec and diff check passed. Next: sign and
  push safety correction, rerun exact-head CI and independent AI review of
  changed scope; do not merge #564 until #552 and owner decisions resolve.
- Independent AI re-review by Sagan (self-reported “Moth”), 2026-09-25, of
  exact SHA `e36b4ffd05a353234d3d4537c21b57a64398c31d` found the prior
  finding only partially fixed: decimal-point and scientific-notation forms
  could hide recognizable card digits. This remains AI evidence, not human
  approval. A further local correction canonicalizes bounded DECIMAL values
  before checking whole/fraction/combined digits, rejects excessive exponents
  without expanding them, and adds `.00` and scientific-form negative tests.
  Thirty-five affected tests, then a full 1740-passed/10-deselected
  non-integration gate, package mypy (119 files), Ruff, strict OpenSpec and
  diff check passed.
  Next: sign/push this correction, require fresh exact-head CI and independent
  AI safety re-review; no release or merge claim.
- Signed draft PR #564 head `aed538ab397c915ecd10b578fdc80da36bca4e56`
  passed 37 applicable checks (four publication-only skips). Independent
  read-only AI reviewer Euclid (self-reported Kepler), 2026-09-25, found no new
  issue in the corrected DECIMAL safety scope. This is AI evidence, not human
  approval; full review chronology and disposition:
  https://github.com/wa-pis/agent-paranoid-android/pull/564#issuecomment-5826458339.
  Local exact-head gate: 1740 passed, 10 deselected; Ruff, mypy (119 files),
  strict OpenSpec and MkDocs passed. Draft PR remains unmerged and depends on
  draft #552 and its intentionally-invalid Parquet decision.
- Owner delegated the RC precision-ceiling choice on 2026-09-25. Decision:
  retain 38 base-ten digits/Arrow decimal128, scale 0..precision. Requested
  DECIMAL(20,2) and DECIMAL(38,16) cases are covered; 76-digit/decimal256
  support is deferred. Above-cap input rejects without FLOAT conversion,
  implicit rounding or publication. This resolves only the precision-cap
  question, not numeric-content/privacy policy or formula rounding.
  OpenSpec plan, design and requirement now record the decision; no runtime
  code or safety boundary changed. Next: settle the separate numeric-content
  decision and #552 Parquet policy before merging #564; continue independent
  source-free work meanwhile. Do not repeat unchanged full gates.
- Signed `2d8a793b45935cb8cc2a4e22f8d0387ca7d00b1e` pushed as draft
  PR #552; GitHub verified the signature. Its exact head passed all 37
  applicable checks; four publication-only checks skipped. PR remains draft
  and unmerged because the intentional-invalid mixed/negative Parquet
  publication choice is pending. No ordinary AI review, tag or publication.
  Next: apply the owner's choice to this PR, rerun changed-scope checks and
  exact-head CI, then consider normal merge; do not restart unchanged gates.
- User selected full rejection for intentionally invalid mixed/negative
  Parquet values rather than a separate invalid-row file. The existing typed
  writer already rejects incompatible values before atomic publication; a
  new two-entity regression covers both modes, prior-output preservation and
  cleanup of partial staging. Documentation records the Parquet-specific
  exception to controlled-invalid publication. Next: run focused checks,
  submit a signed #552 update, then require its fresh CI before merge.
- Finding-10 query-source follow-up on `codex/1-6-query-temporal`: reproduced
  missing date/timestamp bounds on both PostgreSQL and Trino fictional query
  profiles (four aggregate-to-generation cases failed on baseline). Added
  non-sensitive min/max to the existing column summary, no extra statement or
  source-row read; sensitive-name, all-null, malformed and timezone-mismatch
  controls fail closed or omit unsupported evidence. Seventy-three focused
  tests, Ruff, targeted mypy, strict OpenSpec, strict MkDocs and diff check
  passed. Next: save signed local commit, then submit PR after #552 closes;
  no live DB or final installed-candidate evidence.
- Signed local `6776395` contains the query temporal fix. An inspected offline
  probe (SHA-256 `0759bd53c29ab1e04cbe17922d31be7b6660e3bf529ad8fcd894ad89d771ab3c`)
  ran against separately installed public 1.5.0 and a wheel from this commit
  (SHA-256 `0071d5f87cdd33c95b36689ae75811beb4b093da2d6e923777bf078e59e37da6`).
  Baseline: four date/timestamp cases without ranges, bounds or in-period
  output; candidate: four typed ranges and in-period seeded output. Both:
  three fake calls per case. Import roots verified. Shared dependencies and
  interim 1.5.0 metadata limit the claim; no real DB or final RC acceptance.
  Next: preserve this evidence in a docs commit; submit a PR only after #552
  closes, then run exact-head CI without repeating unchanged local tests.
- Safety follow-up before push: the first local query-bound implementation
  checked output names only. A real authorization-path regression proved
  `birth_date AS event_day` requested and retained the sensitive minimum and
  maximum on both adapters. No PR or publication used that SHA. The local
  correction tracks only direct projections from non-sensitive source fields;
  any sensitive query source, sensitive output or derived expression suppresses
  bounds. Eighty-one affected tests, Ruff and targeted mypy pass. Previous
  installed candidate-wheel evidence is historical, not safe acceptance.
  Next: signed correction, rebuild exact wheel, replay alias-negative and
  ordinary date/timestamp cases before opening any PR.
- Signed correction `39b27fee0af980aacb3e77dc9e392350c98ef817` passed
  81 focused tests, Ruff, targeted mypy, strict OpenSpec and strict MkDocs.
  Installed-wheel replay with inspected probe SHA-256
  `5b46ed269b90317ca3bec1c75607f374f6fdc4a1441de1560cf70ba9d08b032c`:
  public 1.5.0 had no ranges; superseded local wheel exposed ranges for four
  sensitive alias/filter cases; corrected wheel SHA-256
  `496e766f4d788dc0bc8ed00fec5f2006fafd4d36e1b379d5b70d32300d072b40`
  retained four ordinary date/timestamp ranges but suppressed all four
  sensitive cases. All used three fake calls, verified separate import roots,
  no live DB. Next: retain this evidence in a signed docs commit; hold PR
  until #552 closes. Exact RC package and private acceptance remain unverified.
- Finding 18 diagnostic slice: two fictional regressions first failed because
  unsupported formula errors echoed an input literal via `ast.dump`, while
  malformed syntax kept an input-bearing `SyntaxError` in exception context.
  Rejections now use fixed, detached messages without changing the permitted
  expression grammar. Twenty-seven focused business-rule tests passed.
  `ROUND` execution, exact DECIMAL/null/rounding semantics and private client
  formula acceptance remain unimplemented/unverified. Ruff, targeted mypy,
  strict OpenSpec and diff checks passed. Next: retain a signed local commit,
  then queue after the earlier draft PR; no ordinary AI review.
- Independent finding-25 fractional-ratio evidence on isolated main worktree:
  fictional 200-row spec with two eligible fields at `mixed/0.25`, seed 31,
  produced 54 intentionally invalid integer cells and 50 intentionally
  invalid boolean cells out of 400 eligible cells. Two bundle runs wrote
  identical rows and effective manifest settings; the input spec stayed
  unchanged. A fictional direct-CSV source at the same ratio/seed likewise
  reproduced its rows and effective settings. Focused tests: 2 passed, Ruff
  passed. This does not prove an exact 25% quota: generation is per-field
  probabilistic. Existing tests expose exit inconsistency: spec-based
  mixed/negative returns 1 for intentional schema-invalid output, while
  direct CSV/profile paths return 0. Do not claim finding-25 closure or
  silently change exit semantics without expected-versus-unexpected failure
  accounting. Next: settle/report controlled-invalid status semantics and
  replay installed candidate; retain the separate saved-valid precedence
  decision.
- Finding-20 Parquet doctor JSON regression on the same isolated worktree:
  an injected fictional capability failure after successful imports and
  quickstart retains the dependency, extra and quickstart checks, returns
  `ok=false`/exit 1, and reports a bounded capability failure without secret
  text or reinstall advice. Three focused tests (this case plus both
  fractional-ratio cases) and Ruff passed. This is local dependency-injection
  evidence, not a fresh installed-package or real Parquet failure replay.
  Next: carry the focused regression with the next substantive client-fix PR;
  keep PR #552 draft until the invalid Parquet publication policy is chosen.
- Installed finding-20 capability replay used an inspected, isolated shim
  (SHA-256 `524de7c6bcf69b0245d045927ed87f0bf8bec00412cacc7445ebcf97d8797dc2`)
  that fails only `pyarrow.parquet.read_table`, never product code. Verified
  public 1.5.0 and interim typed-Parquet candidate import roots both returned
  structured JSON with quickstart/extra available, Parquet capability failed,
  `ok=false`/exit 1, no fictional token and no reinstall advice. The earlier
  output-budget attempt failed before quickstart and is not capability
  evidence. This narrows finding 20; no real fault or final RC was tested.
  Next: preserve the regression/evidence for final installed-RC replay; do not
  rerun unchanged baseline/candidate checks.
- Finding-25 installed-CLI A/B: new fictional test verified the actual import
  root, 12 generated rows, invalid integer-cell types, manifest effective
  `negative/1` settings, invalid report and unchanged input spec. Public 1.5.0
  failed because amounts remained integers; separately installed wheel from
  `76b2806` passed. Source-tree test passed. Wheel SHA-256
  `07c1e6747273070d4d545de1f1c99f97803eee5d95773b66996d57ebaa6e04d7`;
  probe SHA-256 `e54817f6d4a6ad1aabe97d3315f18e060983810b3c3232db145e9bcfa852cf1d`.
  The test deliberately does not assert the unresolved controlled-invalid
  exit-code policy. Shared dependencies and a 1.5.0 version label mean this
  is interim candidate evidence, not a clean install or final RC. Ruff,
  strict OpenSpec and diff checks passed. Next: signed local commit; keep
  saved-valid precedence and invalid Parquet decisions pending owner input.
- Finding 17 independent PostgreSQL table-cost slice: fictional two-table,
  four-column profile (three numeric) made 15 aggregate/metadata statements
  before the change, 16 with one explicitly allowlisted category. Numeric
  shape queries already returned row/non-null/distinct counts, so the profiler
  now uses that same bounded query as the summary instead of querying again.
  Counts fall to 12/13 respectively; logical table-aggregate requests fall
  from nine to six without a category. No raw rows, new SQL permissions,
  budget increases, live connection or source values. Baseline regression
  failed at 15/16 versus the asserted 12/13; after the change 39 focused
  PostgreSQL profiler/query/temporal tests passed. Ruff, targeted mypy,
  strict OpenSpec and diff checks passed. Signed local commit `547bfd5`
  retained for sequential PR after the earlier draft. Actual scanned bytes,
  latency, Trino table costs and final installed-RC behavior remain unverified.
- Same finding-17 query-source path (PostgreSQL and Trino): two numeric columns
  redundantly ran summary and shape aggregates. Their shape query already
  returns row/non-null/distinct counts, so the profiler now consumes it once.
  The fictional three-field regression failed on the old 7/8 statement counts
  and passes at 5/6 without/with one explicitly authorized category. Source
  allowlists, SQL shape, result validation and statement/scan budgets are
  unchanged; no row samples or live connections. Fifty-one focused query
  source/adapter/profile tests passed. Ruff, targeted mypy, strict OpenSpec
  and diff checks passed. Next: signed local commit for a later sequential PR;
  final installed-RC and live cost remain unverified.
- Finding 13 isolated CSV inference fix: fictional 4-parent/100-child input
  with all children linked previously selected an unrelated same-table key on
  an equal-confidence tie. Exact field-name match now wins that tie. The same
  fixture with 75 linked children yields no inferred parent link. This does
  not preserve source orphan rates or alter privacy policy. Focused checks:
  35 tests, changed-file Ruff and strict OpenSpec passed. Next: signed PR and
  exact-head CI, then final installed-RC replay.
- The inference fix passed all applicable PR #553 checks and merged normally
  on 2026-09-25 as `b737bbf4f79e386af4ac79458e6a1e7cf8a42b1e`; no AI
  review, release tag or publication. A separate fictional regression now
  checks declared 4-parent/100-child generation, stable row counts and zero
  orphan keys; undeclared domains remain separate. This does not prove source
  orphan-rate fidelity. Focused identifier/pipeline tests: 36 passed; Ruff,
  strict OpenSpec and diff check passed. Next: signed PR/CI for this acceptance
  check, then final installed-RC replay.
- The declared-link check merged through PR #554 after green applicable CI on
  2026-09-25 as `548ec31810c5392dbc07dc3c867f0c082fbed51a`; no release.
  Preparatory safety fix on current main: five fictional tests reproduced direct
  and unmatched-preserve acceptance for fields with sensitive name/semantic type
  but `sensitive=false`, plus false review display. The shared validator now
  rejects both preservation paths and the review shows effective sensitivity.
  No source-preserving execution or policy exception was enabled. Focused
  policy/approval/receipt tests: 55 passed; Ruff, targeted mypy, strict
  OpenSpec and diff check passed. Next: independent read-only safety review of
  the exact signed head, then PR/CI; policy amendment remains a separate gate.
- The independently reviewed safety fix merged through PR #555 on 2026-09-25
  as `ba2f9d20916e2fc836a0233f6628b53da4a289d6`; its AI review is
  [recorded on that PR](https://github.com/wa-pis/agent-paranoid-android/pull/555#issuecomment-5825635065)
  and is not human approval. This SQL-cost branch integrated main without
  changing its two profiler fixes. Combined focused PostgreSQL/query-source/
  Trino query-builder tests: 85 passed; changed-file Ruff, targeted mypy,
  strict OpenSpec and diff check passed. Next: signed merge commit, then one
  SQL-cost PR with exact-head CI. No live scan-cost or RC acceptance claimed.
- PR #556 merged its bounded SQL-cost reuse through normal green CI on
  2026-09-25 as `aebb40a734032060c14e9a4965be46ae2c247d23`. This
  finding-25 test branch has now integrated that main state; its fractional
  and installed-CLI evidence above remains separate from the unresolved
  controlled-invalid exit policy and Parquet publication decision. Next:
  focused checks on this integration, then a small signed test-only PR.
- PR #557 merged the fractional-mode and installed-doctor acceptance tests
  after 37 applicable green checks on 2026-09-25 as
  `29bf7074ad8a4b5cc8bb1ba7c496aa10b3a82c13`; four publication-only
  checks were skipped. No runtime policy or release changed. This formula
  diagnostic branch integrated that main state; next: focused checks, then a
  signed PR for the fixed error-boundary regression.
- PR #558 merged the formula-error redaction regression after 37 applicable
  green checks on 2026-09-25 as `8abe16f7de0627fd9189ceaceeef1004e057b577`;
  four publication-only checks were skipped. The query-temporal branch has
  integrated this main state and retained both the temporal-bound safety
  guard and the bounded numeric-query reuse. Eighty focused temporal/query-
  source/adapter/builder tests, Ruff, targeted mypy, strict OpenSpec and diff
  check passed. No final-RC or live-DB claim.
- PR #559 merged the narrow active-docs audit on 2026-09-25 as
  `4b2733744c14c837a65e548f3b4256f8fd83c9e8`. It found
  two stale claims calling historical 1.0.0rc6 current; the pilot now names
  stable 1.5.0, and release guidance labels RC6 historical. A planned-only
  1.6.0rc1 section records safety/review gates without claiming readiness or
  authorizing stable 1.6.0. Strict MkDocs and OpenSpec validation passed.
  The query-temporal branch has no code overlap with draft PR #552; its earlier
  hold was sequencing, not a technical dependency. Next: rerun focused checks
  on the integrated head and submit its own signed PR; keep #552 draft until
  the invalid-Parquet publication decision. No source-row or live-DB claim.
- PR #560 merged the safe SQL query-date bounds after 37 applicable green
  checks on 2026-09-25 as `b50885a95e76aa118a8efbef33523f8846b2eb94`;
  publication-only checks were skipped. Finding 1 short-string follow-up adds
  fictional lengths 7 and 8 to the existing deterministic `string_pattern`
  regression, covering the generic branch without a synthetic prefix. This
  tests reachability, not the separate sensitive phone/email/SSN mismatch.
  Nine focused short-string/privacy checks, changed-file Ruff, strict OpenSpec
  and diff check passed. Next: submit the evidence through ordinary CI; await
  the safety-policy choice before changing the sensitive-identifier rule.
- Finding 3 current-main fictional classifier probe: positive fractional
  amount-shaped text classified as `phone`, negative counterpart unclassified;
  phone-shaped integer and Luhn-valid card-shaped secret remained protected.
  This is a local reproduction of numeric ambiguity, not a fix or a blanket
  declassification rule. Next: wait for the explicit field-exception decision
  before changing classifier policy; retain identifier/secret controls.
- Receipt-binding regression slice on current main: fictional local-TTY tests
  reject changed source bytes, policy contents and bytes, mapping bytes,
  evidence serialization and corrupted receipts without reflecting values.
  The existing source-byte check and added rejection cases passed together (9
  tests); changed-file Ruff and diff check passed. No preservation execution,
  safety-policy amendment or new approval authority was enabled. Next: submit
  this focused test-only PR, require exact-head CI, then continue approved
  transformation work; keep draft Parquet #552 separate pending its decision.
- PR #562 merged the receipt-binding regressions on 2026-09-25 as
  `18301a9a8947684c8bb08d0aff5441bae9419981`; GitHub verified the signed
  head and all 37 applicable checks passed (four publication-only skips).
  The fictional C.2 linked-pair local-CLI acceptance test now checks an
  installed package's import root, row counts, FK membership, disjoint key
  domains, four repeated synthetic keys, date bounds and validation. Its
  reviewed source hash remains
  `827e1cd4314b65d2bdf0283f240cebdb3f2ec8755e7f0f536c6c879fbf7ffe44`;
  previous public-1.5.0/interim-wheel A/B is retained as historical evidence,
  not rerun unchanged. Current source: both fictional golden tests passed;
  Ruff, strict OpenSpec and diff check passed. Next: submit a focused PR and
  require exact-head CI. Private C.2, preservation fidelity and final installed
  RC acceptance remain unverified.
- PR #563 merged the fictional linked-pair CLI test as
  `6b9c37b2c8fd2d02d465eba64a8acabf899b934f` after green applicable CI.
  A separate finding-25 fractional `mixed/0.25` CLI acceptance test now covers
  saved spec, safe profile and direct CSV in two deterministic runs each.
  Public installed 1.5.0 fails the spec route (`valid/0` effective settings),
  while an isolated wheel from current main `6b9c37b` passes all three routes
  (four focused tests total). Candidate wheel SHA-256:
  `311619294ca9970e9f600dd3d1582f5bd13835e48796a3888431e0e830fb2403`.
  This wheel is still version-labelled 1.5.0 and uses shared development
  dependencies; not clean/final-RC or private acceptance. New public-contract
  discrepancy: deliberately invalid output exits 1 from spec, 0 from profile
  and CSV, despite all reports being invalid. Asked owner to choose one uniform
  status/exit semantics; no runtime behavior changed. Next: submit the focused
  acceptance test/evidence PR, then implement the chosen exit contract with
  executable parity tests. Do not merge #552/#564 while their separate owner
  decisions remain pending.
- PR #565 merged as `8c0d45126e9c256d48bd20394bfc1f2f0de52b0f` after
  37 applicable checks passed; no ordinary AI review or runtime change.
  Independent private mapping follow-up validates canonical DATETIME strings
  in both inline YAML and local CSV through the shared scalar validator.
  Offset, `Z` and naive strings retain their exact spelling; noncanonical
  forms reject on either mapping side. Fictional focused mapping/CSV tests:
  118 passed including saved-policy round trips; Ruff and focused mypy
  passed. No source-preserving execution or timezone conversion was enabled.
  Next: submit this validation-only slice through signed PR/CI; leave semantic
  timezone equivalence and execution policy for the approved preflight design.
- PR #566 merged the private DATETIME mapping validation on 2026-09-25 as
  `6d3d8e82ce15a0ff674073d981b4940df73d84fe` after applicable green CI.
  The current implementation map now identifies the merged private policy,
  mapping, source-snapshot and receipt boundaries, explicitly without claiming
  a public source-preserving execution path. Strict MkDocs, strict OpenSpec and
  diff check passed. Next: submit this focused map correction; keep #552/#564 draft pending their
  separate publication and privacy decisions. No release tag or publication.
- PR #567 merged the private implementation map on 2026-09-25 as
  `f03c7f435d473ef5547a06db9c7d85a204f0276d` after applicable green CI.
  New fictional preflight probe on merged main: `validate_policy_profile`
  accepted a sensitive field's inline `substitute` entry with identical
  original/replacement values and `unmatched=reject`. There is no public
  source-preserving execution path, so this is a confirmed pre-activation
  safety gap, not observed output leakage. Next: resolve exact typed mapping
  bytes across inline/CSV/domain, reject disguised preservation and test
  value-free errors before enabling any approval/execution route. Do not
  patch inline alone or treat a receipt as sufficient permission.
- Private CSV mapping parser options previously lived outside the saved policy,
  so identical mapping bytes could be interpreted with different delimiters or
  null tokens under the same policy identity. The draft 0.1 CSV declaration now
  carries encoding, delimiter and null token with the previous defaults; both
  in-memory parsing and local loading use only those declared settings. A
  fictional save/load/parse test covers non-default semicolon/null-token replay.
  Focused tests: 153 passed; Ruff, targeted mypy, strict OpenSpec and diff
  check passed.
  This binds parsing semantics to policy bytes but does **not** close the
  sensitive identity-substitution gap above or enable execution. Next: add a
  common typed preflight over resolved inline/CSV/domain mappings and test
  identity, partial composite and null cases before safety review.
- The private approval-material boundary now resolves inline, exact-byte CSV
  and shared-domain scalar mappings against the reviewed field type before a
  local receipt can be prepared. A sensitive non-null source value mapped to
  itself is rejected with a detached, value-free error; CSV `+001` to `1`
  rejects after integer normalization, while null-to-null remains allowed.
  Composite mappings fail closed at this scalar boundary until component-to-
  field bindings are designed; this is not composite-key support. The combined
  policy/mapping/receipt slice passed 163 focused fictional tests, Ruff,
  targeted mypy, strict OpenSpec and diff check. No source-preserving execution
  or public interface was enabled. Next: resolve composite bindings, then add
  full cross-field identity and relationship tests before independent safety
  review and any safety-policy amendment/activation.
- Draft PR #568 opened at signed head `f36b758be4907462113ec1ac803f2fbc799af709`;
  its first exact-head CI was still running at last observation. A local
  follow-up found that even a non-sensitive identity substitution hides
  preservation from the value-free review (`preserves_original=false`). The
  same scalar preflight now rejects every non-null identity mapping, including
  fields otherwise eligible for a separate explicit preserve action; inline,
  CSV and domain cases are covered. The combined 169 focused tests, Ruff,
  targeted mypy, strict OpenSpec and diff check passed. Next: finish the first head's CI,
  send this correction as a new signed head, then require fresh exact-head CI.
  Composite binding and full transformation execution remain unresolved.
- PR #568 corrected exact head `2cd7c975fc83602514b29225947794f80eec24df`
  passed applicable CI and remains draft/open. Independent read-only **AI**
  safety reviewer (tool pseudonym Cicero; self-reported Sentinel) examined this
  exact SHA on 2026-09-25 UTC; this was not a human/GitHub approval. Evidence:
  https://github.com/wa-pis/agent-paranoid-android/pull/568#issuecomment-5827180377
  Two P2 findings remain open: a different but recognizable sensitive literal
  can pass the identity-only substitution preflight; differently offset
  DATETIME strings can represent the same instant. Neither source-preserving
  execution nor public approval is enabled. Do not merge #568 or silently
  decide the sensitive replacement/timezone policy. Next: settle the pending
  component-binding and replacement-safety choices, specify datetime matching,
  add focused executable regressions, then re-review the changed safety scope
  on its new exact SHA and require fresh CI before merge.
- Checked duplicate external mapping labels in the same private approval path:
  `snapshot_identity` already rejects them before returning any receipt, so no
  production change was needed. Added a fictional value-free regression;
  23 focused approval tests, Ruff and diff check passed. `uv run` could not
  initialize its user cache in this sandbox; the existing project virtualenv
  ran the same focused tests successfully. Next: carry this test with the
  substantive safety correction; do not push a test-only revision merely to
  restart CI. The client's monthly-date category suggestion also needs a
  preservation/granularity policy choice; it is not an automatic source-free
  bug fix.
- Inspected and replayed the supplied fictional finding-25 mode probe
  unmodified in separate temporary baseline/source roots (script SHA-256
  `8a860dd6fd9aa515ec192538013bf4702651e3ba4ff93f9d305c5e4e7ecb8653`).
  Verified baseline 1.5.0 and current-source import roots. Baseline lost all
  spec-input mode overrides; current source applied `mixed/1` and `negative/1`
  with different output and matching manifest. The probe mistakes intentional
  exit 1 for absent output and passes invalid ratios to `edge`/`load_test`.
  Supplemental correct invocations passed and recorded `edge/0` and
  `load_test/0`; same CSV bytes as `valid` are not a mode failure here. See
  client-acceptance.md for bounds. Next: include this evidence in final
  installed-RC replay after the controlled-invalid exit and Parquet policy
  choices; do not claim five distinct hashes or private acceptance.
- Inspected and replayed the supplied fictional finding-24/26 Parquet probe
  unmodified in separate installed baseline/interim-candidate roots (script
  SHA-256 `3cd0adfc3832706522b82025b348e7d1a7d46568253eff7c484a465611b47c6e`).
  Public 1.5.0 lost the declared `date` physical type and ignored negative
  mode; the earlier typed-Parquet wheel (SHA-256
  `631c32e3c02e7a079bf09e7b94a72eeb560d12977e2db26073b500e187a1f7da`)
  wrote/read `date32[day]` but rejected negative mixed types without
  publication. The probe returns zero despite printed losses and its all-zero
  null fixture cannot establish honest unknown metadata. See
  client-acceptance.md. Next: resolve intentional-invalid Parquet publication
  and unknown-metadata public compatibility, then replay the final installed
  1.6.0rc1; do not merge draft #552 or claim finding 26 closed.
- Reviewed the remaining supplied doctor/Trino probes without execution.
  Doctor `--fixed` monkeypatches publication and base repeats unchanged
  completed checks; Trino ladder reads a separate analytics query by default,
  copies SQL, prints exception text and always monkeypatches an allowlist arm.
  Neither is safe new acceptance evidence. Next: use only fictional,
  unpatched local tests after the pending auth/SQL product decisions; do not
  connect to a real database or treat these supplied scripts as passed.
- User clarified the intended review workflow: a field marked sensitive is
  transformed; a field explicitly reviewed as non-sensitive may be kept, but
  the data profile must include a system comment explaining the likely meaning
  of each column so the person can make that decision. Planned the bounded,
  value-free comment and its approval-snapshot binding in plan/design/tasks/
  policy-contract; no runtime preservation or declassification was enabled.
  Existing `FieldProfile.sensitive` defaults to false and the Parquet adapter
  can set false without content evidence, so it cannot be treated as automatic
  consent. User decided: `sensitive=false` is a person's explicit decision for
  that column, not a negative detector result; no finding stays unknown. This
  decision is sufficient to proceed with the review contract, not permission
  to override positive/conflicting evidence or to execute preservation. The
  requirement and draft policy contract now state this explicitly. No runtime
  change or check rerun; current worktree retains unrelated in-progress edits.
  Next: implement the bounded review comment and explicit decision separation
  with focused redaction/round-trip tests, then complete the safety-policy
  amendment and independent review before any preservation path is enabled.
- Private review projection now separates `observed_sensitivity=sensitive` from
  `unknown` when no detector fires; the explicit human field decision remains
  `declared_sensitivity`. A bounded, fixed-phrase system comment gives likely
  field meaning from metadata without echoing source values or arbitrary
  semantic labels. Changed evidence/comment bytes alter the approval-material
  snapshot; this is still no local receipt or execution path. Focused policy/
  approval tests: 68 passed; Ruff and targeted mypy passed. Next: implement
  the versioned behavior-profile persistence and wizard display/round trip;
  retain the independent safety review and policy amendment gate before any
  source-preserving execution. PR #568 remains draft with earlier P2 safety
  findings open; do not merge on these review-only checks.
- Agent-use documentation PR #569 adds two portable `SKILL.md` files. Both are
  also included in the wheel from the same repository sources; package install
  does not silently register them with an agent. The transformation skill keeps
  unfinished preservation explicitly disabled. Local wheel and sdist contain
  both skills; installed-wheel bytes match source. Skill validation, focused
  installed-package tests (8), Ruff and diff check passed. Next: require fresh
  exact-head CI for the packaging update before normal merge; no RC claim.
- Exact-head PR #569 container jobs exposed a missing Docker build-context copy:
  Hatch could not find the forced-included `.agents/skills` directory. The
  container context and shared builder now include only those skill files;
  focused container regression checks cover the copy and ignore rules. Next:
  rerun affected tests and exact-head CI; merge remains blocked until green.
- Owner added RC scope for further skill-guided agent use. OpenSpec now records
  version-aware workflow selection and fictional offline acceptance, explicitly
  pending implementation. Bundling both skills is not that acceptance. Next:
  validate this planning change, finish #569 exact-head CI, then triage the
  remaining draft PRs in dependency order; no new agent runtime work yet.
- Owner clarified that both skills target package users, not release operators;
  source-module development is relevant only when a user explicitly requests
  extension. The skills now contain their user workflows and safety boundary
  offline, using installed `--help`/MCP metadata instead of requiring web docs.
  Rebuilt wheel contains both revised files. Next: validate skill format and
  exact-head CI; no transform execution was added.
- PR #552 integrated current `main` while retaining both the Parquet
  regression and newly merged fractional-mode test. The owner's full-rejection
  choice applies when a mixed/negative value is incompatible with declared
  Parquet type; older pending-decision notes above are historical. Next:
  run focused checks on the integrated tree, push the signed merge, require
  fresh exact-head CI, then consider normal merge.
- PR #568 integrated merged `main` in a separate clean worktree; the original
  checkout's unfinished fictional client-acceptance edit was not changed.
  Both progress histories were retained. The merged tree passed 172 focused
  transformation tests, Ruff, targeted mypy, strict OpenSpec and diff checks.
  This is a draft safety-review surface only: the earlier P2 mapping findings
  remain open; no source-preserving execution or receipt
  is enabled. Next: push the signed integration commit and inspect exact-head
  CI; do not merge until the safety questions are resolved and independently
  re-reviewed.
- Draft PR #568 composite-domain preflight now binds each participating field
  to an explicit zero-based tuple component. Every entity using the domain must
  cover the tuple exactly once; mismatched shared types, omitted/duplicate
  positions and any unchanged non-null component reject before approval
  material is prepared. The review shows an opaque domain ordinal and component
  index, not mapping values or private domain names. Fictional inline/CSV and
  cross-entity regressions: 183 focused tests passed; Ruff, targeted mypy,
  strict OpenSpec and diff check passed. This is locally committed validation-only
  work in the isolated mapping worktree; no execution, receipt or preservation
  authority is enabled. Next: finish integration with latest main, obtain exact-head CI
  and resolve the outstanding replacement/timezone safety findings before
  another independent safety review or merging this draft.
- Owner's latest DECIMAL comment indicates a possible documented human
  exception for preserving original values, but does not decide whether an
  explicit `sensitive=false` plus rationale may override positive card/phone
  evidence. The current fail-closed rule remains in force until that exact
  safety choice is confirmed, specified, tested and independently reviewed.
- PR #568 exact head `8e5a97e4ba89627f221f0dc1a7c1d7b4ad9c8a5b`
  completed all 37 applicable GitHub checks successfully; four publication-
  only jobs were skipped and none failed. The PR stays draft. This does not
  dispose of the two earlier P2 AI safety-review findings or authorize source
  preservation. Next: settle the field-level DECIMAL override and replacement/
  timezone semantics, then add executable safety regressions and request one
  independent review of the changed safety scope on its exact head.
- Private policy preflight now requires a bounded, nonblank operator comment
  for direct and unmatched-value preserve actions. The system's value-free
  meaning/sensitivity hint remains separate; the operator comment is private,
  omitted from review/error output, and exact comment bytes are snapshot/receipt
  bound. Missing/blank comments reject before approval material. Fictional
  policy/approval/receipt/mapping/CSV tests: 195 passed; changed-file Ruff,
  targeted mypy, strict OpenSpec and diff check passed. This strengthens a
  private draft only; positive sensitivity evidence still blocks preservation
  and no source-preserving execution is enabled. Next: sign/push this combined
  draft update, require exact-head CI; defer renewed independent safety review
  until the outstanding replacement/timezone/numeric policy findings have a
  complete proposed resolution, avoiding review of every intermediate commit.
- PR #552 merged normally as `d00eee2f0cdfb355c91f87dc1f3dfece8f4fe66d`
  after 37 green applicable checks and the owner-selected whole-export
  Parquet rejection contract. The dependent #564 branch now integrates that
  main state. Merge resolution keeps DECIMAL precision metadata and numeric
  shape in the existing one-query aggregate path for PostgreSQL and allowed
  SQL, preserving temporal bounds and budgets. No numeric-content/privacy
  exception or formula rounding policy was added. On the integrated tree,
  152 focused fake-driver, temporal, Parquet and DECIMAL tests passed; Ruff,
  targeted mypy, strict OpenSpec and diff check passed. Next: push a signed
  draft-PR merge and require fresh exact-head CI; numeric-content/privacy
  choice and safety re-review remain prerequisites to #564 merge.
- User-skill offline checkpoint on merged main `d00eee2`: wheel SHA-256
  `2b8a02ad77f177ed61956c8b0c90e045a4626c044b923186fe43553d922ab18a`
  was installed under a separate import root without network access. Both
  packaged `SKILL.md` files were discoverable. The fictional demo/profile/
  infer/generate/validate CLI route passed with seed 42; `transform --help`
  exited 2 because no transformation command exists. This is partial offline
  acceptance only, not an AI-agent run or final RC proof; details and remaining
  agent-runtime/MCP cases are in client-acceptance.md. Next: keep this evidence
  with a focused documentation PR; test distinct agent runtimes against the
  exact installed RC once the reviewed interfaces exist.
- PR #570 merged the offline skill-checkpoint documentation on 2026-09-25 as
  `cd8410aa25bb93fe5df8feb22e7599dee755d6c4` after applicable green CI.
  It is partial installed-wheel evidence, not agent-runtime or RC acceptance.
- Finding 26: a fictional two-row-group Parquet fixture reproduced false
  `null_ratio=0.0` for two nulls in four rows. The metadata-only adapter now
  sums complete, consistent row-group null counts and reports `0.5`; missing
  statistics remain unmeasured in its private helper. The focused regression
  failed before and passed after the change; 55 adapter/spec tests, Ruff and
  targeted mypy passed. This is not full finding-26 closure: public unknown
  representation, sensitivity and installed-RC replay remain. Next: agree a
  versioned unknown/measured contract before changing that public surface.
- PR #564 exact DECIMAL head `09e05ae317991ddc96e278aa7bdf9239d4530344`
  passed all applicable CI and merged through GitHub as
  `f545d1ef40297893a30134ab30f95bc3fc46eca6` on 2026-09-25. Its
  source-free numeric privacy guard is unchanged since the completed AI safety
  review at `aed538a`; later integration added only an exact CSV companion
  regression. This does not approve source preservation or private acceptance.
  Draft #568 locally merged that mainline with both progress histories retained;
  165 focused policy/approval/mapping/DECIMAL tests passed. Two new executable
  negative tests confirm positive DECIMAL profile sensitivity still rejects
  direct and unmatched fallback preservation. Next: inspect independent read-only
  review of the proposed narrow exception, then amend AGENTS.md/baseline specs
  only with explicit evidence provenance and tests. No preservation execution.
- Independent read-only AI proposal review by Nash (“Boundary Sentinel”),
  2026-09-25, pre-merge `cd38d44`, found that a DECIMAL field with a negative
  profile flag could pass direct/fallback preserve, the schema fingerprint
  omitted precision/scale, and current evidence lacks signal provenance.
  The first two findings reproduced as four and two failing fictional tests,
  respectively. Local draft now rejects DECIMAL preservation by default and
  binds declared precision/scale into the private schema fingerprint; 169
  focused policy/approval/mapping/DECIMAL tests, Ruff and diff check pass.
  Reviewer made no writes or GitHub approval. Next: push integrated draft for
  fresh CI, obtain exact-head safety review of this hardening, then design
  typed evidence provenance before attempting the authorized policy exception.
  AGENTS.md amendment and source-preserving execution remain disabled.
- Exact-SHA independent read-only AI safety re-review by Nash (“Boundary
  Sentinel”), 2026-09-25, of draft #568 `158b7287061cee5f3c31267215cd335ad111a658`
  found no new changed-scope issue in the DECIMAL default deny or shape binding.
  Reviewer ran 52 policy and 42 approval/snapshot tests and fictional forged/
  mutated-profile probes; this is not full-PR or human approval. Evidence:
  https://github.com/wa-pis/agent-paranoid-android/pull/568#issuecomment-5831533019.
  Residual High execution gate: structural policy checks cannot attest source
  type against fixed source bytes. Prior P2 replacement/timezone findings also
  remain open. GitHub CI on this exact head had 36 successes, four release-only
  skips and one running at last check; do not merge or call it green yet.
  Next: wait for exact-head CI without restarting it, design provenance-bound
  classification and resolve prior P2 findings before enabling an exception.
- Draft #568 exact head `158b7287061cee5f3c31267215cd335ad111a658`
  completed 37 applicable CI checks successfully; four publication-only jobs
  skipped. It remains draft. The two older P2 mapping findings were reproduced
  with fictional inline/CSV/domain tests: distinct email-like replacement
  literals and DATETIME strings denoting the same instant passed preflight.
  Owner rejected treating replacement syntax alone as proof of source copying:
  explicit mappings supply replacement literals; no brute-force inference is
  intended. The proposed blanket email-like preflight ban was removed before
  commit. Shared approval preflight now rejects equal offset-aware instants
  before any receipt; no execution path was added. Distinct-sensitive-literal
  P2 still needs disposition consistent with the no-real-PII guarantee.
  Owner initially discussed a simple CSV value-replacement first execution
  slice, still subject to explicit per-field decisions and the existing local
  approval/source-snapshot boundary. Next: run affected mapping/CSV/receipt checks,
  commit/push the timezone correction, get fresh CI and one independent changed-
  scope safety review. AGENTS.md amendment and source-preserving execution
  remain gated on typed evidence and executable end-to-end safety tests.
- Owner rejected the proposed same-type-only CSV `replace` and then clarified
  the intended primitive is an unconditional exact-text replacement table,
  not a typed output-column conversion. `"001" -> "1"` writes literal `1`;
  no FLOAT/DECIMAL parsing, guessed type, cascade or brute-force lookup is
  part of the replacement operation. Whether the table applies globally to
  every CSV cell or only selected columns is awaiting the owner's answer.
  Unmatched-value preservation still requires the separate reviewed safety
  boundary; do not implement or publish a same-type-only path as acceptance.
- Owner further clarified that the input is a table of unconditional text
  substitutions (`true -> false`), not a request for source/target types.
  OpenSpec plan, policy contract and task list now describe literal one-pass
  matching, no implicit coercion, and opt-in bounded local debug output of
  row/column/rule ordinals and match status without values or hashes.
  The owner subsequently chose both separate rules per column and file-wide
  rules. Their conflict precedence is awaiting confirmation. This planning
  update does not enable source-preserving execution. Next: bind the exact-text
  matcher to explicit column decisions and shared trace on fictional fixtures
  under the separately reviewed preservation boundary.
- Added an internal, non-executing exact-text CSV replacement table compiler:
  one left/right text pair per mapping row, duplicate-key and null-pair
  rejection, one lookup returning replacement plus rule ordinal, and `None`
  for unmatched input. It performs no source-row I/O, fallback copy, type
  conversion, output publication or approval. Fictional `true -> false` and
  `001 -> 1` tests: 41 CSV tests pass; Ruff and targeted mypy pass. Next:
  bind each table to its declared scope, then share this matcher with a
  bounded value-free local trace and reviewed CSV execution path.
- Added internal scoped text matching over the compiled tables. A column rule
  affects only its named column; a file-wide rule can match other columns.
  A matching replacement is applied only once, so a replacement equal to a
  different rule's source is not cascaded. Until the owner decides precedence,
  overlap on one cell raises a fixed value-free conflict instead of silently
  choosing a rule. The private match result hides replacement text in repr and
  carries scope plus rule ordinal for future trace. Fictional CSV tests: 43
  passed; Ruff, targeted mypy and diff check passed. A value-free event helper
  now derives row/column ordinals, scope, rule ordinal and matched status from
  the same match result, with no literal passed to the event constructor.
  This is not yet a bounded CLI dry-run or source-row execution. Next: record
  chosen precedence, add bounded CLI trace and reviewed CSV execution behind
  the safety amendment.
- Rechecked the local exact-text slice after the owner's explicit file-wide
  requirement: file-wide and per-column lookup tests pass (43 CSV tests), Ruff,
  targeted mypy and strict OpenSpec validation pass. No output path or source
  preservation was enabled. Next: settle overlapping-scope precedence, then
  implement a bounded value-free local trace using the same matcher.
- Added a private bounded trace summary over the same value-free match events:
  capped event list, total matched/unmatched cells, per-column/scope/rule counts,
  explicit truncation and cell/rule-bucket limits. Forged metadata and limit
  overflow fail with fixed messages. Forty-five focused CSV tests, Ruff and
  targeted mypy pass. This is not a CLI dry-run or source-row execution.
  Next: wire the local debug surface to a fixed approved snapshot after the
  overlap precedence and preservation-policy gates are resolved.
- Draft #568 `3b5cf28040cfb5bce8358de6f1272dee711b55e0` completed 37
  applicable GitHub checks successfully (four release-only skips). The
  subsequent signed trace-summary commit `8f606768653d428c5724210d2db572fc58dea33c`
  was fast-forward pushed to the same draft; its own CI is pending. No AI
  review was requested for this ordinary incremental commit. Next: inspect
  exact-head CI, then continue local CLI debug integration only after the
  matching and preservation contracts are settled.
- Draft #568 `8f606768653d428c5724210d2db572fc58dea33c` completed 37
  applicable GitHub checks successfully (four release-only skips). Focused
  fictional regression confirms the existing local receipt boundary rejects
  a relabelled numeric CSV profile even when policy fingerprint is recomputed
  over the forged profile: `_canonical_request` reprofiles the same source
  bytes and fails value-free. Eleven receipt tests and Ruff pass. This does not
  prove source attestation on any future direct policy or execution route; the
  unresolved review gate remains. Next: retain this regression, then specify
  one canonical approval/execution entry that cannot bypass byte revalidation.
- Draft #568 `3f81d7558238c00815ff1e8e435c0214e2e9dd84` completed 37
  applicable GitHub checks successfully; four release-only jobs skipped.
  Only this draft PR and three unrelated Dependabot PRs remain open. The
  exact-text file/column overlap rule awaits the owner's decision; the
  existing fail-closed conflict remains. Next: bind a future local review and
  execution entrance to `_canonical_request`/fixed source bytes, then prove
  that no direct policy path can bypass revalidation before enabling output.
- Added a private CSV review-preparation entry that derives profile evidence
  from the exact bounded source SnapshotPart it binds into the approval
  request; callers of this entry cannot submit a relabelled profile. Existing
  receipt issue/verification independently reprofile the same bytes. Fictional
  same-source, wrong-source and changed-mapping tests pass with the receipt
  tests (18 total),
  Ruff and targeted mypy pass. No public CLI, receipt issuance or output path
  was enabled by this entry. Next: connect a local read-only review command to
  this entry, then test source/mapping mutation and value-free failure paths.
- Draft PR #564 integrated main through `46cd9cd` without changing the
  source-free DECIMAL privacy guard. Its declared Parquet precision/scale path
  and the newly merged row-group null-statistics path coexist in the same
  metadata adapter. Ninety-one focused fictional adapter, DECIMAL, SQL-source
  and installed-CLI test cases passed; changed-file Ruff, targeted mypy and
  strict OpenSpec passed. Next: sign/push the integration, require exact-head
  CI, and keep the PR draft until the numeric-content exception is settled and
  the changed safety scope independently reviewed. No final RC acceptance.
- Draft PR #564 exact head `2883d95f73f264fd315f0c8c53c249b56adba31a`
  passed 37 applicable GitHub checks. A new fictional installed-root-aware CLI
  CSV regression verifies DECIMAL(20,2) text beyond binary FLOAT precision,
  nullable DECIMAL(38,16) empty cells, saved `dataset_spec.yaml` precision/
  scale/nullability and manifest version/format. The existing bundle already
  carries this companion spec; no new public format or runtime code was needed.
  Sixteen focused DECIMAL tests, Ruff, strict OpenSpec, strict MkDocs and diff
  checks passed. Next: submit this test/documentation delta to the same draft
  PR; retain the numeric-content
  choice and safety review gates. No private data or final RC acceptance.
