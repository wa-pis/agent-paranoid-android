# Current public CSV benchmark — 2026-11-25

Measured implementation: **`0529fb43ce1dbe85bb948623f83a66ac58500fdd`**.
Full run data, stage counters, source fingerprints and provenance:
[public-csv-current-results.json](public-csv-current-results.json).
[CI qualification](ci-followup.md) and [human review guide](review-guide.md)
cover the same implementation. Historical reports remain unchanged.

## Results

Four repeats per case, 25 fields, seed 42. API times are medians; memory columns
are the largest observed value across the four repeats. MiB means 2**20 bytes.

| Rows | Public CSV path | API seconds | Time range, seconds | Sampled process-tree RSS, MiB | Coordinator peak RSS, MiB |
| ---: | --- | ---: | --- | ---: | ---: |
| 100,000 | Ordinary | 5.736 | 5.723–5.743 | 291.2 | 296.1 |
| 100,000 | Streaming, 4 workers | 2.845 | 2.808–2.885 | 465.6 | 110.4 |
| 750,000 | Ordinary | 42.826 | 42.692–42.890 | 1,907.0 | 1,907.0 |
| 750,000 | Streaming, 4 workers | 18.552 | 18.530–18.642 | 549.3 | 188.6 |

On this fixture, streaming takes about half the ordinary API time at 100,000
rows, with a higher whole-process-tree memory peak. At 750,000 rows it is about
**2.31 times faster**, with roughly **71% lower sampled tree RSS**. All four
adjacent comparisons show the same direction. Per-pair ratios and ordering are
retained in the JSON.

Keep streaming an explicit option for supported flat datasets. These results
support its large-volume use; small datasets may pay more memory for the worker
pool. They do not establish a universal row threshold or performance against
the release or the archived pre-port implementation.

## Exclusive coordinator stages

Seconds below are medians of each stage group. Independent medians need not sum
to the median total; each individual run's exclusive stages sum to its API time.

| Rows | Path | Generation / IPC wait | Validation and normalization | CSV encoding and I/O | Artifacts and publication | Setup |
| ---: | --- | ---: | ---: | ---: | ---: | ---: |
| 100,000 | Ordinary | 3.457 | 1.678 | 0.564 | 0.020 | 0.014 |
| 100,000 | Streaming | 0.438 | 1.808 | 0.570 | 0.019 | 0.010 |
| 750,000 | Ordinary | 25.872 | 12.555 | 4.183 | 0.086 | 0.107 |
| 750,000 | Streaming | 0.533 | 13.704 | 4.214 | 0.089 | 0.010 |

Streaming workers generate concurrently with coordinator validation and writing.
Its generation/IPC column measures exclusive coordinator waiting and bookkeeping,
not total worker generation time or CPU consumption. It cannot establish a
generation-only speedup. Ordinary CSV instrumentation includes write, flush and
fsync inside its encoding scope; combining `csv_encoding` and `csv_write` gives
a comparable CSV stage. No claim about isolated encoding speed follows.

## Method and checks

- Existing `scripts/benchmark_public_csv.py`, unchanged. For each size the mode
  order is ordinary/streaming, streaming/ordinary, repeated twice. The separate
  before/after CSV-guard runner is not used in this comparison.
- macOS 26.6.2 arm64, Python 3.11.15, 14 logical CPUs. Existing locked environment:
  package 1.7.1, Faker 40.35.0, Pydantic 2.14.3, PyYAML 6.0.3. No dependency upgrade.
- Source-free fictional fixture: one entity, a primary key and 24 fields cycling
  through integer, float, boolean, date, categorical and string-pattern cases.
  Relationships, business rules, DECIMAL and datetime are outside this fixture.
- Ordinary uses its released random stream; streaming uses `tiled-v1` with four
  workers and 4,096-row tiles. Seed 42 is shared. Byte identity is required across
  repeats within each path; different engine streams do not promise identical
  CSV bytes to each other.
- Every run retains mandatory checks and all four validation-report sections.
  Counters confirm normalization and schema/privacy/constraint/relationship
  validation cover every row once per dataset or tile. Final reports are valid.
- External audits verify all CSV rows, header, ordered unique keys, manifest
  flags, hashes of every output, exact file inventory, private permissions and
  absence of partial staging. These audits run outside the API timer and measured
  child process. Every generated bundle and its owned scratch directory was
  removed. No generated rows are committed.
- **16/16 runs passed**. All four cases reproduced exactly across four repeats.
  **127 focused tests passed**, including instrumentation, negative audit cases,
  privacy gates, deterministic export, atomic publication and failure cleanup.
- RSS is sampled over the worker and descendants using `ps` every 100 ms plus
  sampling overhead. Shared pages may be counted repeatedly and brief peaks may
  be missed. Coordinator RSS additionally uses the OS high-water counter;
  neither column is an OS-enforced memory cap.
- Each worker retains a 600-second generation budget, 750,000-row admission and
  4 GiB output allowance. These are benchmark invocation settings; application
  defaults are unchanged. Measurements ran serially, with no concurrent test
  suite or other benchmark campaign started by this task.

## Reproduction and provenance

From the checkout root, using the existing locked environment:

```sh
env PYTHONPATH="$PWD/src:$PWD/scripts" \
  PYTHONHASHSEED=0 PYTHONDONTWRITEBYTECODE=1 \
  .venv/bin/python scripts/benchmark_public_csv.py \
  --rows 100000 750000 --repeats 4 \
  --output /private/tmp/current-public-csv-results.json
```

The launcher checked all 176 source/helper fingerprints against the exact Git
commit before and after the campaign and verified the checkout's import origins.
The published JSON retains every measurement. Its source-hash map is represented
losslessly as path/digest records; the canonical-map digest algorithm and original
raw-report digest are recorded. Three machine-specific path fields are normalized
explicitly. This report adds metadata only and changes no runtime behavior.
An independent automated recheck reconstructed the source map, matched every
measurement to the private raw report and recomputed the grouped stages and
paired ratios without discrepancies.

Human review remains pending. This synthetic campaign does not certify detector
recall on real data, authorize a dataset or activate transformation extensions.
