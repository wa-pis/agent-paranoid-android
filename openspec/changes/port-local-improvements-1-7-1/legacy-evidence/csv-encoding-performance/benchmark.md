# Public CSV After The Shared Encoding Guard

The later [paired comparison](paired-benchmark.md) measures both versions in
alternating order and supports retaining the guard. This document preserves the
original historical comparison below, including its higher total API times.

Measured 2026-11-23: twelve successful runs, three repeats per case. Raw metadata
is in [public-csv-results.json](public-csv-results.json); exact-equivalence and
regression evidence is in [validation.md](validation.md). Only the two-line
guard in `io/writers.py` differs among the 126 measured source/benchmark files
from [the latest baseline](../value-normalization-performance/benchmark.md).

## Method

The unchanged driver uses public `generate_dataset_bundle`, a fictional
25-field specification and seed 42. Ordinary generation is serial; streaming
uses four workers and fixed 4,096-row tiles. Three fresh subprocesses per
size/path run serially, alternating path order. No tests or other heavy
verification run concurrently. Every instrumented function and budget check
delegates its original implementation. All mandatory checks and all four report
sections remain enabled. No encoding loop, schema check or atomic writer changed.

Environment/settings equal the preceding series: Python 3.11.2, macOS 26.6.2
arm64, 14 logical CPUs, Faker 40.35.0, Pydantic 2.13.4, PyYAML 6.0.3 and
installed package metadata 1.5.0. Limits remain 750,000 rows, 4 GiB output,
600 seconds per worker and 18,750,000 streaming cells; external deadline is
660 seconds. All 126 measured source hashes bind the working-tree candidate.

API time includes generation, validation, CSV, control artifacts, hashing and
atomic directory publication; imports, subprocess startup and the independent
parent audit are excluded. Stages are exclusive coordinator wall time.
Streaming workers generate concurrently, so generation/IPC is exposed waiting
and coordinator work rather than total worker computation. Per-stage medians
need not sum to the median total. Ordinary CSV encoding includes UTF-8 conversion
in bounded-text output; streaming includes per-tile UTF-8 conversion.

Before/after series are historical, not paired/interleaved checkouts. Ranges
below are observed minimum/maximum values, not confidence intervals. No repeat
was discarded or replaced. Source-adapter performance is outside this benchmark.

## Encoding And Total API Time

Medians of three repeats; a positive API change means more total time.

| Rows | Path | API before → after, s | Current API range, s | API time change | Encoding before → after, s | Less encoding time |
| --- | --- | --- | --- | ---: | --- | ---: |
| 100,000 | Ordinary | 6.194980 → 6.394662 | 6.303047–6.434024 | +3.22% | 0.476383 → 0.467307 | 1.91% |
| 100,000 | Streaming, 4 workers | 2.755992 → 2.808688 | 2.795402–2.832130 | +1.91% | 0.466410 → 0.460291 | 1.31% |
| 750,000 | Ordinary | 46.863511 → 47.716514 | 47.134065–49.790613 | +1.82% | 3.611503 → 3.470351 | 3.91% |
| 750,000 | Streaming, 4 workers | 17.618044 → 17.824950 | 17.436894–18.567097 | +1.17% | 3.563569 → 3.487190 | 2.14% |

CSV encoding uses 1.31–3.91% less time, but total API medians are 1.17–3.22%
higher. This series does **not** establish an end-to-end export speedup. Other
stages also took longer: ordinary generation at 100k changed from 4.089478 to
4.243331 seconds and at 750k from 30.782962 to 31.504241 seconds. The only code
change is in the encoder; the historical comparison does not establish the cause
of changes outside that stage. The separate eleven-pass interleaved diagnostic
measured 4.09–5.47% less isolated encoding time; it is not a public API result.

## Exclusive Stage Medians

Seconds. Relationship/constraint validators still execute; this fictional
specification has no relationships or business constraints. `—` means absent.
Control-file atomic writes remain in the write stage.

| Stage | 100k ordinary | 100k streaming | 750k ordinary | 750k streaming |
| --- | ---: | ---: | ---: | ---: |
| Setup and bookkeeping | 0.015401 | 0.010740 | 0.116468 | 0.026636 |
| Generation / IPC | 4.243331 | 0.545135 | 31.504241 | 0.687435 |
| Combined runner residual | 0.000300 | 0.006393 | 0.000288 | 0.045823 |
| Privacy validation | 1.175094 | 1.220716 | 8.957009 | 9.360502 |
| Schema validation | 0.330703 | 0.363217 | 2.486044 | 2.851403 |
| Relationship validation | 0.000004 | 0.000039 | 0.000003 | 0.000275 |
| Constraint validation | 0.000001 | 0.000018 | 0.000001 | 0.000118 |
| Normalization | 0.125880 | 0.137266 | 0.937413 | 1.073319 |
| Streaming global checks | — | 0.015217 | — | 0.121310 |
| CSV encoding | 0.467307 | 0.460291 | 3.470351 | 3.487190 |
| CSV / control-file writes | 0.007068 | 0.023610 | 0.026679 | 0.095294 |
| Artifacts and hashing | 0.022537 | 0.020570 | 0.156978 | 0.094259 |
| Atomic publication | 0.000154 | 0.000150 | 0.000146 | 0.000137 |

