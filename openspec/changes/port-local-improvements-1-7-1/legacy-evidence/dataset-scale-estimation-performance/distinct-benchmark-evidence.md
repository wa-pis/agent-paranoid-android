# Exact distinct benchmark: Python set, DuckDB and SQLite

Historical component experiment. The subsequent
[streaming profiling implementation](../streaming-duckdb-profiling/proposal.md)
and its [full-pipeline validation](../streaming-duckdb-profiling/validation.md)
now cover the production handoff; the measurements below are unchanged.

Measured on 2026-11-20. This experiment selects a candidate for the growing
exact-distinct state in folder CSV profiling. It does **not** measure complete
CSV profiling, generation, validation or export. No production code or project
dependency was changed.

## Decision

Select **streaming DuckDB over bounded digest batches** as the candidate for
large, high-cardinality profiling. At 750,000 × 25 unique values it used a median
384 MiB peak RSS versus 2,982 MiB for Python set (7.8× less), with 11.82 s versus
10.88 s total time (8.6% slower). It used approximately 1.30 GiB temporary disk.
This is a memory improvement, not a demonstrated CPU speedup.

Retain Python set as the current default. It won every time comparison and is
more memory-efficient for low-cardinality inputs. At 10k rows DuckDB added about
76–79 ms (47–52%); at 100k unique rows it saved only 20% RSS while taking 12%
longer. These results do not justify a universal replacement or a guessed
automatic switching threshold.

Do not select SQLite for the proposed large-data path: its 194 MiB RSS was the
lowest for 750k unique rows, but 65.31 s was 5.5× slower than streaming DuckDB.
Reject table-staged DuckDB for this operation: persisting every digest, WAL and
transaction state add avoidable memory and I/O. Keep its measured results as
negative evidence, not as the preferred DuckDB implementation.

A runtime integration is separate work: retain full sensitivity scanning,
normalization and exact counts; validate complete safe-profile equivalence,
source snapshot binding, deadline/cancellation and no partial cache publication.
Raw source values must not enter DuckDB spill. Even digest spill requires an
explicit sensitive-data design: ordinary SHA-256 is not anonymization. Do not
add a general SQL surface or a universal storage-backend framework.

## Environment and method

- Apple M4 Max, 14 physical/logical cores, 36 GiB RAM; macOS 26.6.2 arm64.
- CPython 3.11.2, DuckDB 2.0.1, PyArrow 25.0.0, SQLite 3.39.4.
- Local APFS `/private/tmp`, approximately 59 GiB free before the experiment.
- All timed workers ran sequentially in fresh processes; normal desktop host,
  no CPU affinity, OS cache purge or claim of an otherwise idle machine.
- Original 54-run series: Python/table-DuckDB/SQLite order rotated each repeat.
  Subsequent 18-run series: streaming DuckDB only. Thus comparisons between
  stream and other engines are separate same-host series, not interleaved runs.
- Three repeats per configuration; unique and low-cardinality (100 values per
  column) fixtures at 10k, 100k and 750k rows, always 25 columns. Seed 1729.
- Identical lazy synthetic string generation, `.strip()`, UTF-8 SHA-256 and
  row-major `(column_id, 32-byte digest)` batches of at most 2,000 × 25 cells.
  No complete input list, source file or real row is loaded. Tuple batches are
  common comparison overhead; current production set insertion is per-cell.
- Each worker verifies all 25 exact counts independently against the fixture.
  All **72/72** measured runs passed. Separate smoke/pilot runs are excluded.
- Python uses one set per column. SQLite uses a disk database, one transaction,
  `executemany`, `INSERT OR IGNORE` and compound PK `WITHOUT ROWID`; journal and
  sync are off only because the database is disposable scratch.
- DuckDB uses one query thread, a 128 MiB buffer limit, controlled spill directory,
  disabled extension autoload/install and external access. Streaming uses one
  lazy, single-pass Arrow RecordBatchReader and a fixed grouped exact-distinct
  query; table mode uses Arrow INSERT batches in one transaction.
