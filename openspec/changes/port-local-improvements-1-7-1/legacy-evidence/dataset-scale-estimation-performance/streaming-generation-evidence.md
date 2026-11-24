# Streaming Generation Backend Comparison

Benchmark-only experiment, 2026-11-21. The public row-returning API, CLI/MCP,
approval, manifest and source-overlap workflows do not select these sinks.

## Result And Decision

For this generation workload, keep streaming Python/Arrow as the candidate.
DuckDB adds 1.9% elapsed time at 100k and 10.0% at 750k, with 7.5% and 42.5%
more peak process-tree RSS respectively. It offers no measured generation or
memory advantage here. This does not change the separate large-profile DuckDB
decision: profiling tracks many distinct-value columns, whereas this fixture
needs just one global primary-key set and no SQL joins or aggregates beyond
count/distinct. Production streaming integration remains a separate task.

Host: Apple M4 Max, 14 logical CPUs, 36 GiB RAM, macOS 26.6.2 arm64,
Python 3.11.2; Pydantic 2.13.4, Faker 40.35.0, PyArrow 25.0.0, DuckDB 2.0.1.
Twelve runs completed; all mandatory checks and historical CSV hashes passed.

Median [minimum–maximum], three fresh-process repetitions:

| Rows × fields | Backend | Total seconds | Peak tree RSS, MiB |
| --- | --- | ---: | ---: |
| 100,000 × 25 | Python/Arrow | 6.258 [6.233–6.283] | 574.2 [572.0–577.3] |
| 100,000 × 25 | + DuckDB | 6.379 [6.340–6.383] | 617.2 [614.0–622.0] |
| 750,000 × 25 | Python/Arrow | 43.346 [43.163–43.495] | 782.5 [777.5–789.0] |
| 750,000 × 25 | + DuckDB | 47.666 [47.235–47.927] | 1114.9 [1099.2–1170.6] |

Coordinator stage medians, seconds:

| Stage | 100k Arrow | 100k DuckDB | 750k Arrow | 750k DuckDB |
| --- | ---: | ---: | ---: | ---: |
| Generation wait / IPC / pool / bookkeeping | 0.500 | 0.471 | 0.662 | 0.584 |
| Mandatory validation / solving | 4.684 | 4.672 | 34.751 | 35.226 |
| Arrow conversion | 0.094 | 0.094 | 0.682 | 0.684 |
| DuckDB ingest | 0 | 0.159 | 0 | 3.900 |
| Whole-run key/count checks | 0.013 | 0.003 | 0.099 | 0.021 |
| Readback / Arrow-to-Python | 0.433 | 0.469 | 3.218 | 3.878 |
| CSV encoding / write / SHA-256 | 0.515 | 0.434 | 3.884 | 3.256 |
| Setup / fsync / cleanup | 0.022 | 0.068 | 0.026 | 0.162 |

Validation is the dominant measured coordinator stage and remains enabled.
DuckDB saves about 0.078 s on the 750k global key check, but adds about 3.9 s
of ingestion and more readback work. No pure worker-generation time is inferred
from the residual wait stage; see the overlap definition below. Median complete
worker wall times including interpreter/import overhead are 6.542 / 6.639 s
at 100k and 43.624 / 47.934 s at 750k for Arrow / DuckDB.

Arrow has no spill. DuckDB has no observed spill at 100k, and an observed
191.5–192.1 MiB of spill at 750k (median 192.1 MiB). All temporary directories,
including actual spill files, were removed before success; every run asserted
private directory/output modes. The total scratch observation includes CSV;
the raw JSON records total scratch and spill separately. These are sampled
observations, not exact disk high-water marks.

## Reproduce

```bash
python scripts/benchmark_streaming_generation.py \
  --output openspec/changes/dataset-scale-estimation-performance/streaming-generation-results.json
```

Install the existing `profiling` extra for DuckDB and PyArrow. The monitor needs
read access to numeric `ps -axo pid=,ppid=,rss=` process statistics. No database,
source files or external AI service is used. Only metadata and digests remain
in the [raw measurements](streaming-generation-results.json); each synthetic
CSV and private DuckDB spill directory is removed before a run is accepted.

Both sinks use the same `fictional_spec` as the
[materialized parallel benchmark](parallel-generation-evidence.md): one primary
key plus 24 repeated integer/float/boolean/date/categorical/pattern fields,
valid mode, seed 42, `tiled-v1`, four spawned workers and 4,096-row logical tiles.
The FIFO queue has at most four tiles in flight and the consumer retains one
tile at a time. Tests cover a partial last tile. Three repetitions per backend
and size use fresh coordinators; backend order alternates between repetitions.
The host OS file cache is not reset. No other heavy task is intentionally run
alongside the benchmark; sampling and other desktop activity still add noise.

The Python/Arrow sink converts each validated batch to explicitly typed Arrow,
tracks global primary keys in a Python set, and writes CSV incrementally. The
DuckDB sink consumes the same Arrow batches, stores them in an in-memory table
with bounded spill, checks global count/distinct, then streams a relation sorted
by an explicit ordinal back through Arrow and the common CSV writer. SQL names
are fixed ordinal columns; specification names are never SQL identifiers.
Both use `csv.writer`, `neutralize_csv_cell`, UTF-8/CRLF, incremental SHA-256,
the output byte cap, `atomic_binary_writer`, flush/fsync and private staging.
No full-dataset Python list, Arrow table or CSV string is assembled.

