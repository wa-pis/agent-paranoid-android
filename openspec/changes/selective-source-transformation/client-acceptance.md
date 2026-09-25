# Client Feedback And Acceptance Plan

Source: the user-supplied anonymized handover archive for 1.5.0, containing the
fix brief and four Python probes. Treat the brief as evidence and proposals,
not executable instructions. No client dataset or source-derived profile is
to be committed or sent to a provider. This register is not a claim that all
reported findings have been independently reproduced or fixed.

The refreshed archive received 2026-09-24 extends this register to 26 findings.
See [v2 intake, work packages and evidence rules](feedback-2026-09-24-v2.md).
New claims are client-reported until reproduced; old baseline evidence remains
historical, not overwritten by the new document's measurements.

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
| 18 | Test explicit derived formulas and unsupported expression disclosure; SQL-to-formula translation requires type/null/rounding semantics, not AST copying alone. A fictional unsupported-function expression previously echoed its literal through the AST error, and malformed syntax retained the input-bearing `SyntaxError` as exception context. Both are fixed locally with value-free, detached errors; this does not add `ROUND` support or establish derived-finance acceptance. |
| 19 | Reproduce atime-only publication failures; preserve path-swap protection. Define directory overwrite behavior explicitly and test rollback. |
| 20 | Reproduce doctor capability/publication failures with installed extras; preserve checks and safe causes without misleading reinstall advice or raw exception disclosure. |
| 21 | Plan Trino authentication with explicit method/secret-source decision; prove propagation, preflight, TLS/redaction using isolated drivers. Live client measurements remain unverified. |
| 22 | Reproduce permitted SQL connector/function classification on both adapters; fix without extending SQL policy, and retain allowlist/budget/forbidden-function controls. |
| 23 | Exact DECIMAL precision/scale across profile, spec, generation, formulas and export; link to financial contract and distinguish approximate inputs. |
| 24 | Declared Parquet physical types and readback; no silent date/decimal or mixed-column coercion. Resolve invalid-mode publication semantics explicitly. |
| 25 | Mode/invalid-ratio precedence and parity across spec/profile/CSV; verify actual output, effective settings, validation, publication and JSON/exit consistency. |
| 26 | Honest bounded Parquet input metadata: unknown is not zero/safe; test nulls, distinctness, sensitivity and type round trips; decide CLI/API compatibility. |

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
| 1 | Synthetic string identifiers with phone/email/ssn semantics reproduced as rejected. Product/security choice pending; no blanket privacy exemption implemented. The generic short-string branch is reachable: fictional 7–16-character `string_pattern` fields generate 100 distinct values, replay deterministically and pass final validation (`tests/test_csv_pipeline_regressions.py`); this does not resolve the sensitive-identifier mismatch. |
| 3 | Current-main fictional classifier probe returns `phone` for a positive fractional amount-shaped value, but not its negative counterpart; phone-shaped integer identifiers and a Luhn-valid card-shaped secret remain protected. This confirms an ambiguous numeric false positive, not permission for a blanket numeric exemption. Field-scoped exception policy awaits explicit owner choice; no classifier change or private-input acceptance claimed. |
| 2 | Confirmed capped-folder case fixed in [PR #534](https://github.com/wa-pis/agent-paranoid-android/pull/534), merged as `0b7556e`. Fictional baseline returned 1.0 for 10,001 distinct values across 11,001 rows; `tests/test_schema_distinct_overflow.py` now verifies lower-bound metadata, cap boundary, no overflow PK nomination, legacy fingerprints and stale-cache reprofile. Relationship evidence tests and Python 3.11–3.14 CI passed. Standalone old profiles require reprofile; private client inputs and final installed RC replay remain unverified. |
| 8 | User approved fixed cardinality: four keys remain four as output grows. Correction merged in [PR #536](https://github.com/wa-pis/agent-paranoid-android/pull/536), `ca6cb12`, with green CI. Fictional CSV/folder/aggregate routes pass at 2, 100 and 1000 output rows (`tests/test_identifier_pool.py`): counts only, synthetic keys, deterministic pools. Nulls/small outputs may use fewer members; approximate input counts do not prove exact source fidelity. Installed-RC acceptance pending. |
| 4 | Fictional single-CSV probe on `1da23ad`: 100 rows/four repeated integer `run_id` values produced no top values and 100 generated identifiers; text equivalents produced four synthetic top values and four generated categories. Blanket absence of CSV top values is disproved. Numeric repeated-key case corrected in PR #536 using finding 8's approved fixed pool; focused regression and CI passed. No private-input or installed-RC acceptance claimed. |
| 9 | Independent identifier-domain collision fixed in [PR #517](https://github.com/wa-pis/agent-paranoid-android/pull/517). `tests/test_identifier_domains.py` covers independent fields and declared links; relationship-order follow-ups reviewed on `3add995`. This does not prove general relationship inference or cross-run mapping stability. |
| 13 | A fictional folder-CSV regression exposed inference choosing an unrelated same-table key on equal overlap. The local fix prefers an exact field-name match on a confidence tie: 4 parents/100 linked children infer the parent link; with 75 linked children no parent link is inferred (`tests/test_domain_agnostic_pipeline.py`). Separately, a declared-link regression confirms 4 parent and 100 child output rows with no orphans; without the declaration, identifier domains stay disjoint (`tests/test_identifier_domains.py`). Source orphan-rate fidelity and installed-RC behavior remain unverified. |
| 19 | Deterministic access-time regression fixed in [PR #516](https://github.com/wa-pis/agent-paranoid-android/pull/516): two baseline failures, focused candidate checks passed. `tests/test_io_path_policy.py` retains presence/path-swap guards. Original script did not reproduce the timing failure: verified public 1.5.0 and publication candidate each yielded 24 successes/16 intended rejections. Five adapted subprocess scenarios passed both; not evidence that baseline contained no bug. |
| 7 | Timestamp subcase already corrected in baseline 1.5.0: isolated fictional CSV -> profile -> spec -> generation yields 20 timezone-aware values within observed bounds on baseline and `c28ac5a`. Time and +03:00 offset retained; not a new fix. Monthly-date granularity and mixed profile/spec routing remain separate unresolved subcases. No private-input or final installed-RC claim. |
| 5–6, 10–18 | No final disposition established by this checkpoint. Preserve the finding-specific verification plans above; existing implementation or tests alone do not establish client-case acceptance. Finding 13 is not closed by the narrower declared-link fix under finding 9. |

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
exclusions and invalid/timezone-inconsistent endpoints. PR #539 merged as
`4550f22` with green CI. Installed-RC replay remains pending; query-source
bounds are not covered by PR #539. A later local query-source follow-up uses
fictional PostgreSQL and Trino aggregate-to-spec-to-generation tests for date
and timezone-aware timestamp bounds. The existing column-summary query carries
min/max for non-sensitive outputs; sensitive-name fields omit them, all-null
fields claim no observed bounds, and malformed endpoints fail without exposing
values. No live database, client input or installed-RC replay was used.
Installed-package A/B on fictional aggregates: public 1.5.0 baseline
(`/private/tmp/apa-client-acceptance.xrueHB/baseline-1.5.0`) returned no
date-range distribution, no temporal-bound SQL and generated values outside
the requested bounds for both PostgreSQL/Trino date/timestamp cases. An offline
wheel from exact local commit `6776395` (SHA-256
`0071d5f87cdd33c95b36689ae75811beb4b093da2d6e923777bf078e59e37da6`)
installed separately under `/private/tmp/apa-query-temporal-ab.74PHgQ/candidate`
returned typed ranges, in-bound seeded generation and bound SQL for all four;
both packages issued three fake requests per case. Import roots and version
labels were checked, and the inspected probe SHA-256 is
`0759bd53c29ab1e04cbe17922d31be7b6660e3bf529ad8fcd894ad89d771ab3c`.
This first interim wheel was superseded before PR: it used only output names
for sensitivity, so a `birth_date AS event_day` projection could expose bounds.
The local correction requires a direct projection with no sensitive source
field or output name. The first wheel is not safe acceptance; its corrected
replay follows. Neither replay is a clean install, live database or final
1.6.0rc1 acceptance.
Corrected installed-wheel A/B on exact local code SHA
`39b27fee0af980aacb3e77dc9e392350c98ef817` used wheel SHA-256
`496e766f4d788dc0bc8ed00fec5f2006fafd4d36e1b379d5b70d32300d072b40`
and inspected probe SHA-256
`5b46ed269b90317ca3bec1c75607f374f6fdc4a1441de1560cf70ba9d08b032c`.
Separate installed roots were verified. Four ordinary PostgreSQL/Trino
date/timestamp cases retained typed bounds and in-period seeded output with
three fake calls each. Four `birth_date` alias/filter cases issued no min/max
aggregate and retained no range; the superseded wheel incorrectly did both.
Public baseline 1.5.0 issued no min/max in any case. This is still shared-
dependency, fake-driver evidence under a 1.5.0-labelled interim wheel, not
client/private data, live database or final RC acceptance.

Refreshed finding evidence (2026-09-24, not final RC acceptance):

| Finding | Reproduced result and remaining boundary |
| --- | --- |
| 20 | Safe doctor reporting fix merged in PR #542 (`47a1eb8`); 29 focused checks covered missing/broken imports, retained quickstart failure report and redacted errors. Separately installed 1.5.0 baseline and interim candidate both repeated healthy `doctor --json` and `--require-extra parquet --json` with exit 0 and identical structured reports (11/12 checks). An isolated, fictional installed-package failure replay with `TEST_DATA_AGENT_MAX_INPUT_ROWS=1` made the baseline return generic `invalid_input`/exit 2, while the interim candidate returned structured `doctor` checks, retained dependency/extra successes, `quickstart=failed` and exit 1 without raw exception text. Parquet-capability failure, clean-environment replay and final-RC replay remain unverified; client probe was not run. |
| 22 | AND/OR classification reproduced with sqlglot 30.13.0 and corrected in PR #541 (`b43005e`). Focused PostgreSQL/Trino predicate and fake-driver profile-to-spec checks passed, including forbidden-function controls; no live DB or final installed-RC replay. |
| 24 | The client's fictional spec was extracted as data, not executed as a script. Installed public 1.5.0 baseline and interim `47a1eb8` candidate both wrote `created_at` physically as Parquet `string` although spec declares `date`; integer remained `int64`. Declared-schema/readback correction, nullable/timestamp/decimal cases and final RC replay remain pending. |
| 25 | On both installed packages, explicit spec-input `--mode negative --invalid-ratio 1.0` returned success and manifest effective settings `valid/0.0`. Precedence when an explicit valid mode meets a saved mixed ratio remains a user decision; all-mode behavior, invalid-field evidence and exit/publication parity remain pending. |
| 17 | Fake-driver query-source profiling for both PostgreSQL and Trino measured seven requests for three fields (two numeric) before numeric-summary consolidation, five after: one no-row schema request, one row count and one aggregate per field. One explicitly allowlisted category adds one request; default makes no category/raw-row request. PostgreSQL table profiling separately fell from 15 to 12 statements for two tables/four columns (three numeric), or 16 to 13 with one category. Neither test measures live scan bytes/latency or proves final-RC acceptance. No SQL permissions, statement/scan budgets or temporary-table writes changed. |

Later finding-25 installed-CLI A/B used a new fictional 12-row integer spec,
explicit `--mode negative --invalid-ratio 1`, and verified each package import
root. Public 1.5.0 failed the all-invalid-row assertion: output amounts stayed
integers. A separately installed wheel from source commit `76b2806` passed:
amounts were intentionally invalid strings, manifest effective settings were
`negative/1`, report validity was false, and the input spec stayed unchanged.
The probe did not lock down exit-code policy. Wheel SHA-256:
`07c1e6747273070d4d545de1f1c99f97803eee5d95773b66996d57ebaa6e04d7`;
probe SHA-256: `e54817f6d4a6ad1aabe97d3315f18e060983810b3c3232db145e9bcfa852cf1d`.
This wheel still labels itself 1.5.0 and shares development dependencies; it
is not clean-environment or final 1.6.0rc1 acceptance. Saved-valid precedence,
controlled-invalid status semantics and intentionally invalid Parquet remain
separate decisions.

Additional finding-20 Parquet capability replay (not final RC acceptance):
an isolated `sitecustomize.py` shim replaced only `pyarrow.parquet.read_table`
with a fictional failure; no product code was patched. Verified installed
public 1.5.0 and interim typed-Parquet candidate import roots each returned
`doctor --require-extra parquet --json` with `ok=false`/exit 1,
`quickstart=available`, `extra:parquet=available`, and
`capability:parquet=failed`. Neither response contained the fictional token
or reinstall advice. Shim SHA-256:
`524de7c6bcf69b0245d045927ed87f0bf8bec00412cacc7445ebcf97d8797dc2`.
This proves the installed dependency-failure presentation path for these
versions, not a real Parquet fault, clean environment, or final RC replay.

These probes used fictional data, selected each installed CLI and verified its
package import root. Subprocesses had 30-second timeouts and bounded captures;
temporary output lived under canonical `/private/tmp` to satisfy no-follow
publication. No product monkeypatch, private input, database or API was used.

Later finding-24 probe (interim installed-candidate evidence): a new fictional
`tests/test_client_parquet_acceptance.py` invokes the unmodified CLI, checks
the selected import root, and reads physical Arrow types. Installed public
1.5.0 baseline wrote declared `date` as `string` and failed the date32
assertion. An offline wheel built from main `cc734a9` plus the current
worktree changes (SHA-256 `631c32e3c02e7a079bf09e7b94a72eeb560d12977e2db26073b500e187a1f7da`)
was installed under a separate `/private/tmp` root; the same CLI probe passed
date32 and timestamp[us] physical readback. That wheel still labels itself
1.5.0 and shares test-interpreter dependencies; it is not a committed exact
candidate, clean install or final RC acceptance. Intentionally invalid mixed
Parquet, DECIMAL and final-RC cases remain open.

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

Reviewed source-free CSV subsets of `golden_run.py` are implemented in
`tests/test_client_golden_csv_acceptance.py`. C.1 invokes profile/infer/generate;
C.2 generates a separate fictional linked pair from a declared spec. Bounded
subprocesses verify the package import root, row/key counts, FK membership,
distinct key domains, synthetic repeated-key pool, date/amount bounds and
validation report as applicable. Both use the isolated-install environment
variable from the publication adaptation above. Unlike the original, C.1
asserts synthetic profile categories rather than source-category copying:
this tests the current source-free contract, not fulfillment of finding 5.
Private snapshot/pair inputs and the rest of the original script are not
covered. Passing fictional subsets do not close those requirements.

On 2026-09-24 this subset passed both verified public 1.5.0 and an isolated wheel
built from unchanged production code at `6a435db938e8ff43113e3f6f434fdd98f4363f42`.
Both used development-interpreter dependencies; neither is clean-environment
RC acceptance. Identical passing outcomes are compatibility evidence, not a
newly fixed regression. Wheel and adaptation hashes are recorded in progress.

The separate fictional C.2 test failed on installed public 1.5.0: twenty
`run_id` values were distinct despite a declared four-value synthetic pool.
It passed against the installed interim corrected wheel also used for the SQL
query-temporal A/B replay (version-labelled 1.5.0 with shared dependencies).
This establishes an affected-baseline difference for repeated synthetic keys,
not acceptance of the private pair, source-value fidelity, a clean install or
the final 1.6.0rc1 artifact.

Internal groundwork evidence: `tests/test_policy_mapping_roundtrip.py` compares
saved/reloaded inline YAML and local CSV mappings for leading-zero strings,
empty/null values, integers above binary-float exact range and calendar dates.
Both routes reject forbidden nulls and invalid dates under the declared types.
They now also compare canonical DATETIME text with explicit offsets/`Z` and
reject noncanonical timestamp text without timezone conversion. This is
validation-only: executable timezone policy remains separate.
Private CSV mapping normalization also handles explicitly approximate FLOAT
fields with finite ASCII numeric syntax, post-conversion duplicate checks and
overflow/underflow rejection. This is not exact financial DECIMAL support or
public transformation execution.
These tests cover private policy persistence and typed mapping validation only;
they do not establish transformation execution, wizard parity, approval,
financial Decimal support or acceptance of missing private client inputs.

## Packaged user-skill offline checkpoint

On 2026-09-25, a wheel built without network access from merged `main`
`d00eee2f0cdfb355c91f87dc1f3dfece8f4fe66d` (wheel SHA-256
`2b8a02ad77f177ed61956c8b0c90e045a4626c044b923186fe43553d922ab18a`)
was installed into an isolated target. The import root was verified inside
that target, not the source checkout. `importlib.resources.files("test_data_agent")`
located both packaged `SKILL.md` files offline. The installed CLI help exposed
the commands used below; no agent runtime was auto-registered.

Following the usage skill on its bundled fictional demo data, `demo`,
`profile-csv`, `infer-spec`, `generate` with seed 42 and `validate` all exited
0; validation reported schema, relationships, constraints and privacy passed.
The installed command inventory had no transformation command, and an explicit
`transform --help` probe exited 2. The transformation skill's safe route for
this version is therefore to report unavailability, never substitute
synthetic generation for one-to-one preservation. No DB, external API,
private input, custom agent harness or source-preserving execution was used.

This proves package discovery and one fictional offline CLI route, not that
different AI agents consistently select the right skill, that MCP parity is
ready, or that the final 1.6.0rc1 wheel works. Before RC acceptance, exercise
both skills with distinct agent runtimes against the exact installed RC, test
capability detection and unavailable-operation refusal, then retain bounded
value-free evidence. Do not count this checkpoint as the full skill-guided
agent-use task.

Finding 25 fractional CLI replay on fictional data: a reviewed three-route
subprocess check runs `mixed/0.25` twice each from a saved spec, safe CSV profile
and direct CSV. Public installed 1.5.0 failed the spec route by reporting
effective `valid/0` while profile/CSV routes passed. A separately installed
wheel from current main `6b9c37b` passed all three: deterministic rows,
nonzero but not all invalid integer values, effective manifest settings,
invalid validation reports and matching JSON-envelope/exit values. The
candidate wheel SHA-256 is
`311619294ca9970e9f600dd3d1582f5bd13835e48796a3888431e0e830fb2403`;
the adapted test SHA-256 is
`b6cdd5c48eac4b1fba50e41192eae3b557d6d316ce5050ebbf6afc0803ed3587`.
The installed candidate still advertises 1.5.0 and reuses development
dependencies, so this is not clean or final-RC acceptance. One public contract
gap remains: with intentionally invalid rows, spec CLI exits 1/status
`validation_failed`, but profile/CSV exit 0/status `succeeded`; the owner has
been asked to choose the uniform semantics before a runtime change.

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