- SQLite has a 128 MiB page cache. These are different subsystem limits, not
  equivalent hard RSS caps. DuckDB's memory_limit does not cap the whole process.
  See [DuckDB limits](https://duckdb.org/docs/current/operations_manual/limits).
- Primary time is parent wall time including Python startup, library imports,
  hashing, conversion, ingestion/query, connection close, worker exit and scratch
  cleanup. `communicate(timeout=0.1)` wakes on exit, avoiding 100 ms rounding.
- Memory is each fresh worker's `ru_maxrss` (bytes on macOS), including native
  allocations and bounded input batches. No worker launches child processes.
  It excludes the benchmark controller and OS filesystem cache.
- Scratch is the sampled sum of logical file sizes in the worker directory,
  every 100 ms; it includes database/WAL/spill. Short-lived/unlinked files may
  escape sampling. It is not an exact allocated-disk high-water measurement.
- Per-run deadline 600 s, sampled scratch ceiling 4 GiB; no run hit either.
  Tests cover controller-enforced child timeout kill/reap and scratch cleanup,
  not abrupt termination of the controller itself or machine failure.
- The 750k × 25 case is 18.75 million cells, above the product's normal 10 million
  input-cell budget. This component benchmark does not raise that budget or claim
  the public profiling flow now supports this size.

## Results

Each cell is **median [minimum–maximum]** over three runs. RSS is the median of
per-run peaks, not a maximum taken across repeats. MiB = 1,048,576 bytes.

| Rows | Cardinality | Engine | Total seconds | Peak RSS, MiB | Sampled scratch peak, MiB |
| ---: | --- | --- | ---: | ---: | ---: |
| 10,000 | unique | python | 0.16 [0.16–0.16] | 60.2 [60.2–63.4] | 0.0 [0.0–0.0] |
| 10,000 | unique | duckdb-stream | 0.24 [0.24–0.24] | 109.1 [109.1–109.8] | 0.0 [0.0–0.0] |
| 10,000 | unique | sqlite | 0.36 [0.36–0.36] | 45.9 [45.7–46.0] | 10.4 [10.4–10.4] |
| 10,000 | low | python | 0.15 [0.15–0.15] | 35.9 [35.7–36.0] | 0.0 [0.0–0.0] |
| 10,000 | low | duckdb-stream | 0.23 [0.23–0.23] | 92.7 [92.2–92.7] | 0.0 [0.0–0.0] |
| 10,000 | low | sqlite | 0.25 [0.25–0.26] | 36.0 [35.9–36.1] | 0.1 [0.1–0.1] |
| 100,000 | unique | python | 1.39 [1.37–1.42] | 376.8 [345.0–377.3] | 0.0 [0.0–0.0] |
| 100,000 | unique | duckdb-stream | 1.56 [1.56–1.58] | 300.1 [291.4–309.1] | 83.7 [81.7–84.5] |
| 100,000 | unique | sqlite | 3.89 [3.89–3.94] | 167.3 [165.6–167.8] | 104.0 [104.0–104.0] |
| 100,000 | low | python | 1.23 [1.21–1.24] | 40.8 [39.8–42.8] | 0.0 [0.0–0.0] |
| 100,000 | low | duckdb-stream | 1.30 [1.29–1.31] | 97.0 [97.0–98.9] | 0.0 [0.0–0.0] |
| 100,000 | low | sqlite | 2.27 [2.27–2.28] | 44.4 [41.3–44.8] | 0.1 [0.1–0.1] |
| 750,000 | unique | python | 10.88 [10.87–11.03] | 2982.2 [2980.5–3023.5] | 0.0 [0.0–0.0] |
| 750,000 | unique | duckdb-stream | 11.82 [11.48–11.92] | 383.7 [378.6–423.3] | 1334.8 [1331.2–1338.0] |
| 750,000 | unique | sqlite | 65.31 [64.99–68.53] | 194.0 [193.5–194.0] | 780.7 [780.7–780.7] |
| 750,000 | low | python | 8.87 [8.80–9.10] | 46.8 [46.7–46.8] | 0.0 [0.0–0.0] |
| 750,000 | low | duckdb-stream | 9.31 [9.18–9.34] | 105.3 [105.0–105.8] | 0.0 [0.0–0.0] |
| 750,000 | low | sqlite | 16.51 [16.41–16.86] | 47.2 [47.1–47.2] | 0.1 [0.1–0.1] |

### Rejected table-staging candidate

| Rows | Cardinality | Total seconds | Peak RSS, MiB | Sampled scratch peak, MiB |
| ---: | --- | ---: | ---: | ---: |
| 10,000 | unique | 0.32 [0.31–0.32] | 142.3 [137.9–144.7] | 8.8 [8.8–8.8] |
| 10,000 | low | 0.25 [0.25–0.25] | 110.8 [109.6–113.2] | 1.3 [1.3–1.3] |
| 100,000 | unique | 2.29 [2.26–2.29] | 453.9 [394.1–474.4] | 127.8 [126.6–128.2] |
| 100,000 | low | 1.49 [1.49–1.52] | 243.2 [229.5–249.5] | 9.0 [9.0–9.0] |
| 750,000 | unique | 17.19 [17.12–17.22] | 1124.1 [1111.5–1154.1] | 1769.2 [1766.1–1773.9] |
| 750,000 | low | 9.98 [9.95–10.38] | 982.0 [946.7–1006.6] | 64.0 [64.0–64.0] |

## Reproduction and evidence

The project environment already had PyArrow 25.0.0 (Parquet extra). DuckDB was
installed only in an isolated temporary target; pyproject.toml and uv.lock were
not edited. Use the recorded Python/library versions to compare these numbers.

```sh
uv --cache-dir /private/tmp/apa-benchmark-uv-cache pip install \
  --python .venv/bin/python --target /private/tmp/apa-distinct-benchmark-deps \
  'duckdb==2.0.1'
PYTHONPATH=/private/tmp/apa-distinct-benchmark-deps .venv/bin/python \
  scripts/benchmark_distinct_tracking.py --duckdb-ingestion table \
  --output /private/tmp/distinct-table-results.json
PYTHONPATH=/private/tmp/apa-distinct-benchmark-deps .venv/bin/python \
  scripts/benchmark_distinct_tracking.py --engines duckdb --duckdb-ingestion stream \
  --output /private/tmp/distinct-stream-results.json
```

- [Original raw 54 runs](distinct-benchmark-results.json)
- [Streaming raw 18 runs](distinct-benchmark-stream-results.json)
- [Reproducible script](../../../scripts/benchmark_distinct_tracking.py)
- [Focused checks](../../../tests/test_distinct_benchmark.py)

Raw JSON includes actual versions, counts, settings, per-stage and CPU times,
per-run RSS, wall time and sampled scratch peaks. SHA-256 records identify the
script versions used; the final script additionally supports streaming, while
retaining the original table/Python/SQLite paths. Stream `query_call_seconds`
includes producer work; `input_seconds` and `ingest_seconds` measure hashing and
Arrow conversion before each yield, and `query_seconds` subtracts those costs.
Exclusive stage timing is approximate; total wall is the decision metric.

Validation: 14 focused checks passed with DuckDB available; Ruff passed. Tests
cover deterministic/bounded digest batches, duplicates across batch boundaries,
all engines and both DuckDB modes, lazy single-pass Arrow consumption, isolated
process metrics and timeout cleanup. No live database or source data was used.

Not checked: full CSV-profile equivalence, whole-application speedup, parallel
DuckDB scaling, a hard RSS cap, production spill security, other hardware/library
versions, release gates or cleanup if the controller itself is killed. This experiment does
not complete the broader generation-performance OpenSpec acceptance matrix.