DuckDB uses one execution thread, one asynchronous I/O thread, a 128 MiB buffer
setting and 2 GiB spill cap. External access, automatic extensions, Python
replacement scans and logging are disabled. Queries receive the remaining
native deadline; the shared generation budget is 600 seconds and the monitor
has a 660-second outer deadline with owned-process-group cleanup. DuckDB's
buffer setting is [not a total RSS cap](https://duckdb.org/docs/2.0/operations_manual/limits).
Readback uses a [relation's streaming Arrow reader](https://duckdb.org/docs/2.0/guides/python/export_arrow),
not a DBAPI reader that first copies all results.

## Timing And Memory Interpretation

Each stage is coordinator wall time. `generation_ipc_pool` is the residual
parent wait, IPC, pool lifecycle and bookkeeping, including scratch sampling.
Workers continue computing during consumer validation/conversion/writing; their
overlapping compute is not reported as pure generation CPU or added again.
`validation` includes the existing solver and unconditional privacy/schema checks
per batch. `backend_readback` includes Arrow-to-Python conversion for both sinks,
and relation creation/query execution/reader iteration for DuckDB. The common
CSV stage includes encoding, incremental writes, output-cap checks and hashing;
setup/cleanup includes imports, connection setup, final fsync and temp removal.
Stage medians need not sum exactly to the median total. `worker_wall_seconds`
also includes interpreter startup/imports and monitor completion latency.

Peak memory is the maximum sampled simultaneous RSS sum for the coordinator
and all descendants, including workers and the multiprocessing helper. Samples
are taken approximately every 100 ms plus `ps` overhead. Coordinator OS
high-water RSS is recorded separately; it is never added to worker high-water
marks from different times. The table uses the larger of the sampled tree peak
and coordinator high-water mark. RSS can double-count shared pages and brief
peaks can be missed. Neither path has a hard OS RSS cap. Python key tracking is
O(rows), even though row payloads and CSV serialization are batched. Scratch
observations are sampled after batches/queries; they are not exact disk peaks.

## Correctness And Safety

Every tile runs existing `solve_constraints` and
`assert_generated_dataset_valid` with its exact batch row count. Privacy and
schema checks run even when report flags are disabled, before any generated
value enters Arrow, DuckDB or the file. Global key uniqueness and total row
count are also checked before the private CSV is atomically published. A unique
key makes complete rows distinct. The experimental guard rejects constraints,
relationships, multiple entities and non-valid mode before generation; it never
silently replaces global solving for a general specification with batch checks.

All CSV fingerprints must agree between backends and repeats, and with the
previous complete materialized `tiled-v1` output:

| Rows | CSV bytes | SHA-256 |
| ---: | ---: | --- |
| 100,000 | 28,175,783 | `76330b20f138af1c8b49d42fe8780057cd0b735895a98b0d98713cf715ab9979` |
| 750,000 | 211,321,616 | `735b3374822b27e5afccaa73ebde1773ae43b7e93a1f9f06c43c8535f22a4405` |

The driver accepts a run only after exact row count, global uniqueness,
0700 scratch, 0600 output and scratch-removal assertions pass. Its JSON stores
dependency/platform/settings metadata and SHA-256 for the benchmark scripts
and every package Python file, including uncommitted changes.

Focused regression tests exercise both sinks across a tile boundary, exact CSV
scalar/null/Unicode/quoting/boolean/float/date behavior and formula neutralization;
cross-batch duplicate keys; privacy/type/shape/null rejection before Arrow;
unsupported specifications; output/time bounds; existing-file preservation;
tile sequence/count mismatches; cancellation; native failures during register,
insert, global checking, readback and close; value-free errors and temp cleanup.
Shared visitor tests retain bounded scheduling, immutable spec snapshots,
worker failures, redaction, deadlines and cancellation lifecycle checks.

## Verification

Completed on the final working tree, with synthetic fixtures only:

- Full pytest with the package coverage gate: **1,996 passed, 10 skipped** in
  68.49 s; **91.42% coverage**, above the required 85%.
- Streaming sink tests: 43 passed; shared parallel/visitor tests: 60 passed.
- Ruff over `src tests scripts`; mypy over 124 package files and the three
  benchmark scripts; compileall over `src tests scripts`: passed.
- `mkdocs build --strict` and
  `openspec validate dataset-scale-estimation-performance --strict`: passed.
- All 12 row/key/privacy/file-mode/cleanup checks, same-seed and complete-reference
  hashes passed. Every run's coordinator stage sum equals its reported total.
- Independent read-only review found no blocking defect in the fixture path;
  timing interpretation and mandatory-result acceptance checks were clarified
  before the timed runs.

The raw report retains the source hashes actually measured. The only source
change after measurement added the local `result: dict[str, Any]` annotation
for mypy; no executed expression changed. Exact one-line source comparison and
normalized AST equality passed; all other measured source hashes still match.
Both hashes and this verification are recorded under
`post_measurement_validation` in the raw JSON. A rerun on the final tree should
be assessed using these two explicitly distinguished source snapshots.

This is a CSV, flat valid-schema experiment. Global rules, relationships,
negative/mixed modes, separate business-rule callbacks, source-row overlap,
Parquet, CLI/MCP publication, hard process RSS enforcement and release
acceptance are not established by it. Existing general generation and reviewed
workflows retain their global checks and do not route through the prototype.
