# Verification: Shared CSV Generation Validation

## Implementation And Regression Checks

Checked 2026-11-21:

- Full regression suite: **2,146 passed, 10 skipped**, 79.47 seconds.
- Package coverage: **91.5248%**, exceeding the existing 85% gate.
- `ruff check src tests scripts` passed.
- `mypy` passed for all 125 configured source files.
- Strict MkDocs build passed.
- `openspec validate shared-generation-validation --strict` passed.

Regression coverage includes canonical single-pass counts, exact reports and
settings, all generation modes, strict raw privacy even with disabled report
flags, mandatory ordering/fixed errors, normalized key aliases, relationships
and conditional constraints, input-error precedence/fail-fast, nonmutation and
fresh validation across calls. Public CSV tests cover invalid candidates before
encoding/publication, original bytes and reports, actual ordinary CLI exports
with explicit/saved CSV format, real streaming worker counts/partial tiles,
custom callbacks, post-callback mutation checks and existing atomic cleanup.

Independent runtime review found no remaining safety blocker. The spec-only CLI
now omits only its known unchanged no-op rule wrapper when no rule file exists;
actual/replaced callbacks and source-profile routes retain their boundaries.

## Repeated Public CSV Benchmark

All **12/12** measured attempts passed. The [benchmark report](benchmark.md) and
[raw JSON](public-csv-results.json) record the same environment/fixture/budgets as
the prior experiment, exclusive stage times, concrete validator call/row counts,
tree and coordinator RSS, source fingerprints, full CSV byte/hash equality to
the old result, repeat determinism and complete artifact/privacy/cleanup checks.
Independent review recomputed the summaries and checked source/evidence hashes.
No heavy tests ran concurrently with the performance series.

Legacy medians changed from 18.909 to 9.552 seconds at 100k and 140.921 to 70.874
seconds at 750k. Streaming changed from 11.141 to 6.084 and 80.160 to 41.957
seconds. Defaults, generation random calls/seed namespaces, serialized CSV and
manifest/report contracts are unchanged. Memory remains workload-dependent,
with whole-run streaming primary-key state growing with row count.

## Historical Evidence

The earlier public CSV benchmark files were not edited for this change. Their
SHA-256 values when preparing this proposal were:

| Historical file in `../public-streaming-csv/` | SHA-256 |
| --- | --- |
| `public-csv-results.json` | `2fe32ce83b36684aa561848f04cdc8e97bdc1bc829e963fc997876b953777cf5` |
| `public-csv-benchmark.md` | `673cc70d11ae5d50ec341f0d555c0bf0c78a488426f3e59339fe3f890a92fc52` |

Write new raw results and interpretation under `shared-generation-validation`.
The harness now defaults to this change's new raw-results path. Use a separate
explicit `--output` path when reproducing to preserve both recorded experiments.

No version bump, commit, release build, tag, push or publication was performed
for this task. The unrelated dirty worktree changes were retained.
