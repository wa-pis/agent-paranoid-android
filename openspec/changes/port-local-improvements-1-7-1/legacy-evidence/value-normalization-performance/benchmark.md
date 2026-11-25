# Public CSV After Value-Normalization Preparation

Measured 2026-11-23, three repeats per case, twelve successful attempts.
[Raw runs](public-csv-results.json) and [verification](validation.md) retain
counts, hashes and regression evidence. The only measured runtime change from
[the preceding series](../schema-validation-performance/benchmark.md) is
`validation/values.py`; the benchmark, fixture and other validators are unchanged.

## Method

Use the same public `generate_dataset_bundle` API, fictional specification,
25 fields and seed 42. Ordinary generation is serial; streaming uses four
workers and fixed 4,096-row tiles. Three fresh subprocesses per size/path run
one at a time, alternating path order, without concurrent tests or other heavy
verification. Instrumentation delegates every original function and budget
check. All mandatory checks and all four report sections remain enabled.

Environment and settings exactly match the latest schema-validation baseline:
Python 3.11.2, macOS 26.6.2 arm64, 14 logical CPUs, Faker 40.35.0, Pydantic
2.13.4, PyYAML 6.0.3 and installed package metadata 1.5.0. The working tree is
bound by 126 source-file hashes. Per-worker limits remain 750,000 rows, 4 GiB
output and 600 seconds; streaming also limits cells to 18,750,000. The external
deadline is 660 seconds. Source adapters are not part of this generation benchmark.

API time includes generation, validation, CSV encoding/writing, control artifacts,
hashing and atomic directory publication. Imports, subprocess startup and the
independent parent audit are excluded. Stages are exclusive coordinator wall
time; workers generate concurrently with coordinator validation, so streaming
generation/IPC is not total worker computation. Per-stage medians need not sum
to the median total. Historical before/after series are not paired or interleaved;
background variation limits attribution of small total-time differences.

## Public API And Normalization Time

Medians of three repeats; ranges are minimum/maximum observations, not confidence
intervals. Before values come from the latest schema-validation series.

| Rows | Path | API before → after, s | Current API range, s | Less API time | Normalization before → after, s | Less normalization time |
| --- | --- | --- | --- | ---: | --- | ---: |
| 100,000 | Ordinary | 6.323556 → 6.194980 | 6.185705–6.271778 | 2.03% | 0.248572 → 0.122661 | 50.65% |
| 100,000 | Streaming, 4 workers | 2.880147 → 2.755992 | 2.737521–2.870898 | 4.31% | 0.265991 → 0.135387 | 49.10% |
| 750,000 | Ordinary | 47.581540 → 46.863511 | 45.959096–47.118909 | 1.51% | 1.824381 → 0.924167 | 49.34% |
| 750,000 | Streaming, 4 workers | 18.447407 → 17.618044 | 17.456948–17.663509 | 4.50% | 2.072514 → 1.032116 | 50.20% |

Normalization uses 49.10–50.65% less time. Ordinary API time is 1.51–2.03%
lower and streaming API time 4.31–4.50% lower. Its contribution to the full
export is smaller than generation or privacy validation, so halving normalization
does not halve the whole export. Separate bounded native/CSV-string timings
are recorded in the verification document.

## Exclusive Stage Medians

Seconds. Relationship and constraint validators execute, although this fictional
specification has no relationships or business constraints. `—` means absent.
Control-file atomic writes remain in the write stage.

| Stage | 100k ordinary | 100k streaming | 750k ordinary | 750k streaming |
| --- | ---: | ---: | ---: | ---: |
| Setup and bookkeeping | 0.014558 | 0.010069 | 0.109212 | 0.028741 |
| Generation / IPC | 4.089478 | 0.502010 | 30.782962 | 0.643637 |
| Combined runner residual | 0.000287 | 0.006232 | 0.000293 | 0.043561 |
| Privacy validation | 1.149898 | 1.198276 | 8.718921 | 9.134031 |
| Schema validation | 0.320266 | 0.373891 | 2.431341 | 2.766836 |
| Relationship validation | 0.000003 | 0.000034 | 0.000004 | 0.000245 |
| Constraint validation | 0.000001 | 0.000019 | 0.000001 | 0.000125 |
| Normalization | 0.122661 | 0.135387 | 0.924167 | 1.032116 |
| Streaming global checks | — | 0.013763 | — | 0.110461 |
| CSV encoding | 0.476383 | 0.466410 | 3.611503 | 3.563569 |
| CSV / control-file writes | 0.007790 | 0.016764 | 0.026844 | 0.122233 |
| Artifacts and hashing | 0.018245 | 0.019333 | 0.169001 | 0.091087 |
| Atomic publication | 0.000122 | 0.000124 | 0.000150 | 0.000142 |

