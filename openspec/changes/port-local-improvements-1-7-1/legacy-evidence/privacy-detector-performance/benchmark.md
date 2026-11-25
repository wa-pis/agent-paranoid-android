# Public CSV After Detector Dispatch Optimization

This repeats the immediately preceding [privacy-validation experiment](../privacy-validation-performance/benchmark.md).
Only two necessary-character guards were added to the common content classifier:
the original assignment regex requires `:` or `=`, and the email regex requires
`@`. Builtin string membership preserves the original behavior for subclasses
that override membership. Every regex, flag, classification priority and helper
(including floating-point entropy calculations) remains unchanged. Raw runs are
in [public-csv-results.json](public-csv-results.json).

## Method And Verification

Use the same public `generate_dataset_bundle` API, fictional specification,
seed 42 and all mandatory/report checks: 100,000 / 750,000 rows × 25 fields.
Ordinary generation remains serial; streaming uses four workers and fixed
4,096-row tiles. Three fresh subprocesses per case run in alternating order,
one at a time, with no concurrent heavy verification. Both paths retain finite
750,000-row, 4 GiB output and 600-second budgets (external deadline 660 seconds);
streaming additionally limits cells to 18,750,000. Defaults are unchanged.

Hardware is Apple M4 Max, 14 logical CPUs and 36 GiB RAM, confirmed locally.
The environment remains Python 3.11.2, Faker 40.35.0, Pydantic 2.13.4,
PyYAML 6.0.3 and macOS 26.6.2 arm64. New measurements are dated 2026-11-22;
the baseline is the recorded prior series, not interleaved old/new checkouts.
Absolute performance and the value of a negative-match guard depend on workload.

Instrumentation delegates original functions and streaming budget checks. Every
concrete validator and normalization must execute once per complete ordinary
entity or tile, covering every requested row. Stages are exclusive coordinator
wall times; the combined runner records only work outside nested validators.
Workers also compute while the coordinator validates, so streaming generation /
IPC time is not total worker computation. Per-stage medians need not sum to the
median total. Shared control-file atomic writes remain in the file-write stage.

API time includes generation, checks, CSV, artifacts/hashes and atomic directory
publication. Imports, subprocess startup and the independent parent audit are
outside API time. The parent samples concurrent coordinator-plus-descendant RSS
at nominal 100 ms plus sampling overhead; this covers startup/export, excluding
the later audit. Report maxima across repeats separately from coordinator
`ru_maxrss`; brief peaks may be missed and shared pages counted more than once.
This does not measure exact physical memory or enforce a hard RSS cap.

After each child exits, the parent streams its CSV to check header, 25 columns,
count and ordered unique synthetic keys. It checks all report sections, manifest
flags/counts/actual engine, exact required artifacts and every output hash,
0700 directories, 0600 files, no staging residue and complete scratch removal.
Owned process groups are stopped before audit and cleanup. Only metadata/hashes
remain; independent review verifies recorded evidence and the audit code.

Every CSV byte count and SHA-256 must equal its prior privacy-validation
reference; repeats must match within each size/path. Different seed namespaces
still distinguish ordinary from tiled output. Failed attempts remain recorded
and prevent completion. Source hashes and the baseline artifact hash are saved;
historical evidence stays unchanged.

## Results

All twelve attempts succeeded: three repeats per size/path, no failures. The
table compares median total public API time against the immediately preceding
privacy-validation series. Ranges are the minimum and maximum of the new three
runs, not confidence intervals.

| Rows × 25 fields | Path | Before, s | After, s | New range, s | Less API time |
| --- | --- | ---: | ---: | --- | ---: |
| 100,000 | Ordinary | 7.019 | 6.884 | 6.880–6.999 | 1.93% |
| 100,000 | Streaming, 4 workers | 3.624 | 3.334 | 3.323–3.414 | 7.99% |
| 750,000 | Ordinary | 52.975 | 50.967 | 50.561–51.117 | 3.79% |
| 750,000 | Streaming, 4 workers | 24.081 | 21.756 | 21.587–21.832 | 9.65% |

Privacy checking took 21.77–23.85% less time. The separate bounded classifier
profile measured 30.47% less classifier time; traversal and policy work remain
in the public privacy stage. Ordinary generation still dominates API time, so
its overall benefit is modest. For example, its 100k generation stage took
4.180 seconds versus 4.015 in the prior series, partly offsetting detector gains.
Neither series is a paired before/after experiment; background variation and
workload composition limit attribution of the total API difference.

| Rows | Path | Privacy before, s | Privacy after, s | Less privacy time | All validation before → after, s |
| --- | --- | ---: | ---: | ---: | --- |
| 100,000 | Ordinary | 1.476 | 1.124 | 23.85% | 2.496 → 2.185 |
| 100,000 | Streaming | 1.521 | 1.190 | 21.77% | 2.610 → 2.291 |
| 750,000 | Ordinary | 10.918 | 8.327 | 23.73% | 18.698 → 16.162 |
| 750,000 | Streaming | 11.488 | 8.907 | 22.47% | 19.613 → 17.211 |

