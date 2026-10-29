# Installed feedback acceptance — 1.7.0rc1

This dated follow-up binds the original findings 1–26 and section E to actual
public installed packages. It supplements the historical client register; no
private measurements or prior runs are relabelled. The
[machine-readable ledger](feedback-acceptance-1.7.0rc1.json) records every
selected test case/outcome, fixture hashes, original script hashes and all 61
historical source-anchor locations for each installed package.

## Package identity and results

Baseline is published 1.6.0, source `258c035c22408becf17ab090635710a50dda8ccc`;
candidate is published 1.7.0rc1, source
`64b7c8c3bbb0174fd7e159c4dfb42312045a1716`. Independently downloaded PyPI
wheels match the release hashes, and all 157/173 installed package payloads
match those wheels byte-for-byte. Both separate Python 3.11.2 environments use
MCP 2.3.0, OpenAI 3.37.0, SQLGlot 30.24.0, PyArrow 26.0.0, Pydantic 2.14.1
and Faker 40.43.0 for this comparison. These current dependencies do not
reconstruct the historical client environment.

The shared cohort has **782 cases** across 32 maintained fictional test modules:
1.6.0 has 757 passes and 25 differing assertions; 1.7.0rc1 passes all 782 after
the environment correction below. The 25 differences include new-feature and
changed mock-query expectations, so they are not 25 newly discovered baseline
bugs. Candidate conditional formulas additionally pass all 33 cases; dependency
guards pass on both packages. Twenty real `doctor --require-extra parquet
--json` invocations in fresh processes per package all exit zero.

The initial cohort recorded 756/26 and 781/1 pass/fail respectively: a clean
PATH hid `pg_config`, preventing installed psycopg from loading native libpq.
Doctor correctly stopped at dependency import before the expected Trino check.
Adding the installed native dependency discovery directory made the unchanged
doctor/dependency tests pass (17 per package). The first conditional follow-up
also omitted its example file (48 passes, two fixture failures); copying the
exact reviewed fictional example produced 33/33. Original outcomes and separate
rechecks are retained rather than silently overwritten. Product code was not
patched.

## Per-finding disposition

The module links identify the actual selected tests, not private-client input.
The newer [260 installed feedback regressions](release-evidence-1.7.0rc1.md)
and the published 600-cell cross-interface matrix supplement this cohort.

