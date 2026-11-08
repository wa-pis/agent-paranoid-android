# Progress

## 2026-11-08 — Authorized Design And Implementation Start

The owner requested an OpenSpec for fast linked-table generation and then work.
An isolated worktree/branch preserves unrelated original-checkout edits.
Current work: specify bounded acyclic FK support with a new explicit engine,
then implement and test the deterministic planner before wiring publication.
Only fictional fixtures are permitted. No new release/publication is claimed.

## 2026-11-08 — Linked Streaming Implemented, Final Checks In Progress

The explicit `scalable-relational-v1` policy now admits bounded synthetic-key
DAGs, generates parent-first with original-index seed streams, assigns scalar
FK domains and verifies actual keys/references before publication and streamed
recovery. No parent/key pools are retained. Actual relationship/null counts and
executed utility evidence replace the independent report for linked runs.

Nullable references, integer/string keys, chains, multiple parents, one-to-one,
rejected hypotheses, invalid graphs, rehashed FK/PK tampering, disabled optional
reports, late-child cancellation and shared deadlines are covered. Whole-graph
bounded calibration preserves FK feasibility. CLI no longer passes an absent
business-rule configuration as a nonempty callback. Existing independent
engine/legacy defaults and source/database limits remain in place.

Evidence: `openspec validate scalable-relational-generation --strict` passed;
Ruff and strict mypy passed (168 source files). Focused suite
`test_scalable_relational`, `test_dataset_capacity`, `test_mcp_client_workflow`,
`test_activation_patches`, `test_contract_fixtures`: **86 passed, 1 skipped**
in 24.34 s. Real SDK stdio tests include engine/fingerprint invalidation,
fictional approval and interrupted-completion recovery. These are AI-driven
technical tests, not manual human acceptance.

The isolated branch has only this change. Historical activation patches are
unchanged; an additive reversible public-contract overlay carries the new
engine pattern. Full checks and repeated linked 750k-total-row × 25-column
measurements are still running. Do not treat provisional timings as final.
No new tag, release or manual-acceptance claim is made.

## 2026-11-08 — Performance Evidence And Serial Full-Gate Retry

Nine 750k-total-row × 25-column runs plus six smaller 10k/100k runs passed
mandatory validation. CSV data hashes match across all worker settings within
each size. Three-run medians: 58.70 s (one worker), 42.52 s (two), 30.06 s
(four); four-worker speedup **1.953×**, so the ≥2× target is **not met**.
Data bytes: 172,858,082; conservative four-worker memory upper bound 372.4 MiB.
Raw measurements and caveats are in `benchmark-evidence.json` and `evidence.md`.
Timings vary widely; no isolated-host or cross-platform speed claim is made.

Final forecast review fixed synthetic FK width estimation when a child field
is not explicitly marked as an identifier. Focused generation/capacity checks
on that source: **74 passed, 1 skipped** (16.36 s). Documentation checks:
**54 passed** (3.87 s). Strict mypy and Ruff passed after this correction.

The initial full gate was interrupted after its new-change catalog assertion
failed and an existing Hypothesis provider test exceeded its 200 ms timing
threshold (515.63 ms). The active-change catalog is fixed. Isolated GigaChat
mock tests passed (49 tests, 52.09 s), and the affected property test also passed
under coverage (10.47 s). No provider call, provider behavior change or relaxed
timing threshold was introduced. A complete serial gate retry is now running
without concurrent benchmark/verification processes. Release authorization
and manual human acceptance are still outside this change.

## 2026-11-08 — Full-Suite Memory-History Diagnosis

The serial full gate completed with 4,892 passed / 24 skipped and eight failures
in new direct-library tests: their 1 GiB fixture correctly rejected the shared
coverage runner's earlier RSS high-water at the worker allowance. Coverage was
91.79%; production memory checks were not bypassed. The standalone 1 GiB scale
runs and focused tests passed in fresh processes.

The functional test helper now explicitly budgets 4 GiB for that long-lived
runner. Default engine limits, resource accounting and guard behavior are
unchanged. Real scale evidence remains under 1 GiB. This fixture adjustment and
the long-lived-process caveat are documented; another complete gate must pass
before committing this implementation.

## 2026-11-08 — Initial Scope Verified, Ready For Review

Complete serial `scripts/check_release.sh` passed: **4,900 passed, 24 skipped**,
353.43 s, **91.83% coverage** against the 85% floor. Lint, strict typing,
compilation, license/compatibility policy, privacy/SQL boundary checks,
operational resource checks, schema freshness and quickstart all passed.

The final MCP/CLI help metadata describes both engines and explicit relational
limits. After refreshing its contract fixture and reversible overlay, focused
activation/contract/parser/real-SDK tests passed: **20 passed** in 11.95 s.
Ruff, strict mypy (168 source files) and strict OpenSpec validation passed again.
Historical activation patches remain unchanged; no SQL/source-preserving
execution authority is added. All fixtures and scale data are fictional.

The initial DAG scope is ready for review on `codex/scalable-relational-generation`.
Remaining performance target: ≥2× on a suitable isolated host; measured median
is 1.953× with large timing variation. Before any separately authorized RC,
independent exact-SHA review, manual client acceptance and release gates remain
unchecked. No new release/tag or human-acceptance evidence is claimed here.

## 2026-11-08 — Next RC Authorized

The owner authorized publication of the next RC with Python 3.15 support.
Selected 1.7.0rc3 after verified 1.7.0rc2. Release preparation starts from
main d5143ad8d580b7f5a9f23c9ed0e3ac33521b212a in an isolated worktree.
Fresh exact-main gates/review, Ubuntu hashes, signed acceptance and public
verification remain required. The relational manual client acceptance is
not replaced by SDK tests or historical consent. No tag/publication yet.
