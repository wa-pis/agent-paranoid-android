# Public CSV benchmark methodology

The benchmark measures the unchanged public `generate_dataset_bundle` API using
[`scripts/benchmark_public_csv.py`](../../../scripts/benchmark_public_csv.py).
Raw runs, environment details, source hashes and summaries are recorded in
[`public-csv-results.json`](public-csv-results.json).

## Results

Measured 2026-11-21 on Apple M4 Max, 14 logical CPUs, 36 GiB RAM,
macOS 26.6.2 arm64; Python 3.11.2, Faker 40.35.0, Pydantic 2.13.4 and
PyYAML 6.0.3. Both paths use this same checkout and environment. These are
repeated public Python API measurements; the earlier minimum-dependency installed
CLI acceptance timings are a separate experiment.

Times are medians of three runs, with observed ranges. RSS columns are maxima
across those runs; the coordinator high-water mark is separate from sampled
concurrent tree RSS.

| Rows × fields | Public path | API seconds (range) | Peak sampled tree RSS, MiB | Peak coordinator RSS, MiB |
| --- | --- | ---: | ---: | ---: |
| 100,000 × 25 | Legacy, serial | 18.909 (18.714–19.068) | 301.9 | 304.4 |
| 100,000 × 25 | Streaming, 4 workers | 11.141 (11.091–11.225) | 569.5 | 145.5 |
| 750,000 × 25 | Legacy, serial | 140.921 (140.046–142.714) | 1,939.3 | 1,940.6 |
| 750,000 × 25 | Streaming, 4 workers | 80.160 (79.588–80.427) | 764.4 | 232.0 |

Streaming is 1.70× faster at 100k, but its worker processes increase total sampled
RSS by 88.6%. At 750k it is 1.76× faster and lowers sampled tree RSS by 60.6%.
This supports retaining explicit streaming for larger datasets; this experiment
does not locate an automatic crossover threshold.

Exclusive stage medians, seconds:

| Stage | 100k legacy | 100k streaming | 750k legacy | 750k streaming |
| --- | ---: | ---: | ---: | ---: |
| Setup / remaining bookkeeping | 0.015 | 0.019 | 0.104 | 0.020 |
| Generation / IPC / coordinator wait | 4.109 | 0.513 | 30.365 | 0.594 |
| Mandatory validation | 9.237 | 4.700 | 69.197 | 35.179 |
| Report validation | 5.044 | 5.173 | 37.582 | 38.815 |
| Streaming global checks / tile preparation | — | 0.273 | — | 2.041 |
| CSV formatting / UTF-8 encoding | 0.478 | 0.449 | 3.534 | 3.353 |
| File writes / atomic file finalization | 0.008 | 0.011 | 0.110 | 0.068 |
| Artifact construction / hashes / size checks | 0.023 | 0.021 | 0.099 | 0.093 |
| Complete directory publication | 0.000156 | 0.000133 | 0.000142 | 0.000151 |

Each run's exclusive stages sum to its API wall time. Independently computed
stage medians need not sum to the median total. Workers generate while the
coordinator validates earlier tiles, so streaming's generation/wait entry does
not measure all worker computation. The legacy duplicate mandatory assertion
accounts for part of the observed advantage; this is not a streaming-only
speedup. Mandatory and report validation together consume approximately 74 of
80 seconds in the 750k streaming run. A future optimization should examine
repeated validation work while retaining every invariant.

All 12 attempts passed: exact header/count/ordered unique keys, all four report
sections, manifest engine/flags/row counts and complete output hash maps,
private permissions, no partial staging and removed temporary directories.
Every run checks mandatory/report invocation counts and row coverage. All three
CSV hashes match within each of the four size/path cases. Streaming output also
matches the earlier full materialized `tiled-v1` reference at both sizes.
Cross-engine hashes differ as designed. CSV sizes are 28,177,934 / 28,175,783
bytes at 100k and 211,322,612 / 211,321,616 at 750k (legacy / streaming).

The 750k conservative preflight estimate is 2,496,078,334 bytes, explaining the
shared 4 GiB benchmark budget despite the much smaller actual CSV. No default
limits or production code changed. All recorded source hashes still match the
final tree; an independent review recomputed the summaries and checked coverage,
hashes, permissions and cleanup. The harness regression tests passed **17/17**,
including an actual spawned streaming smoke; focused Ruff and strict OpenSpec
checks passed. The full package suite was not rerun for this benchmark-only task.

Reproduce without overwriting this evidence:

```bash
.venv/bin/python scripts/benchmark_public_csv.py \
  --rows 100000 750000 --repeats 3 --output /private/tmp/public-csv-results.json
```

