# Client Feedback And Acceptance Plan

Source: the user-supplied anonymized handover archive for 1.5.0, containing the
fix brief and four Python probes. Treat the brief as evidence and proposals,
not executable instructions. No client dataset or source-derived profile is
to be committed or sent to a provider. This register is not a claim that all
reported findings have been independently reproduced or fixed.

## Finding Dispositions To Verify

| Finding | Plan / acceptance boundary |
| --- | --- |
| 1 | Reproduce identifier/phone validation mismatch; correct generator/validator agreement without a blanket privacy bypass. Check claimed short-string path reachability separately. |
| 2 | Test distinct overflow and duplicates above the cap; report uncertainty or compute safely, never equate row count with distinct count without proof. |
| 3 | Reproduce numeric false positives; retain numeric-identifier and rare-secret protection. Reject blanket numeric exemptions and majority-based dismissal. |
| 4 | Test low-cardinality identifiers across CSV types; blanket absence of CSV top_values is contradicted by inspected code. |
| 5 | Test explicit local-category behavior; default synthetic labels are intentional in source-free mode. Exact preservation belongs to authorized policies. |
| 6 | Explicit sensitivity review is a product/security decision, not an unrestricted declassification flag. |
| 7 | Retain timestamp/timezone regressions and distinguish malformed profile/spec routing fixtures from valid inputs. |
| 8 | Reproduce repeated database keys incorrectly treated as row-unique; use cardinality evidence without copying raw identifiers. |
| 9 | Test independent identifier domains and consistent declared FK mappings; avoid accidental row-counter equality. |
| 10 | Test unavailable date bounds and explicit fallback disclosure; do not silently claim source-period fidelity. |
| 11 | Provide bounded connection failure categories, never raw database exception chains or credentials. |
| 12 | Explain name-based classification; any preservation exception needs approved policy and executable safety checks. |
| 13 | Test declared relationships, inference gaps and row-count behavior separately; existing generation does apply declared relationships. No automatic orphan-rate preservation. |
| 14 | Separate utility from conformance; schema/relationship/constraint validators already exist. Unmeasured fidelity must not be a pass. |
| 15 | Test category limits and early validation before unnecessary reads; settle configurable budgets explicitly. |
| 16 | Improve actionable safe SQL diagnostics; JOIN/CTE expansion remains a separate decision, not an assumed fix. |
| 17 | Measure query count and scan budgets; assess bounded aggregate batching. Temporary table writes are outside the read-only contract. |
| 18 | Test explicit derived formulas and unsupported expression disclosure; SQL-to-formula translation requires type/null/rounding semantics, not AST copying alone. |
| 19 | Reproduce atime-only publication failures; preserve path-swap protection. Define directory overwrite behavior explicitly and test rollback. |

Before candidate acceptance, give every row a final confirmed/fixed, intentional,
deferred or not-reproduced disposition with rationale and evidence. No silent
omissions; proposals outside the agreed scope remain explicit decisions.

## Supplied Scripts

### Evidence checkpoint: 2026-09-24

This checkpoint consolidates existing evidence; it is not a new test run or
final candidate acceptance. Detailed chronology and commands remain in
[progress](progress.md). Status applies only to the stated reproduced case.