Median total validation, from each run's sum of combined-runner residual,
privacy, schema, relationship, constraint and normalization stages:
1.633715 / 1.726012 / 12.380759 / 13.331439 seconds respectively. Streaming global
checks remain separate.

## Peak Memory

MiB, maxima over three repeats for each metric independently. Tree RSS is a
concurrent coordinator-plus-descendant sum sampled at nominal 100 ms plus
sampling overhead, including startup/export and excluding the later parent
audit. Brief peaks may be missed and shared pages counted repeatedly. Coordinator
`ru_maxrss` is its own high-water mark. Do not add the columns or sum individual
process high-water marks. This does not measure exact physical memory or impose
a hard RSS cap.

| Rows | Path | Tree RSS before → after | Coordinator RSS before → after |
| --- | --- | --- | --- |
| 100,000 | Ordinary | 268.86 → 291.81 | 295.80 → 297.97 |
| 100,000 | Streaming, 4 workers | 547.81 → 539.27 | 132.19 → 133.06 |
| 750,000 | Ordinary | 1914.41 → 1917.08 | 1917.66 → 1923.80 |
| 750,000 | Streaming, 4 workers | 757.80 → 753.16 | 224.31 → 219.97 |

The guard retains no cache, row collection or additional output buffer. Memory
changes are mixed; this experiment does not establish a memory improvement.
The ordinary 100k sampled peak rises more than its coordinator high-water mark,
illustrating the sampling distinction.

## Preserved Checks, Bytes And Atomic Publication

All real validators and normalization cover every requested row: one complete
ordinary entity, or 25 streaming tiles at 100k / 184 at 750k. Combined validation
runs once per entity/tile; duplicate mandatory/report entry points remain unused.
All four report sections pass. Exclusive stage sums equal API time in every run.
Raw privacy stays before encoding and every tile is checked before writing.

After each measured child exits, the independent parent streams the CSV to
verify header, 25 fields, count and ordered unique synthetic keys. It verifies
report validity, synthetic/no-source-reuse flags, manifest counts and engine,
exact artifact set and every artifact SHA-256. Output directories are 0700 and
files 0600; owned process groups are stopped, no staging remains and every
scratch directory is removed. The parent does not classify every CSV cell again;
real runtime privacy checks and unchanged regression suites provide that evidence.

All repetitions within each size/path are byte-identical and equal every matching
repetition of the latest value-normalization baseline and the driver's older
privacy-validation reference. Ordinary/tiled outputs differ because of their
existing seed namespaces; each path preserves its exact previous output.

| Rows | Path | CSV bytes | SHA-256 |
| --- | --- | ---: | --- |
| 100,000 | Ordinary | 28,177,934 | `24e6f6833a83cebc9b17e52bc7b7c07449527741348be3221e64553d1b3ab462` |
| 100,000 | Streaming, 4 workers | 28,175,783 | `76330b20f138af1c8b49d42fe8780057cd0b735895a98b0d98713cf715ab9979` |
| 750,000 | Ordinary | 211,322,612 | `5b3a754438204d3fb5dce71e814a8cbac6c4cd749b0db5b55576394dce1923dc` |
| 750,000 | Streaming, 4 workers | 211,321,616 | `735b3374822b27e5afccaa73ebde1773ae43b7e93a1f9f06c43c8535f22a4405` |

Independent read-only review recomputes summaries/stages, counts/row coverage,
audit flags, repeat/baseline equality and all 126 source hashes against the final
working tree. No production data, source rows, live databases or external AI
providers were used. Only metadata/hashes remain; the fixture does not estimate
real-world privacy accuracy or source-adapter performance.

## Evidence And Reproduction

| Artifact | SHA-256 |
| --- | --- |
| Current `public-csv-results.json` | `3bcb174e80561d2fa26b06f52786a62a6b04656f95017b36caff80ecf280d937` |
| Latest baseline `../value-normalization-performance/public-csv-results.json` | `65e588a7784c6591e7e7d30517ef4ba3c3f93cdd081cc7701d79d6ee7520eb24` |

The unchanged driver still names `privacy-validation-performance` as its built-in
byte/hash reference. These tables explicitly compare with the latest
`value-normalization-performance` series. All historical artifacts remain intact.

```bash
.venv/bin/python scripts/benchmark_public_csv.py \
  --rows 100000 750000 --repeats 3 \
  --output /private/tmp/csv-encoding-public-csv.json
```

Use a new destination to preserve evidence. Local process-list access is required
for `ps` RSS sampling.