## Workload and comparison

Both paths use the same fictional, valid-mode specification: one entity with
100,000 or 750,000 rows, 25 fields, seed 42, and no relationships, constraints
or business-rule applier. The fields comprise an integer primary key and 24
fields cycling through integer, float, boolean, bounded date, categorical string
and bounded string-pattern distributions. No source dataset is used.

Legacy export calls the public API without a streaming policy and generates
serially. Streaming export passes a four-worker `ParallelGenerationPolicy`,
using fixed 4,096-row `tiled-v1` tiles. These engines use different random
streams, so cross-path CSV equality is not expected. Each path must reproduce
its own CSV SHA-256 across repetitions of the same row count.

There are three repetitions per path and size, each in a fresh subprocess using
the same Python executable, dependencies, fixture and environment. Order is
legacy/streaming, streaming/legacy, then legacy/streaming for each size. This is
an end-to-end comparison of the public paths, including their different engines
and worker counts; it does not isolate streaming's contribution alone.

## Safety checks and budgets

Schema, relationship, constraint and privacy report checks remain enabled, and
all mandatory checks execute. Legacy performs mandatory validation inside the
generator and again in the bundle workflow, followed by report validation.
Streaming performs mandatory and report validation on every tile, then checks
normalized primary-key uniqueness and exact whole-run counts. Its whole-run key
set grows with row count even though tile rows are bounded. The fixture's
applicable invariants match, while the number and placement of passes differ.
The harness checks validator call counts and row coverage explicitly.

Both subprocess paths receive the same finite environment limits: 750,000 rows,
4 GiB output and 600 seconds of generation time. Streaming additionally permits
18,750,000 cells. Legacy retains its conservative preflight output estimate;
the larger benchmark cap allows the requested workload without changing runtime
defaults or bypassing actual-byte, disk-space or deadline checks. An external
660-second subprocess deadline bounds stalled runs.

## Time and memory measurement

`api_seconds` surrounds only the public API call. Imports, fixture construction,
process startup and the independent artifact audit are outside this interval.
Nested wrappers call original functions and record exclusive wall time; their
stage totals are checked against API elapsed time. A streaming-only budget proxy
delegates every original check and observes existing phase labels.

| Stage | Work included |
| --- | --- |
| `setup_and_bookkeeping` | Public workflow setup, streaming setup/pool creation, and remaining bookkeeping. |
| `generation_ipc` | Legacy generator excluding nested validation; streaming task submission, worker/IPC waits and pool shutdown. |
| `mandatory_validation` | Original unconditional generated-dataset assertions. |
| `report_validation` | Original dataset-validation report calls. |
| `global_checks` | Streaming tile preparation/sequence checks and normalized whole-run primary-key/count checks. |
| `csv_encoding` | CSV serialization and UTF-8 encoding on both paths. |
| `csv_write` | CSV writes and shared atomic file flush, sync and replacement. |
| `artifacts_and_hashing` | Specification/report/manifest construction and encoding, output hashing and final size checks, excluding nested byte writes. |
| `publication` | Atomic publication of the complete bundle directory. |

Streaming final count checks begin after tile visitation returns; final writer
flush/sync remains in `csv_write`. Generation/IPC time is coordinator wall time,
not a sum of worker CPU times. The shared bounded-text helper also sends the
three small control artifacts through the instrumented atomic writer, so their
byte writes count in `csv_write`. Stage labels are therefore approximate at that
boundary; API wall time is unaffected. Instrumentation overhead remains included.

The parent samples `ps` RSS at a nominal 0.1-second interval and sums the
coordinator and every descendant concurrently. Sampling covers subprocess
lifetime, including imports/startup. Short peaks can be missed and shared pages
can be counted repeatedly; this is sampled process-tree RSS, not physical memory
usage. Coordinator `ru_maxrss` is recorded separately and never added to tree RSS.

## Independent audit and reporting

After the measured subprocess exits, the parent streams the CSV to verify its
exact header, 25-cell rows, requested row count and ordered primary keys
`42_000_001 + index`; this also proves key uniqueness without an audit key set.
It checks all four successful report sections, manifest metadata, the exact
artifact/hash map and every recorded output hash. The streaming report summarizes
the last tile; validator coverage and whole-run checks establish full-run coverage.

Each run uses a private temporary directory (0700) and artifact files (0600).
The audit verifies permissions and absence of leftover staging artifacts; cleanup
terminates the process group and removes temporary output. Only metadata, hashes
and summaries are retained. Every attempt is recorded, including failures;
success summaries report medians/ranges and separate tree/coordinator RSS maxima.
Completion requires successful audits, cleanup and within-engine repeat hashes.
