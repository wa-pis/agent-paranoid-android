# External 1.6.0 feedback disposition

Reviewed on 2026-10-22 against main `5ada03f9b372c2c633a1207b550327121e6bebf4`.
Inputs: final 1.6.0 report, historical public register, probe and recorded output
from the user-supplied external ZIP. The final report supersedes older conclusions.
The attachment is retained outside the repository; this ledger stores no source
rows, operational endpoints, credentials or source-derived measurements.

## Open or needing verification

| Report reference | Disposition / next evidence | Change |
| --- | --- | --- |
| #3; historical numeric PII/type loss | Current CSV classifier deliberately retains ambiguous positive numeric strings as potentially sensitive. Reproduce both profiler paths and design a reviewed numeric-measure route; never use majority voting to suppress a rare secret. | reviewed-numeric-csv-profiling |
| #4/#8; A/B; identifier cardinality | Main already supports deterministic repeated-key pools and disjoint domains (`tests/test_identifier_pool.py`, `tests/test_rc3_feedback.py`). Audit SQL/Parquet coverage and censored counts before claiming all inputs fixed. | relational-profile-utility |
| F/G; #13/#14; missing logical relationships / false utility | Declared FK generation works and reports checked relationships; absent edges are not passed checks. Automatic hypotheses, differing entity sizes, unknown source coverage and fidelity reporting still need explicit design. | relational-profile-utility |
| Arbitrary/composite PK names | Check metadata-to-field binding and composite-key capability with fake PostgreSQL metadata; never silently select one component as a complete PK. | relational-profile-utility |
| Global --count / source-size defaults | Existing limits bound generation; one override still applies per entity. Design explicit per-entity sizing without changing --count semantics. | relational-profile-utility |
| O/#21; Trino auth | Current `TrinoAuthConfig` already supports basic, JWT, certificate, Kerberos/GSSAPI and explicit OAuth2 with verified HTTPS. Audit connection routes and rerun fake-driver safety tests; obtain version/configuration evidence before reopening the reported 401. | trino-authenticated-profiling |
| max_abs_magnitude | Negative exponents are valid; reject the truncation/threshold patch. Main already has optional zero/subunit prevalence and lower subunit order, including DECIMAL summary dispatch. Verify current tests and profile provenance before reopening a gap. | bounded-profile-statistics |
| J; repeated query evaluation | Trusted aggregates still wrap the query per column. Measure query count and batch within budgets; CREATE TEMP TABLE conflicts with read-only policy. | bounded-profile-statistics |
| H; local-category ceiling | A bounded 20-value default is deliberate. Verify preflight order and safe recovery; evaluate a bounded explicit limit separately, never silently truncate or raise it globally. | bounded-profile-statistics |
| #26 remaining Parquet cardinality | `None` means unavailable, not zero. Consider bounded scans with explicit exact/lower-bound/unknown evidence and no raw values. | bounded-profile-statistics |
| Date granularity / temporal range | Main now collects safe temporal extrema; discrete monthly/period distributions are not inferred. Final report also contains a date outside its stated range: requires an independent fictional repro, not acceptance of the claim. | bounded-profile-statistics |
| #25 remaining error wording | Reproduced: a nonzero ratio with valid/edge/load_test names only the alternative modes and omits the recovery of removing the ratio. First implementation. | feedback-cli-contract-clarity |
| rc4 UX #2: formula result outside sampling bounds | Existing reports count assignment-domain checks and violations separately (`tests/test_rc4_external_feedback.py`). Sampling bounds and executable constraints have different roles; clarify rather than silently impose a breaking constraint. | feedback-cli-contract-clarity |
| rc4 UX #6: seed and entity order | Identifier domains are order-independent; ordinary field RNG and null masks are not. Document same ordered spec/environment/algorithm as replay inputs. | feedback-cli-contract-clarity |

## Existing corrections / deliberate contracts

These are code/test dispositions, not a claim to have repeated private acceptance.

