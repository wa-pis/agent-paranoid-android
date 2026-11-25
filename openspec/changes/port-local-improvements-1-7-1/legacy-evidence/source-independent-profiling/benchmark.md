# Public CSV After The Profiling And Privacy Changes

Measured locally on 2026-11-22 after the current source-independent profiling,
whole-column semantics and privacy-signal changes. Raw metadata and all twelve
runs are in [public-csv-results.json](public-csv-results.json). No runtime code,
benchmark instrumentation or dependencies changed for this experiment.

## Method

Use the existing public `generate_dataset_bundle` benchmark with the same
fictional specification, seed 42 and 25 fields: 100,000 and 750,000 rows.
Ordinary export is serial; streaming uses four workers and fixed 4,096-row
tiles. Each size/path runs three times in fresh subprocesses, one at a time,
alternating path order. No tests or other heavy verification run concurrently.
All mandatory checks and all four validation-report sections remain enabled.

The environment equals the preceding detector-performance series: Python
3.11.2, macOS 26.6.2 arm64, 14 logical CPUs, Faker 40.35.0, Pydantic 2.13.4,
PyYAML 6.0.3 and installed package metadata 1.5.0. The measured implementation
is the working tree, identified by 126 file hashes in the raw result. Per-run
limits remain 750,000 rows, 4 GiB output and 600 seconds; streaming also limits
cells to 18,750,000. The external worker deadline is 660 seconds.

API time includes generation, validation, CSV encoding/writing, control
artifacts, hashing and atomic directory publication. Imports, subprocess
startup and the independent parent audit are excluded. Instrumentation delegates
every original implementation and every budget check. Stages are exclusive
coordinator wall times; workers generate concurrently while the coordinator
validates, so streaming generation/IPC is not total worker computation.
Per-stage medians need not sum to the median total.

Memory is sampled across the concurrent coordinator and descendant process tree
at nominal 100 ms plus sampling overhead, including child startup/export but
excluding the later parent audit. Tree RSS can count shared pages repeatedly
and miss brief peaks; it is not exact physical memory. Coordinator `ru_maxrss`
is recorded separately. Tables show maxima over the three repetitions for each
memory metric independently, not sums of per-process high-water marks.

## Public API Time

All twelve measured attempts succeeded. Ranges are minima/maxima, not confidence
intervals. The comparison is with the immediately preceding
[detector-performance series](../privacy-detector-performance/benchmark.md),
not interleaved old/new checkouts. Small differences cannot establish an effect
of the intervening changes.

| Rows | Path | Previous median, s | Current median, s | Current range, s | Time change |
| --- | --- | ---: | ---: | --- | ---: |
| 100,000 | Ordinary | 6.884041 | 6.728698 | 6.677161–6.735903 | −2.26% |
| 100,000 | Streaming, 4 workers | 3.334131 | 3.327725 | 3.306813–3.331274 | −0.19% |
| 750,000 | Ordinary | 50.967243 | 50.786452 | 50.463792–50.853018 | −0.35% |
| 750,000 | Streaming, 4 workers | 21.756261 | 22.164009 | 22.079184–22.230453 | +1.87% |

Streaming is 2.02× faster at 100k and 2.29× faster at 750k in this series.
At 750k its sampled peak tree RSS is 60.05% lower; at 100k it uses more tree
memory because of process overhead. Streaming remains useful as an explicit
option for large exports.

## Exclusive Stage Medians

Seconds. Relationship and constraint validators execute, although the fictional
specification has no relationships or business constraints. An absent stage is
shown as `—`. Control-file atomic writes are included in the write stage.

| Stage | 100k ordinary | 100k streaming | 750k ordinary | 750k streaming |
| --- | ---: | ---: | ---: | ---: |
| Setup and bookkeeping | 0.014197 | 0.009812 | 0.106213 | 0.022947 |
| Generation / IPC | 4.041112 | 0.496142 | 30.322977 | 0.609402 |
| Combined runner residual | 0.000277 | 0.005988 | 0.000291 | 0.043698 |
| Privacy validation | 1.129470 | 1.217312 | 8.639266 | 9.296104 |
| Schema validation | 0.788141 | 0.822878 | 5.955096 | 6.294248 |
| Relationship validation | 0.000003 | 0.000032 | 0.000003 | 0.000237 |
| Constraint validation | 0.000001 | 0.000017 | 0.000001 | 0.000126 |
| Normalization | 0.247210 | 0.259397 | 1.843518 | 2.010824 |
| Streaming global checks | — | 0.013884 | — | 0.108938 |
| CSV encoding | 0.469989 | 0.454432 | 3.586307 | 3.472388 |
| CSV / control-file writes | 0.004862 | 0.021718 | 0.023750 | 0.164300 |
| Artifacts and hashing | 0.027632 | 0.018540 | 0.171046 | 0.089062 |
| Atomic publication | 0.000121 | 0.000140 | 0.000140 | 0.000157 |

