# Parallel generation evidence

Implemented and unreleased, measured locally on 2026-11-21. This records the
standalone opt-in Python path, not completion of the full forecasting, streaming
or CLI/MCP performance proposal. All eighteen requested measurements completed,
with equal seeded CSV output at each row count.

## Implementation and compatibility

The public opt-in entry point is
`test_data_agent.adapters.parallel_generation.generate_dataset_parallel`, with
the typed `ParallelGenerationPolicy`. The pure tile generator owns deterministic
values; the adapter owns process lifecycle and resource policy. Existing
`generate_dataset`, CLI/MCP, approvals, artifact schemas and dependencies retain
their behavior. The new path has no source-row input or publication authority.

Engine `tiled-v1` uses immutable logical tiles of 4,096 rows. SHA-256 of engine,
seed, entity name and tile number derives independent RNG/Faker seeds. The
absolute row index retains global identifiers and repeated-key pools. Tile width
is part of the engine version and has no caller setting. One, two and four
workers generate identical ordered rows for the same specification, seed and
dependency versions. Values differ from legacy generation under the same seed.

The adapter snapshots the specification, validates its safety and row/cell
limits, then keeps at most one outstanding tile per worker. FIFO collection
preserves order. It stops and joins the pool before reusing the existing global
constraint solver and mandatory privacy/schema/relationship validation. It
returns the complete dataset and therefore uses O(rows) memory; no hard RSS cap,
constant-memory generation, semantic callbacks or business-rule files are added.

