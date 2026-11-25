# Human review guide — PR #718

Review [PR #718](https://github.com/wa-pis/agent-paranoid-android/pull/718)
against `origin/main` at `49d12c515c3aa7d012b038c5d1c96b50195fbcc1`.
This inventory is pinned to **`0529fb43ce1dbe85bb948623f83a66ac58500fdd`**:
284 changed files, including **40 production source files**, **63 test/fixture
files** and **130 immutable historical evidence files**. Later documentation
commits may increase the file count; review any later code delta separately.

## Status and evidence

Automated agent reviews and focused rechecks cover the implementation through
`0529fb43`, including the final DuckDB initialization-order fix. The last fix
passed the same 63 focused tests in both minimum and locked dependency
environments. These are automated checks, **not human review or approval**.
Require passing PR checks for the exact current head; a green result on an older
SHA does not approve a later code change.

**Human review is pending.** This guide assigns no reviewer and records no human
approval. A human reviewer must inspect the changes and record their own decision
against an explicit SHA. Dataset approval, transformation activation and release
acceptance remain separate decisions.

Read [design](design.md) and the [public contract](specs/public-contracts/spec.md)
first. [Final review](final-review.md), [checks](final-review-checks.json) and the
[runtime manifest](final-runtime-policy.json) are evidence for `1a40ad08`, not
claims that later commits were included in that historical run. The earlier
[verification](verification.md), [release parity](release-parity/comparison.json)
and [development sync](development-sync.md) retain their own revision boundaries.
Use the [legacy index](legacy-evidence-index.json) to verify the 130 archived
files; their old timings are not measurements of this PR.
The [CI follow-up](ci-followup.md) records 51 passing checks at `0529fb43`.
The [fresh CSV campaign](public-csv-current.md) records 16 checked runs of that
implementation, with its timing and memory limitations.

## Suggested reading order

Paths below are relative to the repository root. Start with the named files,
then follow their changed callers; review all 40 source changes before approval.

| Area | Source files to inspect | Questions and matching tests |
| --- | --- | --- |
| Shared semantics and privacy across sources | `core/semantics.py`, `core/privacy.py`, `safety.py`; `adapters/{csv_file,legacy_profile,parquet_dataset}.py`; `csv_profiler.py`, `postgres_profiler.py`, `sql_query_{source,profiling}.py`, `trino_masking.py`, `io/transformation_source.py` | Do weak SSN/card/secret signals remain sensitive while semantics require context? Do native numerics, aliases and every source label receive the same guards? Missing schema/aggregate evidence must stay unknown, with no added source-row reads or broader SQL. Read `test_privacy_semantic_accuracy.py`, `test_source_{name,numeric}_privacy.py`, `test_source_profile_safety.py`, `test_query_source_privacy_provenance.py`, `test_parquet_source_policy.py` and `test_column_semantics.py`. |
| Exact distinct counts and private spill | `profiling/{schema_profiler,duckdb_distinct,budget,cache}.py`, `core/limits.py`, `csv_profiler.py` | Does the crossing value survive the set-to-DuckDB handoff, using the same iterator? CSV has no 10,000 ceiling; released bounded Parquet evidence remains exact/lower-bound/unknown as applicable. Check keyed tokens, owned scratch, all error/cancellation cleanup, quotas and deadlines. At `0529fb43`, scratch is configured before the external-access ban; denial and configuration lock precede reader registration. Read `test_{single_csv_distinct,duckdb_profiling,duckdb_distinct_security,duckdb_optional,schema_distinct_overflow,profile_port_release_boundaries}.py`. |
| Generation, exact calculations and validation | `generation/{entity_generator,tiled_generator,constraint_solver,planner}.py`, `adapters/parallel_generation.py`, `rules/{expressions,typed_values}.py`, `validation/{schema_validator,values,constraint_validator,reconciliation}.py` | Preserve released ordinary/scalable engines, modes, exact DECIMAL, relationships, scenarios and every validation/privacy check. Tiled generation is explicit and has its own deterministic namespace. Inspect formula/aggregate dependency order and integer overflow checks. Read `test_calculation_dependencies.py`, `test_port171_tiled_compatibility.py`, `test_parallel_generation.py`, `test_{schema_validation,normalization,generation_dispatch,string_generation,privacy_validation}_equivalence.py` and `test_validation_values.py`. |
| Public CSV and atomic output | `io/{streaming_csv,workflows,writers,commands,artifacts}.py`; `cli.py`, `cli_{application,commands,parser,dependencies,doctor}.py` | Streaming stays opt-in; unsupported relations/rules retain the current path. Check equivalent checks and deterministic results for the same engine/settings/seed, bounded worker admission, typed CSV encoding, final privacy validation and atomic publication/rollback. No source rows may feed generated output. Read `test_streaming_csv_{export,bundle,cli}.py`, `test_combined_generation_validation.py`, `test_csv_{encoding_equivalence,validation_reuse,pipeline_regressions}.py` and the paired/public CSV benchmark tests. |
| Compatibility and resource boundaries | `trino_work_budget.py` plus the shared files above; `pyproject.toml`, `uv.lock`, `.github/dependency-compatibility.toml`, constraints/CI, schemas and public docs | DatasetSpec 1.1 and exact DECIMAL remain compatible. Cache 12 must reject 10/11; unknown profile metadata must not become invented evidence. The optional profiling extra must not affect small/base-only usage. Check saved-plan fingerprints, local-category authorization, SQL policy 1.2, reviewed numeric overrides and minimum dependencies. Read `test_reviewed_csv_numeric_fields.py`, `test_dependency_compatibility.py`, `test_installed_package.py`, `test_release_artifacts.py` and `test_transformation_receipt.py`. |

All source paths in the table are under `src/test_data_agent/`; all named tests
are under `tests/`.
The 63 test/fixture paths include the independently labelled accuracy corpus and
the generation-manifest fixture; review changed expectations as well as code.

## Commit checkpoints

- [47543ce3](https://github.com/wa-pis/agent-paranoid-android/commit/47543ce3):
  main port onto 1.7.1; [bd19407a](https://github.com/wa-pis/agent-paranoid-android/commit/bd19407a)
  integrates the current development baseline and records source-freshness policy.
- [77096f93](https://github.com/wa-pis/agent-paranoid-android/commit/77096f93):
  released FLOAT coercion and suppression of sensitive computed summaries.
- [1a40ad08](https://github.com/wa-pis/agent-paranoid-android/commit/1a40ad08):
  exact INTEGER quantiles, constant FLOAT endpoints and cache 12. Corpus labels
  and the privacy guard remain intact.
- [c855178b](https://github.com/wa-pis/agent-paranoid-android/commit/c855178b):
  example SQL-policy expectations;
  [b8fc1c2b](https://github.com/wa-pis/agent-paranoid-android/commit/b8fc1c2b):
  three scoped secret-scan false-positive fingerprints. Confirm these do not
  become broad exclusions.
- [0529fb43](https://github.com/wa-pis/agent-paranoid-android/commit/0529fb43):
  Linux-safe DuckDB setup in production and synthetic benchmark paths, with
  live-setting, no-consumption and failure-cleanup regressions.

## Reviewer checklist

- [ ] Confirm the exact head and review any delta after `0529fb43`.
- [ ] Inspect the five areas above and their changed test expectations; keep
  schema-only/aggregate-only sources unknown when evidence is absent.
- [ ] Confirm privacy, source provenance, scratch cleanup and existing budgets
  remain enforced; engine memory limits do not claim a total-process RSS cap.
- [ ] Confirm deterministic released behavior, exact DECIMAL, explicit tiled/
  streaming admission and atomic output; examine the intentional calculation
  ordering correction separately from unchanged release-parity cases.
- [ ] Require current-head CI, including minimum profiling dependencies, supported
  Python versions, packaging/schema checks and applicable disposable integrations.
- [ ] Read the fresh 100,000/750,000 × 25-field CSV campaign and its engine,
  timing and sampled-RSS limitations. Archived benchmarks remain historical;
  neither campaign certifies real-world detector accuracy.
- [ ] Record the human reviewer, reviewed SHA, findings and approval/request for
  changes in the PR. Do not count an agent report as that human decision.