Median total validation, computed from each run's sum of combined-runner
residual, privacy, schema, relationship, constraint and normalization stages:
1.591389 / 1.715946 / 12.074744 / 12.963277 seconds respectively. Streaming global
checks are separate.

## Peak Memory

MiB, maxima over three repeats for each metric independently. Tree RSS is a
concurrent coordinator-plus-descendant sum sampled at nominal 100 ms plus
sampling overhead, including startup/export and excluding the later parent
audit. Brief peaks may be missed and shared pages counted repeatedly. Coordinator
`ru_maxrss` is its own high-water mark; do not add these columns or sum per-process
high-water marks. These are not exact physical-memory or hard RSS-cap measurements.

| Rows | Path | Tree RSS before → after | Coordinator RSS before → after |
| --- | --- | --- | --- |
| 100,000 | Ordinary | 269.36 → 268.86 | 296.44 → 295.80 |
| 100,000 | Streaming, 4 workers | 545.73 → 547.81 | 139.02 → 132.19 |
| 750,000 | Ordinary | 1920.02 → 1914.41 | 1922.08 → 1917.66 |
| 750,000 | Streaming, 4 workers | 770.06 → 757.80 | 230.08 → 224.31 |

Only field-count-sized metadata is retained within one normalization call;
no value cache or extra row copy is introduced. Memory changes are small and
mixed; this experiment does not establish a general memory reduction.

## Privacy, Determinism And File Safety

All real validators and normalization cover every requested row: one complete
ordinary entity, or 25 streaming tiles at 100k / 184 at 750k. Combined validation
runs once per entity/tile, duplicate mandatory/report entry points remain unused,
and all four report sections pass. Per-run exclusive stages sum exactly to API
time. Strict raw-value privacy remains before combined normalization.

After each measured child exits, the independent parent streams its CSV to check
header, 25 fields, exact count and ordered unique synthetic keys. It verifies
report validity, synthetic/no-source-reuse flags, manifest counts and engine,
exact artifact set and all artifact hashes. Directories are 0700, files 0600;
owned process groups are stopped, no staging remains and every scratch directory
is removed. Only metadata/hashes are retained. The parent audit does not repeat
per-cell privacy classification; the actual runtime validator covers every row.

Every repetition within a size/path is byte-identical and equals every matching
repetition of the latest schema-validation baseline, plus the driver's older
privacy-validation reference. Ordinary and tiled outputs differ because their
established seed namespaces differ; each path retains its exact previous output.

| Rows | Path | CSV bytes | SHA-256 |
| --- | --- | ---: | --- |
| 100,000 | Ordinary | 28,177,934 | `24e6f6833a83cebc9b17e52bc7b7c07449527741348be3221e64553d1b3ab462` |
| 100,000 | Streaming, 4 workers | 28,175,783 | `76330b20f138af1c8b49d42fe8780057cd0b735895a98b0d98713cf715ab9979` |
| 750,000 | Ordinary | 211,322,612 | `5b3a754438204d3fb5dce71e814a8cbac6c4cd749b0db5b55576394dce1923dc` |
| 750,000 | Streaming, 4 workers | 211,321,616 | `735b3374822b27e5afccaa73ebde1773ae43b7e93a1f9f06c43c8535f22a4405` |

Independent read-only review recomputes summaries, stage sums, validator counts,
row coverage, audit flags and baseline/repeat equality, and checks all 126 source
hashes against the final tree. Existing safety/source/callback/atomic-publication
regressions passed before timing. The fixture has no source data and does not
measure real-world detector accuracy or source-adapter performance. No production
data, live databases or external AI providers were used.

## Evidence And Reproduction

| Artifact | SHA-256 |
| --- | --- |
| Current `public-csv-results.json` | `65e588a7784c6591e7e7d30517ef4ba3c3f93cdd081cc7701d79d6ee7520eb24` |
| Latest baseline `../schema-validation-performance/public-csv-results.json` | `8001de3b876dfbef3dc51dff012a61044df8c1492dec4fed6e902d864eb05da4` |

The unchanged driver still names `privacy-validation-performance` as its built-in
byte/hash baseline. The tables above explicitly compare against the latest
`schema-validation-performance` series. All historical evidence stays unchanged.

```bash
.venv/bin/python scripts/benchmark_public_csv.py \
  --rows 100000 750000 --repeats 3 \
  --output /private/tmp/value-normalization-public-csv.json
```

Use a new destination to preserve evidence. Process-list access is required for
local `ps` RSS sampling.