The multiprocessing context explicitly uses `spawn`, including the one-worker
baseline. A coordinator and resource tracker are additional processes. This
follows the [Python multiprocessing lifecycle guidance](https://docs.python.org/3.11/library/multiprocessing.html#using-a-pool-of-workers).
On POSIX, the coordinator defers SIGINT during startup until it holds the pool
reference; worker processes leave cancellation to the coordinator. Timeout,
failure and ordinary cancellation attempt both termination and join. Native
setup/submission/worker/cleanup errors are value-free; known parent budget and
interrupt exceptions are preserved. SIGTERM, SIGKILL, repeated interrupts or
OS-level cleanup failures cannot guarantee graceful cleanup.

## Benchmark method

[benchmark_parallel_generation.py](../../../scripts/benchmark_parallel_generation.py)
uses fresh coordinator processes, 100,000 and 750,000 rows x 25 fields, one/two/four
worker processes and three repetitions per combination. Worker order rotates
between repetitions; each run completes and cleans up before the next starts.
No other heavy checks run during the timed matrix. CPU affinity and cache purge
are not applied.

The source-free fixture has one unique integer key, followed by four repetitions
of integer, float, boolean, date, weighted category and string pattern. Seed 42,
valid mode, no semantic provider or global business-rule file. Every row's exact
global key and the final CSV SHA-256 are checked. All existing unconditional
generation validation runs; global rules are separately exercised in tests.

Each run explicitly supplies per-entity `max_rows=rows`, total
`max_cells=rows*25` and a 600-second `GenerationBudget`. The 750k case therefore
allows 18,750,000 generated cells without altering ordinary generation,
profiling or database limits. The CSV remains subject to the existing 512 MiB
output limit. No dataset is written to disk; only aggregate measurement JSON is
saved, so dataset temporary disk is zero (interpreter caches/OS semaphores are
outside this data metric).

Generation timing includes process startup, ordered transfer, cleanup, global
constraint solving and mandatory validation. Total adds CSV serialization and
UTF-8/hash work. Exact-key verification is separately timed and excluded from
total; full worker wall time also includes interpreter imports/spec creation and
verification. This is not the complete CLI bundle/publication workflow.

The monitor samples concurrent RSS for the coordinator and every descendant,
including resource tracker, using numeric `ps` PID/PPID/RSS output. The requested
interval is 0.1 seconds plus collection time. It records peak concurrent summed
RSS, sample count and process count. Coordinator `ru_maxrss` is separately
recorded. Reported peak is the larger of sampled process-tree RSS and coordinator
high-water RSS; independent per-process high-water marks are never added.
Short peaks between samples may be missed, and shared pages can count in more
than one process's RSS. The monitor itself is outside the workload process tree.

Host: Apple M4 Max, 14 cores, 36 GiB RAM, macOS 26.6.2 arm64, CPython 3.11.2,
Pydantic 2.13.4, Faker 40.35.0. The
[raw report](parallel-generation-results.json) records source hashes, versions,
policy and every run. The imported adapter's origin and contents were verified
against the recorded checkout hash outside the timed runs.
Reproduce on an otherwise idle host with:

```sh
.venv/bin/python scripts/benchmark_parallel_generation.py \
  --rows 100000 750000 --workers 1 2 4 --repeats 3 \
  --output parallel-generation-results.json
```

## Results and decision

Medians of three independent runs, with [minimum–maximum]. Time includes
generation, mandatory global checks, CSV serialization and UTF-8/hash work.
RSS is MiB, using the observed process-tree/coordinator high-water metric above.

| Rows x 25 fields | Workers | Total seconds [min–max] | Peak RSS MiB [min–max] |
|---|---|---:|---:|
| 100,000 | 1 | 10.277 [10.249–10.490] | 376.7 [369.0–383.5] |
| 100,000 | 2 | 8.039 [7.971–8.074] | 464.2 [454.4–479.2] |
| 100,000 | 4 | 6.892 [6.876–6.943] | 592.8 [585.1–632.1] |
| 750,000 | 1 | 72.314 [72.000–73.022] | 1940.4 [1935.2–1943.4] |
| 750,000 | 2 | 55.989 [55.696–56.404] | 1945.7 [1938.7–1953.0] |
| 750,000 | 4 | 47.668 [47.265–47.904] | 1935.9 [1932.9–1951.0] |

All nine runs at each size have the same complete CSV hash and exact unique
global key range. CSV payloads are 28,175,783 bytes at 100k and 211,321,616 bytes
at 750k, below the unchanged 512 MiB output limit. Maximum observed process
counts are 3/4/6: worker pool plus coordinator plus resource tracker.

| Rows x 25 | Workers | Generation + checks | CSV serialization | UTF-8/hash | Full worker wall |
|---|---|---:|---:|---:|---:|
| 100,000 | 1 | 9.759 | 0.519 | 0.010 | 10.662 |
| 100,000 | 2 | 7.515 | 0.514 | 0.010 | 8.404 |
| 100,000 | 4 | 6.385 | 0.512 | 0.010 | 7.241 |
| 750,000 | 1 | 68.549 | 3.683 | 0.082 | 72.883 |
| 750,000 | 2 | 52.208 | 3.698 | 0.083 | 56.587 |
| 750,000 | 4 | 43.892 | 3.674 | 0.081 | 48.320 |

Stage medians are computed separately and need not sum exactly to median total.
Exact-key verification adds approximately 0.01 seconds at 100k and 0.09 seconds
at 750k to full worker wall. Samples range from 61 to 625 per run. The coordinator
high-water mark caught CSV allocation peaks missed by the 0.1-second process-tree
sampling; the table therefore uses both measurements rather than only samples.

Four workers are the fastest measured choice on this host and fixture: 1.49x
versus one at 100k and 1.52x at 750k. At 100k, median peak RSS rises by 57%; at
750k, observed peak RSS is effectively unchanged within overlapping ranges,
because the complete dataset/CSV in the coordinator dominates the peak.
Retain conservative explicit opt-in selection; use four workers for the tested
large workload when memory permits. No universal worker-count heuristic is added.

The measured scaling is below the broader 2x performance target. Global
validation, CSV work and ordered IPC remain in the path; this matrix does not
separately profile their CPU shares. Full legacy/CLI bundle comparison, bounded
streaming validation/export and the overall performance acceptance remain open.
No comparison to the user's reported 20-minute workload is claimed.

## Correctness and failure evidence

- 54 focused tests pass: exact ordered rows/CSV for 1/2/4 processes in
  valid/mixed/negative modes, all field types, nulls, Unicode categories,
  Faker email/phone, two entities, identifier pools, tile boundaries/tail,
  seed replay/change and prefix stability. Linked keys, formulas and aggregate
  calculations reuse the global solver and are validated.
- Tests cover configured/explicit limits, bad policies, empty-field rejection,
  bounded outstanding jobs, unchanged caller specifications, mandatory safety
  despite disabled report flags, and value-free worker/future/setup/submission/
  cleanup failures. They preserve primary budget/interrupt identities and
  attempt join even if cleanup is interrupted.
- Real subprocess checks passed for deadline, worker `os._exit(7)`, native
  exception redaction, SIGINT during execution and SIGINT during pool startup.
  Each completed within four seconds with no active worker children left.
- Final full local suite passed 1,947 tests with 10 skips and 91.41% coverage,
  including all 54 focused parallel tests and the cleanup-interrupt regressions.
  The process adapter has 98% coverage and the pure tile generator 93%.
- Ruff across source/tests/scripts, mypy across the package and benchmark scripts,
  strict MkDocs and documentation tests passed. A wheel built offline and its
  installed base-only environment produced identical 1/2/4-worker results.
  The wheel contains the exact checked runtime modules; its SHA-256 is
  `52b3f67b0486edb25a2715082fb0cd56bfd516fe29611beed6b696fe57aa7feb`.

Python 3.12–3.14, Windows, external providers/databases, full bundle performance,
and peak hard-memory enforcement have not been exercised for this change.
No release, push, database operation or publication was performed.
