# Run-local distribution preparation: validation evidence

Measured 2026-11-21 on the same local host, before and after the two runtime
changes in generation/entity_generator.py and validation/schema_validator.py.
This validates the first optimization only; it does not complete the broader
capacity, 750k-row, batching or process-parallelism proposal. Unreleased.

## Method

The [checker](../../../scripts/check_generation_distributions.py) runs each source
version in a fresh, sequential worker process and alternates their order across
three repetitions. The baseline is a private copy of the complete source package
immediately before this optimization, including all earlier unreleased fixes.
There are no mocks or overridden model properties in this comparison.

The fictional specification has 25 fields: one unique integer primary key and
four repetitions of integer, float, boolean, date, weighted category and string
pattern. Seed 42, valid mode, no provider or business rules. Existing row/time
limits and all unconditional generation/schema/privacy checks remain enabled.
Only synthetic rows are produced; the report retains timing, RSS and CSV hashes.

Generation timing includes constraint solving and mandatory validation. Total
adds CSV serialization in memory. Worker wall time separately includes imports,
spec construction and hashing. This is not the complete CLI bundle workflow:
filesystem publication, its extra validation/report passes and external storage
are excluded. Peak RSS covers the complete worker including CSV hashing; this
optimization uses no child workers or spill files. No other heavy jobs ran during
measurement; no CPU affinity or cache purge was applied.

Environment: Apple M4 Max, 14 cores, 36 GiB RAM, macOS 26.6.2 arm64,
CPython 3.11.2, Pydantic 2.13.4 and Faker 40.35.0. Full settings, source-file hashes
and all twelve measurements are in [generation-distribution-results.json](generation-distribution-results.json).

## Results

Medians of three runs; times in seconds and RSS in MiB.

| Rows x 25 fields | Version | Generation + checks | CSV serialization | Total [min–max] | Peak RSS |
|---|---|---:|---:|---:|---:|
| 10,000 | Before | 1.421 | 0.046 | 1.467 [1.455–1.468] | 85.1 |
| 10,000 | Prepared | 0.856 | 0.045 | 0.902 [0.901–0.903] | 85.0 |
| 100,000 | Before | 14.175 | 0.470 | 14.645 [14.549–14.717] | 290.0 |
| 100,000 | Prepared | 8.476 | 0.470 | 8.942 [8.924–8.953] | 289.7 |

At 100k rows, generation plus mandatory checks takes 40% less time; including
CSV serialization takes 39% less time. Memory and CSV serialization are
essentially unchanged. CSV SHA-256 matches across all six runs at each size.
No speedup is claimed for Faker-heavy, formula-heavy or linked workloads.

Reproduce with package directories from the two source versions:

```sh
.venv/bin/python scripts/check_generation_distributions.py \
  --baseline-source /path/to/before/src --candidate-source src \
  --rows 10000 100000 --repeats 3 --output generation-check.json
```

## Correctness

Seven focused tests compare prepared and unprepared paths, including exact rows,
CSV and provider requests in valid/mixed/negative modes; nulls, identifier pools,
numeric/string/category/date distributions, timezone timestamps, sensitive Faker
email and two entities. They also verify that parse work scales with fields,
metadata edits are observed between calls and validation remains non-mutating.
An independent replay check additionally confirmed identical RNG and Faker
states across three seeds and all three modes.

The optimization keeps per-call metadata only. It changes no public generation
API, schema, manifests, dependencies, resource limits or random stream. Invalid
in-place distribution edits can fail earlier during preparation, as documented
in the design. Batches, parallel workers and a new generation engine remain
outside this change.

Final local checks: 1,893 passed, 10 skipped; coverage 91.34% (85% required).
Ruff across source/tests/scripts, mypy across the package and new checker, strict
MkDocs build and whitespace checks passed. The standalone checker also passed a
103-row two-version smoke run. Python 3.12–3.14, live databases/providers and
multicore scaling were not exercised for this change. No release or publication
was performed.