| Finding | Executed fictional coverage | Disposition / limit |
| --- | --- | --- |
| 1: Synthetic identifier validation | [csv_pipeline_regressions](https://github.com/wa-pis/agent-paranoid-android/blob/6801997b763fa4b4ba9a27303b96ab507ab1f610/tests/test_csv_pipeline_regressions.py), [privacy_corpus](https://github.com/wa-pis/agent-paranoid-android/blob/6801997b763fa4b4ba9a27303b96ab507ab1f610/tests/test_privacy_corpus.py) | Supported synthetic identifiers pass privacy validation; this does not waive sensitive-name/content checks or validate the absent private snapshot. |
| 2: Distinctness and primary-key evidence | [schema_distinct_overflow](https://github.com/wa-pis/agent-paranoid-android/blob/6801997b763fa4b4ba9a27303b96ab507ab1f610/tests/test_schema_distinct_overflow.py), [identifier_pool](https://github.com/wa-pis/agent-paranoid-android/blob/6801997b763fa4b4ba9a27303b96ab507ab1f610/tests/test_identifier_pool.py) | Overflow remains lower-bound evidence and cannot nominate a primary key; reprofile older artifacts. |
| 3: Numeric storage versus sensitivity | [csv_pipeline_regressions](https://github.com/wa-pis/agent-paranoid-android/blob/6801997b763fa4b4ba9a27303b96ab507ab1f610/tests/test_csv_pipeline_regressions.py), [privacy_corpus](https://github.com/wa-pis/agent-paranoid-android/blob/6801997b763fa4b4ba9a27303b96ab507ab1f610/tests/test_privacy_corpus.py) | Conservative positive sensitivity remains. Reviewed numeric-measure declarations and their separate installed feedback regressions are recorded in the release evidence; no majority-based declassification. |
| 4: Categorical metadata and repeated keys | [identifier_pool](https://github.com/wa-pis/agent-paranoid-android/blob/6801997b763fa4b4ba9a27303b96ab507ab1f610/tests/test_identifier_pool.py), [local_category_policy](https://github.com/wa-pis/agent-paranoid-android/blob/6801997b763fa4b4ba9a27303b96ab507ab1f610/tests/test_local_category_policy.py) | Bounded synthetic categories and generated repeated-key domains are supported; no source identifier pool is copied. |
| 5: Source enum retention | [client_golden_csv_acceptance](https://github.com/wa-pis/agent-paranoid-android/blob/6801997b763fa4b4ba9a27303b96ab507ab1f610/tests/test_client_golden_csv_acceptance.py), [local_category_policy](https://github.com/wa-pis/agent-paranoid-android/blob/6801997b763fa4b4ba9a27303b96ab507ab1f610/tests/test_local_category_policy.py) | Intentional source-free default. The original golden source-enum assertion stays red on both packages; explicit reviewed local categories are separately tested. |
| 6: Sensitivity-name override | [transformation_policy](https://github.com/wa-pis/agent-paranoid-android/blob/6801997b763fa4b4ba9a27303b96ab507ab1f610/tests/test_transformation_policy.py), [transformation_approval](https://github.com/wa-pis/agent-paranoid-android/blob/6801997b763fa4b4ba9a27303b96ab507ab1f610/tests/test_transformation_approval.py), [privacy_corpus](https://github.com/wa-pis/agent-paranoid-android/blob/6801997b763fa4b4ba9a27303b96ab507ab1f610/tests/test_privacy_corpus.py) | Intentional safety boundary; notes and declarations cannot override positive evidence. |
| 7: Timestamp and temporal routing | [csv_pipeline_regressions](https://github.com/wa-pis/agent-paranoid-android/blob/6801997b763fa4b4ba9a27303b96ab507ab1f610/tests/test_csv_pipeline_regressions.py), [date_fallback_disclosure](https://github.com/wa-pis/agent-paranoid-android/blob/6801997b763fa4b4ba9a27303b96ab507ab1f610/tests/test_date_fallback_disclosure.py) | Supported offsets/bounds and disclosed missing-bound fallback are tested. Monthly-category inference remains deferred. |
| 8: Repeated-key cardinality | [identifier_pool](https://github.com/wa-pis/agent-paranoid-android/blob/6801997b763fa4b4ba9a27303b96ab507ab1f610/tests/test_identifier_pool.py), [client_golden_csv_acceptance](https://github.com/wa-pis/agent-paranoid-android/blob/6801997b763fa4b4ba9a27303b96ab507ab1f610/tests/test_client_golden_csv_acceptance.py) | Generated repeated-key pools retain bounded distinct domains; observed output membership can be smaller in short/null-heavy samples. |
| 9: Distinct key roles and declared FK | [identifier_domains](https://github.com/wa-pis/agent-paranoid-android/blob/6801997b763fa4b4ba9a27303b96ab507ab1f610/tests/test_identifier_domains.py), [client_golden_csv_acceptance](https://github.com/wa-pis/agent-paranoid-android/blob/6801997b763fa4b4ba9a27303b96ab507ab1f610/tests/test_client_golden_csv_acceptance.py) | Independent key domains and declared parent membership are asserted; no source mapping or arbitrary relationship inference is implied. |
| 10: Supported temporal extrema | [postgres_temporal_bounds](https://github.com/wa-pis/agent-paranoid-android/blob/6801997b763fa4b4ba9a27303b96ab507ab1f610/tests/test_postgres_temporal_bounds.py), [sql_query_temporal_bounds](https://github.com/wa-pis/agent-paranoid-android/blob/6801997b763fa4b4ba9a27303b96ab507ab1f610/tests/test_sql_query_temporal_bounds.py), [date_fallback_disclosure](https://github.com/wa-pis/agent-paranoid-android/blob/6801997b763fa4b4ba9a27303b96ab507ab1f610/tests/test_date_fallback_disclosure.py) | Fictional typed bounds and explicit unknown/fallback behavior pass. The missing private pair and its source period remain unverified. |
| 11: Safe backend diagnostics | [postgres_client](https://github.com/wa-pis/agent-paranoid-android/blob/6801997b763fa4b4ba9a27303b96ab507ab1f610/tests/test_postgres_client.py), [sql_query_adapters](https://github.com/wa-pis/agent-paranoid-android/blob/6801997b763fa4b4ba9a27303b96ab507ab1f610/tests/test_sql_query_adapters.py) | Typed diagnostics and value-free failures are tested with fictional drivers; no live reachability or raw exception-text parsing. |
| 12: Source names and sensitive fields | [transformation_policy](https://github.com/wa-pis/agent-paranoid-android/blob/6801997b763fa4b4ba9a27303b96ab507ab1f610/tests/test_transformation_policy.py), [transformation_approval](https://github.com/wa-pis/agent-paranoid-android/blob/6801997b763fa4b4ba9a27303b96ab507ab1f610/tests/test_transformation_approval.py), [privacy_corpus](https://github.com/wa-pis/agent-paranoid-android/blob/6801997b763fa4b4ba9a27303b96ab507ab1f610/tests/test_privacy_corpus.py) | Intentional conservative policy; source-name preservation requires the separate reviewed transformation contract and local receipt. |
| 13: Relationships and orphan utility | [identifier_domains](https://github.com/wa-pis/agent-paranoid-android/blob/6801997b763fa4b4ba9a27303b96ab507ab1f610/tests/test_identifier_domains.py), [relationship_discovery](https://github.com/wa-pis/agent-paranoid-android/blob/6801997b763fa4b4ba9a27303b96ab507ab1f610/tests/test_relationship_discovery.py), [domain_agnostic_pipeline](https://github.com/wa-pis/agent-paranoid-android/blob/6801997b763fa4b4ba9a27303b96ab507ab1f610/tests/test_domain_agnostic_pipeline.py) | Declared links and offline bounded hypotheses are tested. Source orphan-rate fidelity and absent private pair remain unverified. |
| 14: Conformance versus utility | [domain_business_invariants](https://github.com/wa-pis/agent-paranoid-android/blob/6801997b763fa4b4ba9a27303b96ab507ab1f610/tests/test_domain_business_invariants.py), [client_golden_csv_acceptance](https://github.com/wa-pis/agent-paranoid-android/blob/6801997b763fa4b4ba9a27303b96ab507ab1f610/tests/test_client_golden_csv_acceptance.py) | Conformance assertions do not establish statistical utility. Current utility/hypothesis delivery and its installed regressions are linked from release evidence; no invented client score. |
| 15: Local-category preflight and limits | [local_category_policy](https://github.com/wa-pis/agent-paranoid-android/blob/6801997b763fa4b4ba9a27303b96ab507ab1f610/tests/test_local_category_policy.py), [postgres_query_builders](https://github.com/wa-pis/agent-paranoid-android/blob/6801997b763fa4b4ba9a27303b96ab507ab1f610/tests/test_postgres_query_builders.py) | Scopes and existing bounded preservation contract are tested; no global cap increase or source-value logging. |
| 16: SQL shape and rejection | [sql_query_source](https://github.com/wa-pis/agent-paranoid-android/blob/6801997b763fa4b4ba9a27303b96ab507ab1f610/tests/test_sql_query_source.py), [sql_query_adapters](https://github.com/wa-pis/agent-paranoid-android/blob/6801997b763fa4b4ba9a27303b96ab507ab1f610/tests/test_sql_query_adapters.py) | Supported shapes and fixed recovery diagnostics pass; JOIN/CTE expansion remains unsupported. |
| 17: Bounded aggregate work | [sql_query_profiling](https://github.com/wa-pis/agent-paranoid-android/blob/6801997b763fa4b4ba9a27303b96ab507ab1f610/tests/test_sql_query_profiling.py), [postgres_query_builders](https://github.com/wa-pis/agent-paranoid-android/blob/6801997b763fa4b4ba9a27303b96ab507ab1f610/tests/test_postgres_query_builders.py) | Fictional query-count/schema-drift/batch regressions distinguish 1.6.0 and candidate. No temporary writes or live latency/scan-byte claim. |
| 18: SELECT expression dependencies | [sql_query_adapters](https://github.com/wa-pis/agent-paranoid-android/blob/6801997b763fa4b4ba9a27303b96ab507ab1f610/tests/test_sql_query_adapters.py), [sql_query_profiling](https://github.com/wa-pis/agent-paranoid-android/blob/6801997b763fa4b4ba9a27303b96ab507ab1f610/tests/test_sql_query_profiling.py) | Unsupported automatic expression inference rejects. Owner-excluded internal SQL formula transfer is not silently implemented. |
| 19: Publication, overwrite and path identity | [io_path_policy](https://github.com/wa-pis/agent-paranoid-android/blob/6801997b763fa4b4ba9a27303b96ab507ab1f610/tests/test_io_path_policy.py), [client_publication_acceptance](https://github.com/wa-pis/agent-paranoid-android/blob/6801997b763fa4b4ba9a27303b96ab507ab1f610/tests/test_client_publication_acceptance.py) | Five content/exit/preservation cases plus deterministic atime/path-swap guards pass. Original 40-process probe is separately diagnostic, not universal crash/race proof. |
| 20: Doctor retention and repeatability | [cli_doctor](https://github.com/wa-pis/agent-paranoid-android/blob/6801997b763fa4b4ba9a27303b96ab507ab1f610/tests/test_cli_doctor.py), [cli_dependencies](https://github.com/wa-pis/agent-paranoid-android/blob/6801997b763fa4b4ba9a27303b96ab507ab1f610/tests/test_cli_dependencies.py) | Structured failures and missing extras pass after native-library discovery is configured. Twenty real fresh CLI doctor runs per package all exit zero; no remote service tested. |
| 21: Trino authentication | [trino_auth](https://github.com/wa-pis/agent-paranoid-android/blob/6801997b763fa4b4ba9a27303b96ab507ab1f610/tests/test_trino_auth.py), [trino_client](https://github.com/wa-pis/agent-paranoid-android/blob/6801997b763fa4b4ba9a27303b96ab507ab1f610/tests/test_trino_client.py), [trino_oauth_cli](https://github.com/wa-pis/agent-paranoid-android/blob/6801997b763fa4b4ba9a27303b96ab507ab1f610/tests/test_trino_oauth_cli.py) | Fictional six-method propagation/redaction is tested. Tentative external 1.6.0 plus server username/password does not establish historical application configuration or explain 401. |
| 22: Boolean SQL predicates | [sql_query_source](https://github.com/wa-pis/agent-paranoid-android/blob/6801997b763fa4b4ba9a27303b96ab507ab1f610/tests/test_sql_query_source.py), [sql_query_adapters](https://github.com/wa-pis/agent-paranoid-android/blob/6801997b763fa4b4ba9a27303b96ab507ab1f610/tests/test_sql_query_adapters.py) | AND/OR and forbidden-function controls pass without widening allowlists or resource budgets. |
| 23: Exact decimals | [exact_decimal_dataset](https://github.com/wa-pis/agent-paranoid-android/blob/6801997b763fa4b4ba9a27303b96ab507ab1f610/tests/test_exact_decimal_dataset.py), [exact_decimal_units](https://github.com/wa-pis/agent-paranoid-android/blob/6801997b763fa4b4ba9a27303b96ab507ab1f610/tests/test_exact_decimal_units.py), [parquet_decimal_profile](https://github.com/wa-pis/agent-paranoid-android/blob/6801997b763fa4b4ba9a27303b96ab507ab1f610/tests/test_parquet_decimal_profile.py) | Declared exact DECIMAL paths and typed outputs are tested; no float-to-exact recovery or preservation exemption. |
| 24: Physical Parquet types | [client_parquet_acceptance](https://github.com/wa-pis/agent-paranoid-android/blob/6801997b763fa4b4ba9a27303b96ab507ab1f610/tests/test_client_parquet_acceptance.py), [exact_decimal_dataset](https://github.com/wa-pis/agent-paranoid-android/blob/6801997b763fa4b4ba9a27303b96ab507ab1f610/tests/test_exact_decimal_dataset.py) | Declared valid-mode schema/readback passes. Original diagnostic overwrites its file pointer with negative output, so its final round-trip is not a valid-mode regression. |
| 25: Mode/ratio and artifact parity | [client_mode_installed_acceptance](https://github.com/wa-pis/agent-paranoid-android/blob/6801997b763fa4b4ba9a27303b96ab507ab1f610/tests/test_client_mode_installed_acceptance.py) | Spec/profile/CSV routing, effective settings, deterministic replay and intentional invalid exit 1 pass. Old probe rejects nonzero ratios with edge/load by contract and mislabels exit 1 as failure. |
| 26: Parquet metadata honesty | [source_adapters](https://github.com/wa-pis/agent-paranoid-android/blob/6801997b763fa4b4ba9a27303b96ab507ab1f610/tests/test_source_adapters.py), [parquet_decimal_profile](https://github.com/wa-pis/agent-paranoid-android/blob/6801997b763fa4b4ba9a27303b96ab507ab1f610/tests/test_parquet_decimal_profile.py), [identifier_pool](https://github.com/wa-pis/agent-paranoid-android/blob/6801997b763fa4b4ba9a27303b96ab507ab1f610/tests/test_identifier_pool.py) | Unknown statistics remain unknown and bounded supported distinctness is measured. No absent private Parquet or unknown null ratio is certified safe. |

## Original scripts and disclosed adaptations

Six original scripts were run unchanged on each package in new temporary roots:
`golden_run.py`, `probe_output_contract.py`, `probe_doctor_parquet.py` (base arm,
20 repeats), `rc_anchor_check.py`, `probe_mode_flags_ab.py` and
`probe_parquet_types_ab.py`. The controller bounds each run, selects its CLI
explicitly by PATH and clears external configuration. Only their fictional
self-contained fixtures are available; no private profiles/specs are supplied.

Both golden runs report six green and three red checks: source-enum copying is
intentionally unsupported by default, and the private snapshot/pair are absent.
The original script exits zero even with these reds. Each publication run
executes 40 fresh processes: 32 successes and eight intended filled-directory
rejections; its banner still incorrectly says 1.5.0. The maintained five-case
adaptation checks exit, file contents, layout and preservation, not mere file
existence. It passes on both actual packages. The original doctor base arm
reports 20/20 on each; separate real CLI doctor results are above.

The mode probe treats deliberate invalid publication exit 1 as a failure, passes
a nonzero invalid ratio to edge/load modes that forbid it, and compares hashes
as if they established semantics. Preserve its diagnostic output; the eight
maintained CLI mode cases assert actual settings/artifacts and pass. The Parquet
probe inspects both valid and negative arms, then uses the last (negative) file
for its round-trip: the resulting string types do not demonstrate valid-mode
type loss. Declared valid-mode physical schema/readback tests pass separately.

The Trino ladder script has a Python 3.11 SyntaxError at line 206 and its private
query is absent. Its product-monkeypatched arm is not an acceptance route. The
publication fix wrapper/runner also monkeypatch production code, so their fixed
arms are retained as diagnostic history and excluded from acceptance. Unpatched
installed SQL/publication controls above provide the reviewed replacement
scenarios. None of these exclusions is counted as a passing original probe.

Tests and their exact fictional example are copied outside the checkout. A
legacy `src` fixture path explicitly points to that arm's installed site-packages;
initial imports and subprocess checks verify installed-package provenance.
No application source checkout is imported. Reproduction uses the selected
interpreter with `-I -m pytest`, disabled automatic pytest plugins, the listed
32 test modules and `TEST_DATA_AGENT_ACCEPTANCE_PACKAGE_ROOT` set to installed
site-packages. Add the reviewed example for `test_conditional_formulas.py`.
The ledger retains controller, fixture and report hashes and every test case.
Parameter payloads are replaced by deterministic per-function case ordinals;
fixture hashes bind reconstruction without publishing sensitive-shaped test literals.

## Section E safeguards and remaining evidence

| Guard | Evidence / limit |
| --- | --- |
| E.0 identity/extras | Real public wheel hashes, byte-identical installed payloads, versions/dependencies above, doctor extra/capability checks in the ledger. No in-place product fix. |
| E.1 anchors | All 61 old anchors rebound independently on both installations in the ledger. Moved/absent strings are historical diagnostics, never proof of a runtime defect. Current test links bind the accepted source. |
| E.2 claims and before/after | All findings 1–26 above have an explicit supported, intentional, deferred or unverified disposition. Original script results remain separate from maintained assertions. No missing private snapshot, pair or query is passed. |
| E.3 seed/layout/routing/overwrite | Installed golden/mode/publication tests assert deterministic replay, flat artifacts, profile/spec routing, retained invalid output, exit semantics and overwrite. Path-identity/atime negatives remain executable. |
| E.3 dependencies/doctor | Missing-extra guards and retained structured failure tests pass; 20 fresh real CLI doctor runs per version exit zero. Native library discovery correction is disclosed. No actual remote connection attempted. |
| E.3 speed/resource limits | Fictional bounded query-count and preflight regressions pass on candidate. Live PostgreSQL latency/scan costs and the client's original table remain unverified; no temporary writes or higher default budgets. |
| E.4 record/harness review | This new source-bound ledger supplements earlier release records, retains initial harness failures and separates diagnostic probes, assertions and unavailable cases. |

This completes the accessible fictional matrix and reviewed local replay with
explicitly unavailable cases. It does **not** certify full private-client utility,
historical Trino 401 configuration, external profile provenance, final-public
1M × 100 configured transformation capacity or new preservation authority.
At this 2026-10-25 checkpoint the broad documentation audit remained open.
It subsequently [completed on 2026-10-29](documentation-consistency-2026-10-29.md);
remaining transformation capacity and amendment-review tasks stay open.