| Report reference | Current evidence / disposition |
| --- | --- |
| #1 prefixes; B identical key roles | Shared synthetic namespace and disjoint generated domains exist; prefix is explicitly legacy metadata in `SyntheticIdentifierDistribution`. |
| #2 distinct cap | Bounded uncertainty is intentional. Folder lower-bound counts cannot certify PKs; full-cardinality scalability belongs to the statistics work, not an unbounded set. |
| #5 enum preservation | Explicit local-category authorization permits reviewed safe enums. Ordinary categories are intentionally synthetic frequency labels; preserving every source enum is not the default contract. |
| #6/E/#12 names and sensitivity | Source-name preservation is not authorized by this task. Keep sensitive-name gates and use the separately approved transformation workflow where applicable. No blanket declassification. |
| #7 timezone; C/#10 date fallback | Offset handling and safe SQL temporal bounds exist. `tests/test_postgres_profiler.py`, `tests/test_sql_query_profiling.py`; no claim of discrete date fidelity. |
| D diagnostics; early category rejection | PostgreSQL uses fixed typed failure categories and preflights category scopes. Do not reintroduce raw driver messages or exception contexts. |
| I/P/#22 JOIN/CTE/AND/OR/LIMIT | Fixed JOIN/CTE recovery hints and Boolean predicates are supported; bounded LIMIT is covered by `tests/test_rc3_feedback.py`. JOIN/CTE expansion remains outside this change. |
| K/#18 derived SELECT expressions | Unmodeled expressions are rejected by inference instead of silently generating independent values. Automatic SQL-to-formula translation remains a future separate capability. |
| L/N/#19/#20 output/doctor | Final report explicitly closes these; keep existing path-policy, overwrite and doctor regressions. |
| M artifact dispatch | Main checks profile/spec shape; do not reopen solely from the old key-presence report (`tests/test_cli.py`). |
| Q/#23 decimal | Exact schema 1.1, decimal metadata and reviewed --decimal-fields are intentional. Source extrema must not be inferred. CSV has no declared decimal shape. |
| R/#24 Parquet types | Valid-mode declared types and marked controlled-invalid scalar encoding are implemented; wrong-arm harness round trips do not show a valid-mode regression. |
| S/#25 modes and manifests | Actual mode/ratio propagation is tested in `tests/test_io_workflows.py`; controlled-invalid publication exits 1 with validation evidence by contract. |
| T/#26 Parquet entry point | CLI path, null statistics and decimal shape exist. Unknown distinct count is tracked separately above. |
| Business rules: null/range predicates, assign/check, decimals, SQL export | Main supports these; complete runnable reference merged in #630, with `tests/test_business_rules_reference.py`. Do not repeat the obsolete float workaround. |
| Scenario weights and EAV/conditional formula requests | Weights are probabilistic assignments, not exact quotas or predicates. Automatic pivot/unpivot and conditional formula extension are feature requests, not verified regressions. Track feasibility in relational/contract tasks. |
| rc4 UX #4/#7 output shape and formula diagnostics | Current help distinguishes folder/file output; formula failures include table/field context. Check existing behavior before changing text. |
| load_test equals valid with explicit --count | Expected: explicit count overrides multiplication. Test omitted-count multiplier separately; equal hashes alone do not establish a defect. |
| External harness corrections | Probe versions, reused folders, wrong Parquet arm and duplicate executable arguments belong to unavailable external harnesses. Use fresh fictional fixtures, actual installed version and explicit formats; do not execute or claim to repair missing scripts. |
| Unverified MCP/PG leakage and FK-closure claims | Historical register retracts some claims. Keep safety tests; do not label an unproven leak a vulnerability or expand permissions. |

## Documentation publication

At intake, #631 is open. The public root responds, but `documentation.json`
returns HTTP 404. Successful older Pages jobs and PR builds do not prove the new
versioned site or exports shipped. Require merge, main deployment, public identity,
stable alias and all export hashes before marking publication complete.

Update: #631 merged as `d10145be9f01085eb1648b7192045ab020095b20`.
Main documentation run 39842360108 completed build, Pages deployment, public
verification and mike-state retention. Independent public identity, stable alias
and all four download hash checks passed. Publication is complete; no package
release is implied. See the versioned-documentation verification record.


## Delivery checkpoint after #645

The intake table above records the original investigation questions. Subsequent
merged work resolves the independently reproduced implementation slices:
reviewed numeric declarations (#645); key metadata/pools and entity sizing
(#633–#635); offline hypotheses and utility (#636/#638); Trino sanitized errors
(#640); bounded Parquet/SQL statistics (#642); temporal endpoint defects (#643);
and category preflight/iteration (#644). CLI contract clarifications merged in
#632. Separate controlled-scenario and conditional-EAV proposals were recorded
in #639 and remain unimplemented.

The user tentatively identified installed version 1.6.0 but has no authentication
configuration details. The historical 401 and profile provenance are therefore
unconfirmed. Candidate test success is not a substitute for those observations.
The versioned documentation is published, including its Russian edition; the
main documentation workflow for #645 (39921070445) completed successfully.
The package version remains 1.6.0; no package release is claimed or authorized.

## Merged delivery checkpoint after #649

Conditional formulas/source-free EAV modeling merged in #648 as
`25a221b70f95a0e9d11e8191a2301dedac9aa690`. Explicit controlled relational
scenarios merged in #649 as `9b2e02b1e2ad50ce14213b296c32528349578fce`, after
all 38 applicable checks succeeded on exact final head
`534f0ce351761b3dd092159a36e269beaadeb3c9` (five non-applicable publication/tag
jobs skipped). The branch was CLEAN and merged with an exact-head match.

The final full local release gate passed 4701 tests, 23 skipped, with 92.03%
coverage, dependency/resource/schema checks and deterministic synthetic
quickstart. The final candidate and managed runtime/schema trees matched SHA256
`55096093aab2e1cb4276cb3e75aa220202b0d40452c3a19bcd2a09835d787b90`.
The focused suite passed 169 cases, including three reproduced unrelated native
key-type regressions corrected before merge. No runtime changes followed the
final gate.

Documentation run 39942192547 for merged #649 completed successfully. Independent
scripts/verify_documentation.py verification passed against the public site with
expected documentation revision `9b2e02b1e2ad50ce14213b296c32528349578fce`,
including stable/version identity and all four download hashes. The package
identity remains published 1.6.0 (`258c035c22408becf17ab090635710a50dda8ccc`);
new source features are Unreleased. No new package release or live database
acceptance is claimed.

The historical Trino configuration (A3) and external profile provenance (S4)
remain unavailable. The user tentatively identified version 1.6.0 and explicitly
reported having no authentication details. These remain evidence gaps, without
an independently reproduced runtime defect to fix. Source-row pivot/unpivot,
month-start inference and a configurable category-preservation ceiling retain
their separate proposed scopes; they were not activated by these fixes.