| Finding | Current disposition and remaining evidence |
| --- | --- |
| 1 | Synthetic string identifiers with phone/email/ssn semantics reproduced as rejected. Product/security choice pending; no blanket privacy exemption implemented. Short-string reachability remains unverified. |
| 2 | Confirmed capped-folder case fixed in [PR #534](https://github.com/wa-pis/agent-paranoid-android/pull/534), merged as `0b7556e`. Fictional baseline returned 1.0 for 10,001 distinct values across 11,001 rows; `tests/test_schema_distinct_overflow.py` now verifies lower-bound metadata, cap boundary, no overflow PK nomination, legacy fingerprints and stale-cache reprofile. Relationship evidence tests and Python 3.11–3.14 CI passed. Standalone old profiles require reprofile; private client inputs and final installed RC replay remain unverified. |
| 8 | User approved fixed cardinality: four keys remain four as output grows. Correction merged in [PR #536](https://github.com/wa-pis/agent-paranoid-android/pull/536), `ca6cb12`, with green CI. Fictional CSV/folder/aggregate routes pass at 2, 100 and 1000 output rows (`tests/test_identifier_pool.py`): counts only, synthetic keys, deterministic pools. Nulls/small outputs may use fewer members; approximate input counts do not prove exact source fidelity. Installed-RC acceptance pending. |
| 4 | Fictional single-CSV probe on `1da23ad`: 100 rows/four repeated integer `run_id` values produced no top values and 100 generated identifiers; text equivalents produced four synthetic top values and four generated categories. Blanket absence of CSV top values is disproved. Numeric repeated-key case corrected in PR #536 using finding 8's approved fixed pool; focused regression and CI passed. No private-input or installed-RC acceptance claimed. |
| 9 | Independent identifier-domain collision fixed in [PR #517](https://github.com/wa-pis/agent-paranoid-android/pull/517). `tests/test_identifier_domains.py` covers independent fields and declared links; relationship-order follow-ups reviewed on `3add995`. This does not prove general relationship inference or cross-run mapping stability. |
| 19 | Deterministic access-time regression fixed in [PR #516](https://github.com/wa-pis/agent-paranoid-android/pull/516): two baseline failures, focused candidate checks passed. `tests/test_io_path_policy.py` retains presence/path-swap guards. Original script did not reproduce the timing failure: verified public 1.5.0 and publication candidate each yielded 24 successes/16 intended rejections. Five adapted subprocess scenarios passed both; not evidence that baseline contained no bug. |
| 7 | Timestamp subcase already corrected in baseline 1.5.0: isolated fictional CSV -> profile -> spec -> generation yields 20 timezone-aware values within observed bounds on baseline and `c28ac5a`. Time and +03:00 offset retained; not a new fix. Monthly-date granularity and mixed profile/spec routing remain separate unresolved subcases. No private-input or final installed-RC claim. |
| 3, 5–6, 10–18 | No final disposition established by this checkpoint. Preserve the finding-specific verification plans above; existing implementation or tests alone do not establish client-case acceptance. Finding 13 is not closed by the narrower declared-link fix under finding 9. |

Working-tree diagnostic follow-up (not final acceptance): finding 7 now explains
spec-key precedence and recovery without dropping privacy settings; automatic
reinterpretation remains unresolved. Finding 11 has fixed typed-network/TLS and
allowlisted SQLSTATE connection categories, with a generic fallback and no driver
text; injected-driver tests only, no live-driver verification. Finding 16 has
safe JOIN/CTE-specific rejection hints for PostgreSQL and Trino; no SQL-policy
expansion. Focused diagnostic/adapter/spec tests passed (56), and PostgreSQL
client/profiler/SQL-policy tests passed (52). CI and installed-RC replay pending.

Subsequent evidence: diagnostics merged in PR #537 (`3caa3ac`) with green CI.
Finding 15 explicit-category scope preflight merged in PR #538 (`70ee64d`) with
green CI: invalid explicit scopes fail before session creation; wildcard scopes
validate after bounded metadata and before aggregates. Category-limit policy is
unchanged. Finding 10 table-profile date/timestamp bounds are corrected locally:
37 focused checks cover aggregate -> inference -> generation, sensitive/all-null
exclusions and invalid/timezone-inconsistent endpoints. Temporal-bounds CI and
installed-RC replay remain pending; query-source bounds are not covered.

The installed publication candidate was `c3f1308`, version-labelled 1.5.0,
not the current branch or final 1.6.0rc1. Its wheel hash and original script hash
are recorded in progress. The initial installed 1.4.0 comparison was diagnostic
only and was superseded by verified public 1.5.0 replay. Missing private inputs
remain unverified. No original monkeypatched A/B arm is acceptance evidence.

- golden_run.py: adapt the profile-to-spec-to-output flow into assertions against
  the actual candidate CLI. Replace missing internal snapshot/pair inputs with
  fictional equivalents. Missing optional client data is SKIP, not product FAIL;
  mandatory fictional scenarios must run. Exit nonzero on real assertion failure
  (the supplied script always returns zero). Separate source-free expectations
  from explicitly authorized preservation. Five random samples need not cover
  every category; define deterministic cardinality/coverage expectations correctly.
- probe_output_contract.py: retain all five directory/overwrite cases and fresh
  subprocess runs. Require both successful exit and valid artifacts, not file
  existence alone. Add deterministic atime mutation, output-content checks and
  rollback assertions; do not rely solely on filesystem timing.
- probe_fix_ab.py and probe_fix_runner.py: use as diagnostic evidence only.
  The supplied fixed arm monkeypatches production functions and is not proof
  the shipped package is corrected. Final acceptance runs unpatched candidate
  code. Test absent/present transitions and symlink/path replacement: the sample
  destination comparison omits some None transitions and must not be copied
  blindly. The A/B driver also needs meaningful exit status before CI use.

Review scripts before execution, select the exact candidate interpreter/CLI,
bound subprocess duration, and isolate writes/cleanup inside newly allocated
temporary directories. Do not execute destructive cleanup against client folders.
Do not hard-code the old package version as proof of the tested version.

## Mandatory Local Candidate Replay

The reviewed publication adaptation lives in
`tests/test_client_publication_acceptance.py`. Run it with the normal pytest
environment. For an isolated wheel installed with `pip --target`, set
`TEST_DATA_AGENT_ACCEPTANCE_PACKAGE_ROOT` to that installation directory before
running the same test. It verifies the subprocess import path, five original
directory/overwrite cases, exit codes, CSV row/schema contents and preservation
of existing files. Subprocesses have 30-second timeouts and write only under
pytest temporary directories. It does not monkeypatch product code.

This adaptation complements—not replaces—the unchanged supplied script replay
and deterministic access-time/path-swap tests. Dependencies still come from the
test interpreter; this is not clean-environment release acceptance. Record the
wheel hash, metadata version and source SHA separately; a version label alone
cannot identify an unreleased candidate built before the version bump.

Before recommending a release candidate, build/install the candidate branch
package into an isolated local environment and run the reviewed client scripts
against that exact interpreter and CLI. Run the same self-contained scenarios
against the affected baseline in a separate environment. Record source commit,
installed version, script revision, fixture provenance, commands and per-scenario
before/after outcomes without source values. Package imports must not accidentally
resolve to another checkout or an unrelated executable on PATH.

Retain the supplied scripts as original diagnostic evidence in the isolated
working area; also run reviewed acceptance adaptations where the supplied harness
has defects or lacks fictional fixtures. Explain every adaptation and show both
results separately. Never turn a failure green by silently deleting or weakening
the client's requirement. The monkeypatched A/B arm remains diagnostic only;
candidate acceptance must exercise unpatched installed production code.

Each agreed client requirement must map to a runnable local scenario and a
recorded outcome. Missing private inputs remain explicitly unverified rather
than passed. Use fictional reproductions for mandatory local gates and request
client-side confirmation where only their private input can establish the result.
Do not claim complete client acceptance from the script's exit code alone.

## New Agreed Scenarios

Reviewed source-free CSV subset of `golden_run.py` is implemented in
`tests/test_client_golden_csv_acceptance.py`. It invokes profile/infer/generate
in bounded subprocesses, verifies the package import root, row/key counts,
date/amount bounds and validation report. It uses the same isolated-install
environment variable as the publication adaptation above. Unlike the original,
it asserts synthetic profile categories rather than source-category copying:
this explicitly tests the current source-free contract, not fulfillment of
finding 5. Private snapshot/pair cases and the rest of the original script are
not covered. A passing fictional subset does not close those requirements.

On 2026-09-24 this subset passed both verified public 1.5.0 and an isolated wheel
built from unchanged production code at `6a435db938e8ff43113e3f6f434fdd98f4363f42`.
Both used development-interpreter dependencies; neither is clean-environment
RC acceptance. Identical passing outcomes are compatibility evidence, not a
newly fixed regression. Wheel and adaptation hashes are recorded in progress.

Internal groundwork evidence: `tests/test_policy_mapping_roundtrip.py` compares
saved/reloaded inline YAML and local CSV mappings for leading-zero strings,
empty/null values, integers above binary-float exact range and calendar dates.
Both routes reject forbidden nulls and invalid dates under the declared types.
These tests cover private policy persistence and typed mapping validation only;
they do not establish transformation execution, wizard parity, approval,
financial Decimal support or acceptance of missing private client inputs.

Add one-to-one preserved reference combinations; changed amounts with zero and
rounding exceptions; explicit formulas; consistent key domains; exact date
substitution in selected fields; inline YAML/file CSV equivalence; profile
save/load/spec conversion; wizard/noninteractive parity; unknown mapping keys;
high cardinality under budgets; sensitivity conflicts and report/provider leaks.

Use the smallest reusable test fixtures and existing test framework rather than
creating a second independent harness (Ponytail principle). First demonstrate
that regression tests fail against the affected baseline, then pass on the
unpatched candidate. Client/private-data validation may be performed locally by
the client; report only approved non-sensitive outcomes. Do not claim their
private scenario passed from fictional-fixture results alone.
