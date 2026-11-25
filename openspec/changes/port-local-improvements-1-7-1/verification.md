# Port Verification — 2026-11-25

## Source And Scope

- Branch: `codex/port-local-improvements-1-7-1`.
- Base: published `v1.7.1`, commit `8aa5d40af2a9f5f15e6572fd2abafdd805df8c9e`.
- Local source: `codex/1-6-parquet-typed` at `26af69043cfd8d46df48ed43e18d5e168d223d3a`.
- The original checkout, branch and all 323 local file hashes remain unchanged.
  [Source inventory](source-inventory.json) records every disposition: 118 adapted
  paths, 130 byte-identical historical evidence files, 74 superseded documentation
  files retained in the original checkout, and the released README retained.
- Historical evidence is isolated under `legacy-evidence/`; its hashes match the
  source snapshot. Previous timings and CSV hashes are not 1.7.1 measurements.
- Package version stays 1.7.1 on this development branch. No tag, push,
  publication, source transformation or real database/provider call occurred.

The port retains DatasetSpec 1.1, exact DECIMAL, reviewed numeric replacements,
capacity forecasts, ordinary/scalable/relational engines, conditional rules,
relational scenarios, configurable inference/entity sizes, utility evidence,
bounded Parquet content/distinct inspection, CLI/MCP error corrections and all
released transformation/session approval boundaries. New tiled generation and
streaming CSV remain explicit options. SQL policy 1.2 tightens alias provenance
without expanding accepted SQL or resource budgets; cache format 10 invalidates
older local profiling results.

## Deterministic Release Comparison

[Comparison](release-parity/comparison.json) and its [probe](release-parity/probe.py)
use independently authored synthetic specifications, seed `170117`, separate
Python 3.11.15 environments and identical shared dependency versions.

- 21 unchanged cases: 849 generated rows and 35 CSV artifacts per side, all seven
  field types and 863 native DECIMAL-cell checks.
- Equal logical/direct rows, typed CSV bytes, saved specifications, validation
  and business reports, result metadata and stable execution statistics.
- All five ordinary modes, native formulas/temporal constraints, DECIMAL formulas
  and aggregates, conditional formulas, unsorted foreign-key hierarchies and
  relational scenarios are represented.
- Both released scalable engines retain worker/batch invariance: eight checks
  compare workers 1/2 and batch sizes 7/19 across valid/edge modes.
- The only manifest difference is newly recording installed DuckDB and the
  corresponding dependency-map hash; generation does not use DuckDB.
- Six separate formula → aggregate → formula permutations demonstrate the
  intentional ordering fix: released 1.7.1 rejects them; this branch produces
  the same valid rows for every declaration order.
- Replaying all 27 target cases after the final fixes exactly matches the saved
  target evidence. Temporary generated CSV/rows are removed in `finally`.

## Executable Gates

- Final combined suite: **6,236 passed, 25 skipped**, zero failures/errors,
  340.11 seconds; statement coverage **92.24%** (required floor: 85%).
- Ruff: `src tests scripts`, pass.
- Mypy: all 174 production Python modules, pass.
- `compileall`: `src tests scripts`, pass; bytecode written outside the checkout.
- Both generated JSON schemas match the checked-in released schemas.
- Dependency compatibility and all 113 installed dependency licenses pass.
- Operational profile/generation/validation resource checks pass.
- Strict MkDocs build and 80 documentation/build tests pass.
- Strict OpenSpec validation and the staged whitespace check pass for active
  code, tests, documentation and new evidence. The byte-identical legacy archive
  is excluded from that cosmetic check: its historical Markdown has five EOF
  blank lines and its patch artifacts have four required/retained context-space
  lines. These nine historical warnings are preserved rather than rewriting
  source-bound evidence.
- Final wheel installs and passes installed-package smoke checks in independent
  `base`, `profiling` and `all` environments, including entry points, packaged
  skills/resources, doctor, demo and CSV/JSON quickstarts.
- The minimum-dependency environment passes 140 profiling/security, workflow,
  business-rule and I/O tests with Faker 25.0.0, Pydantic 2.7.0, PyYAML 6.0.0,
  PyArrow 15.0.0, DuckDB 2.0.1 and NumPy 1.26.4.
- Wheel: 468,957 bytes, below the released 512 KiB ceiling; SHA-256
  `66a0e234892cd6f75ce10459333c27a681a3bb68c782c122043aee54040e0bcf`.

The clean-release baseline first passed 4,929 tests with 25 skips and eight
sandbox-only controlling-TTY failures. Repeating the affected transformation
files with local PTY access passed 217 tests with four skips. The final port
suite uses the same PTY access, preserving the real-terminal enforcement tests.

## Independent Review

Separate agents reviewed shared privacy/source provenance, validators and
calculation order, profiling/native spill, and parallel/streaming publication.
Four concrete defects found during integration were fixed with regression tests:

1. Do not attach temporal metrics when the report disables constraint checks.
2. Bound each exact integer aggregate operand and intermediate result, including
   overflow before later cancellation; preserve integers above 2**53 exactly.
3. Estimate all in-flight tiles before worker/file creation, refusing extremely
   wide strings before allocating them while admitting large narrow datasets.
4. Return a value-free generic resource-limit error from workers instead of
   incorrectly describing every limit as a timeout.

The last fixes were independently rechecked with 22 focused tests. All 177
runtime/policy files match [the frozen manifest](runtime-policy.json), whose
canonical file-map SHA-256 is
`2b2613323ce80115701a7dae211f6c0ce9b8f07bbea7c0932d893dbeb4cfd49c`.
No further actionable findings remain from this review.

## Limits

Local gates use macOS and Python 3.11.15. The existing Python 3.11–3.15 CI matrix
is retained; other Python/OS jobs were not run locally. Live PostgreSQL/Trino,
real providers, isolated prospective activation candidates and genuine human
approval campaigns were not exercised. This branch does not authorize or claim
new public transformation activation or release acceptance.

The 25 suite skips comprise ten disposable live-database cases, one MCP-only
environment, one Linux-only accounting case, four isolated CLI/MCP composition
cases, six prospective preservation negatives, two execute-only destination
cases and one isolated registration-candidate case. These are retained gates,
not newly disabled checks. Four serializer warnings come from tests assigning
the rejected status as a raw string; the corresponding release test also warns.

The 100,000/750,000 × 25-field performance campaigns were not repeated for this
port. Historical results remain source-bound. Corpus/parity tests do not prove
real-world detector recall, and bounded tile admission is not an OS RSS cap.

## Release candidate safety follow-up

Independent review of `204a32405b8edf8ad366d849ff0a5ef9fb0d0c11` found two
release blockers. That candidate and its artifacts are not releasable.

`GenerationBudget.remaining_seconds()` again calls the polymorphic `check()`
before calculating native-work time. A real injected-clock `QueryWorkBudget`
rejects expired requests through both `InvocationGenerationBudget` and
`_McpTransformationBudget`, even while the generation deadline is live.
Configured PostgreSQL and Trino capture refuse before entering the worker
boundary when the request expires after policy checks. All six regressions
failed before the fix and pass after it; the existing clock test now asserts
elapsed-time behavior without requiring a particular number of clock reads.

Native Parquet/PostgreSQL-query/Trino-query transformation profiling no longer
retains unused distinct-digest sets. Distinctness remains unknown rather than
reporting a false exact zero; privacy/type/null counters and bounded samples
remain active. The three native regressions failed before the fix and pass
after it, covering 64/2,048 distinct rows, both row orders and late sensitive/null
evidence. Exact CSV distinct orchestration is unchanged. Neither fix changes
read authority, transformation activation, approval rules or dependencies.

A diagnostic working-tree run passed 272 tests and skipped two across the 13
focused budget/capture/isolation/profiling modules. The skipped cases are
`test_common_mcp_expiry_during_capture_is_typed_and_never_publishes[True-review]`
and `[True-validate]` in `tests/test_transformation_review_regressions.py`, both
with reason `only execute accepts a destination`; those combinations do not
accept destination retention. Ruff and mypy (176 source files) passed.
This shared-working-tree evidence is diagnostic. A final combined run on the
frozen repair files passed 89 tests across the budget, configured SQL capture,
CSV distinct and native-profile regression modules; Ruff and mypy also passed.
The related native source/execute/query/batch/receipt run passed 585 tests and
skipped four opt-in isolated CLI/MCP composition cases. Seven controlling-TTY
cases failed in the sandbox; the selected external-sandbox rerun passed all 12
selected cases, including those seven. No live source or dataset approval was
used. Exact-source review and replacement Ubuntu-artifact acceptance remain
required before any tag or publication; historical evidence keeps its original
identity.

## Replacement candidate qualification — 2026-11-25

Replacement candidate `1.8.0rc1` qualified at exact source
`48538d05ec4d9ab6af3ffa951262703bae66f161`. Fresh exact-source gates,
independent technical AI review and installed Ubuntu-artifact acceptance are
recorded in the [published release evidence](../../../docs/release-evidence-1.8.0rc1.md).
Publication and [artifacts-scope public verification](https://github.com/wa-pis/agent-paranoid-android/actions/runs/45589440125)
completed with all 13 jobs passing. This closes the replacement qualification
requirement above; the diagnostic and historical evidence retains its recorded
source identity and measurements. Candidate `204a3240` and its artifacts remain
unreleasable. The documentation revision and full-scope public verification
are tracked separately; artifacts-only verification does not establish live
guide acceptance. The separate human-review task stays open. Publication grants
no dataset approval or new transformation activation.