All-validation medians are computed from each run's sum of the combined-runner
residual, privacy, schema, relationship, constraint and normalization times.

## Exclusive Stage Medians

Seconds, rounded to six decimal places. Relationship and constraint validation
still execute; this synthetic specification has no relationships or business
constraints. An absent stage is shown as `—`.

| Exclusive stage | 100k ordinary | 100k streaming | 750k ordinary | 750k streaming |
| --- | ---: | ---: | ---: | ---: |
| Setup and bookkeeping | 0.015349 | 0.010636 | 0.108841 | 0.023493 |
| Generation / IPC | 4.180149 | 0.519648 | 30.923553 | 0.620685 |
| Combined runner residual | 0.000182 | 0.003538 | 0.000196 | 0.024345 |
| Privacy validation | 1.124028 | 1.189628 | 8.327086 | 8.906954 |
| Schema validation | 0.808841 | 0.835051 | 6.009918 | 6.254906 |
| Relationship validation | 0.000003 | 0.000036 | 0.000003 | 0.000246 |
| Constraint validation | 0.000001 | 0.000017 | 0.000001 | 0.000126 |
| Normalization | 0.250297 | 0.268043 | 1.850568 | 2.015196 |
| Streaming global checks | — | 0.015976 | — | 0.111017 |
| CSV encoding | 0.480901 | 0.463380 | 3.558558 | 3.492600 |
| CSV / control-file writes | 0.008625 | 0.020609 | 0.043036 | 0.173194 |
| Artifacts and hashing | 0.022098 | 0.019812 | 0.154542 | 0.094097 |
| Atomic publication | 0.000155 | 0.000163 | 0.000151 | 0.000154 |

## Peak Memory

MiB, maxima over three repeats for each metric independently. Tree RSS is a
sampled concurrent sum; coordinator RSS is its own high-water mark. Do not add
these columns or sum per-process high-water marks.

| Rows | Path | Tree RSS before → after, MiB | Coordinator before → after, MiB |
| --- | --- | --- | --- |
| 100,000 | Ordinary | 265.22 → 269.56 | 295.00 → 296.53 |
| 100,000 | Streaming | 547.44 → 541.75 | 140.81 → 138.38 |
| 750,000 | Ordinary | 1,914.53 → 1,918.36 | 1,916.58 → 1,918.39 |
| 750,000 | Streaming | 755.86 → 763.47 | 231.44 → 229.08 |

The optimization adds no cache or retained collection. These observations show
similar memory use, with small changes in both directions; they do not establish
a memory reduction. Streaming has more process overhead at 100k and lower peak
tree RSS than ordinary export at 750k.

## Completed Checks And Determinism

Every run passed the independent CSV, report, manifest, hash, permission and
cleanup audits described above. Each concrete validator and normalization
covered exactly the requested row count: one complete ordinary entity or
25 streaming tiles at 100k / 184 at 750k. Per-run exclusive stages sum to total
API time. All required report sections remained enabled, temporary directories
were removed, and no partial staging remained.

All twelve CSVs match their preceding-series reference in byte count and
SHA-256; all three repeats within each size/path also match. They additionally
match the earlier shared-validation and public-streaming evidence. Ordinary and
streaming outputs remain different because their established seed namespaces
differ; this change preserves the exact output of each path.

| Rows | Path | CSV bytes | SHA-256 |
| --- | --- | ---: | --- |
| 100,000 | Ordinary | 28,177,934 | `24e6f6833a83cebc9b17e52bc7b7c07449527741348be3221e64553d1b3ab462` |
| 100,000 | Streaming | 28,175,783 | `76330b20f138af1c8b49d42fe8780057cd0b735895a98b0d98713cf715ab9979` |
| 750,000 | Ordinary | 211,322,612 | `5b3a754438204d3fb5dce71e814a8cbac6c4cd749b0db5b55576394dce1923dc` |
| 750,000 | Streaming | 211,321,616 | `735b3374822b27e5afccaa73ebde1773ae43b7e93a1f9f06c43c8535f22a4405` |

The result captures 125 source-file hashes, all matching the measured working
tree. The only runtime change from the preceding experiment is the classifier
dispatch guard; `core/privacy.py` SHA-256 is
`642dfde5ce68f256bc2a0bcd833f97d603104f509e82008a6c5c00c87af0c23f`.
The benchmark script changes only its new-result default and baseline paths.
Historical JSON and Markdown evidence remains unchanged; fingerprints and
regression results are in [validation.md](validation.md).

## Reproduction

```bash
.venv/bin/python scripts/benchmark_public_csv.py \
  --rows 100000 750000 --repeats 3 \
  --output /private/tmp/detector-performance-public-csv.json
```

Use a separate destination to preserve the experiment; the script's default
now targets this change's recorded raw-results path.