Median total validation, calculated from each run's sum of the combined-runner
residual, privacy, schema, relationship, constraint and normalization stages,
is 2.172150 / 2.305458 / 16.450462 / 17.701719 seconds respectively. Streaming
global checks are separate. Ordinary generation and streaming validation remain
the largest exposed stages.

## Peak Memory

MiB, maxima over three repetitions. Do not add the two memory columns.

| Rows | Path | Sampled tree RSS | Coordinator high-water RSS |
| --- | --- | ---: | ---: |
| 100,000 | Ordinary | 290.30 | 295.97 |
| 100,000 | Streaming | 549.39 | 138.80 |
| 750,000 | Ordinary | 1,912.06 | 1,915.28 |
| 750,000 | Streaming | 763.91 | 231.36 |

## Privacy, Determinism And File Safety

Every measured run retains the real privacy, schema, relationship and constraint
validators and normalization. Each processes exactly the requested row count:
one ordinary entity, or 25 tiles at 100k / 184 tiles at 750k. The combined runner
executes once per entity/tile; duplicate mandatory/report validation entry
points remain unused. All four report sections pass. Instrumented exclusive
stage times sum to the measured API time for every run.

The independent parent audit streams each completed CSV to verify its exact
header, 25 fields, row count and ordered unique synthetic keys. It verifies the
report, synthetic/no-source-reuse flags, manifest row counts and actual engine,
the exact artifact set and every artifact SHA-256. Output directories are 0700
and files 0600; there is no partial staging, and every scratch directory is
removed. Owned process groups are stopped before audit/cleanup. Only metadata
and hashes are retained. This audit does not independently classify every CSV
cell again; the real runtime privacy validator covers every generated row.

All three repetitions within each size/path are byte-identical. Every CSV
also matches every corresponding repetition of the preceding detector series
and the harness's earlier privacy-validation baseline. Ordinary and streaming
CSV files differ because their established seed namespaces differ; deterministic
within-path output is preserved.

| Rows | Path | CSV bytes | SHA-256 |
| --- | --- | ---: | --- |
| 100,000 | Ordinary | 28,177,934 | `24e6f6833a83cebc9b17e52bc7b7c07449527741348be3221e64553d1b3ab462` |
| 100,000 | Streaming | 28,175,783 | `76330b20f138af1c8b49d42fe8780057cd0b735895a98b0d98713cf715ab9979` |
| 750,000 | Ordinary | 211,322,612 | `5b3a754438204d3fb5dce71e814a8cbac6c4cd749b0db5b55576394dce1923dc` |
| 750,000 | Streaming | 211,321,616 | `735b3374822b27e5afccaa73ebde1773ae43b7e93a1f9f06c43c8535f22a4405` |

Before timing, the focused harness, frozen detector/privacy equivalence, semantic
accuracy/signal-strength and public streaming-export suites passed: **175 tests
in 3.87 seconds**. The earlier full-suite result remains **2704 passed, 10
skipped**, documented in [validation.md](validation.md); it was not rerun for
this measurement-only task. Existing cross-source safety evidence is also
there. The benchmark consumes a fictional specification, so it does not time
source adapters or establish real-world detector accuracy. No source rows,
production data, live databases or external AI providers were used.

Independent read-only review recomputed every summary, stage sum, validator
count, row-coverage check and baseline/repeat comparison, and verified all 126
source hashes against the final working tree. Environment and settings exactly
match the latest detector series. `git diff --check` and
`openspec validate source-independent-profiling --strict` passed. Historical
benchmark files and the benchmark driver remain unchanged.

## Evidence And Reproduction

| Artifact | SHA-256 |
| --- | --- |
| Current `public-csv-results.json` | `e2a84aed6a266c85d59295f8f19eb2d4d3882712391f9f896f59bbb4add84330` |
| Previous `../privacy-detector-performance/public-csv-results.json` | `31d9d79ab3f9ff0fd1cdee5f2195e259f13ab38155cc301d790be5bdcfd047c2` |

The unchanged driver records `privacy-validation-performance` as its built-in
byte/hash baseline; the time comparison above explicitly uses the newer
`privacy-detector-performance` result. Both historical references stay intact.

```bash
.venv/bin/python scripts/benchmark_public_csv.py \
  --rows 100000 750000 --repeats 3 \
  --output /private/tmp/post-changes-public-csv.json
```

Use a new destination to preserve recorded evidence. Local `ps` access is
required for tree RSS sampling; the restricted-sandbox preflight stopped before
any measured attempt, then the same command ran with process-list access.
