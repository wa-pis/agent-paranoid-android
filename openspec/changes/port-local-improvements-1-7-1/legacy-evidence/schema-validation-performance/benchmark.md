# Public CSV After Schema-Validation Preparation

Measured 2026-11-23. All twelve runs succeeded. Raw metadata is in
[public-csv-results.json](public-csv-results.json); safety, equivalence and
regression evidence is in [validation.md](validation.md). The only runtime
change from the latest [baseline](../source-independent-profiling/benchmark.md)
is `validation/schema_validator.py`. The benchmark and fictional fixture are unchanged.

## Method

Use the public `generate_dataset_bundle` API, seed 42, 25 fields and
100,000 / 750,000 rows. Ordinary generation is serial; streaming uses four
workers and fixed 4,096-row tiles. Run three fresh subprocesses per size/path,
one at a time in alternating path order. No tests or other heavy verification
run concurrently with measurement. All mandatory checks and all four report
sections remain enabled. The instrumented functions and budget checks delegate
to their original implementations; no validator is stubbed or skipped.

Environment and settings exactly match the preceding series: Python 3.11.2,
macOS 26.6.2 arm64, 14 logical CPUs, Faker 40.35.0, Pydantic 2.13.4, PyYAML
6.0.3 and installed package metadata 1.5.0. The measured working tree is bound
by 126 source-file hashes. Limits remain 750,000 rows, 4 GiB output, 600 seconds
per worker and 18,750,000 streaming cells, with an external deadline of 660 seconds.

API time includes generation, checks, CSV, control artifacts, hashing and atomic
directory publication. Imports, subprocess startup and the independent parent
audit are excluded. Stages are exclusive coordinator wall time; workers generate
concurrently with validation, so streaming generation/IPC is not total worker
computation. Per-stage medians need not sum to the median API total.

## Public API And Schema Time

Times are medians of three repetitions. Ranges are minimum/maximum observations,
not confidence intervals. Before/after comparisons use historical baseline runs,
rather than interleaved old/new checkouts; workload and background variation
limit attribution of total API differences. A separate bounded interleaved
validator experiment is recorded in the verification document.

| Rows | Path | API before → after, s | Current API range, s | Less API time | Schema before → after, s | Less schema time |
| --- | --- | --- | --- | ---: | --- | ---: |
| 100,000 | Ordinary | 6.728698 → 6.323556 | 6.303188–6.331888 | 6.02% | 0.788141 → 0.321263 | 59.24% |
| 100,000 | Streaming, 4 workers | 3.327725 → 2.880147 | 2.872888–2.933736 | 13.45% | 0.822878 → 0.362795 | 55.91% |
| 750,000 | Ordinary | 50.786452 → 47.581540 | 47.068338–47.764899 | 6.31% | 5.955096 → 2.406416 | 59.59% |
| 750,000 | Streaming, 4 workers | 22.164009 → 18.447407 | 18.362994–18.504159 | 16.77% | 6.294248 → 2.749296 | 56.32% |

Schema time falls by 55.91–59.59%. Ordinary export takes 6.02–6.31% less
API time; streaming takes 13.45–16.77% less. Ordinary generation and streaming
privacy validation remain the largest exposed stages. No cache, backend,
optional dependency, random-call order or seed algorithm was added or changed.

## Exclusive Stage Medians

Seconds. Relationship and constraint checks still execute; this fictional
specification has no relationships or business constraints. `—` means absent.
Control-file atomic writes remain in the write stage.

| Stage | 100k ordinary | 100k streaming | 750k ordinary | 750k streaming |
| --- | ---: | ---: | ---: | ---: |
| Setup and bookkeeping | 0.014234 | 0.026159 | 0.108811 | 0.023206 |
| Generation / IPC | 4.082516 | 0.514750 | 30.947335 | 0.619974 |
| Combined runner residual | 0.000288 | 0.005939 | 0.000294 | 0.042681 |
| Privacy validation | 1.146941 | 1.193213 | 8.577537 | 9.154148 |
| Schema validation | 0.321263 | 0.362795 | 2.406416 | 2.749296 |
| Relationship validation | 0.000003 | 0.000031 | 0.000003 | 0.000218 |
| Constraint validation | 0.000001 | 0.000018 | 0.000001 | 0.000127 |
| Normalization | 0.248572 | 0.265991 | 1.824381 | 2.072514 |
| Streaming global checks | — | 0.013533 | — | 0.111357 |
| CSV encoding | 0.476992 | 0.470309 | 3.552960 | 3.484826 |
| CSV / control-file writes | 0.005199 | 0.014437 | 0.024416 | 0.087015 |
| Artifacts and hashing | 0.021807 | 0.019580 | 0.113444 | 0.094301 |
| Atomic publication | 0.000142 | 0.000156 | 0.000135 | 0.000157 |

Median total validation, computed from each run's sum of the combined-runner
residual, privacy, schema, relationship, constraint and normalization stages, is
1.718172 / 1.825879 / 12.785204 / 13.994589 seconds respectively. Streaming global
checks remain separate.

## Peak Memory

MiB, maxima across three repeats for each metric independently. Tree RSS is a
concurrent coordinator-plus-descendant sum sampled at nominal 100 ms plus
sampling overhead; startup/export is included, the later parent audit excluded.
Sampling can miss brief peaks and count shared pages more than once. Coordinator
`ru_maxrss` is its own high-water mark. Do not add these columns or sum individual
process high-water marks; this is not exact physical memory or a hard RSS cap.

| Rows | Path | Tree RSS before → after | Coordinator RSS before → after |
| --- | --- | --- | --- |
| 100,000 | Ordinary | 290.30 → 269.36 | 295.97 → 296.44 |
| 100,000 | Streaming, 4 workers | 549.39 → 545.73 | 138.80 → 139.02 |
| 750,000 | Ordinary | 1912.06 → 1920.02 | 1915.28 → 1922.08 |
| 750,000 | Streaming, 4 workers | 763.91 → 770.06 | 231.36 → 230.08 |

The optimization introduces only field-count-sized, invocation-local metadata.
Observed memory changes are mixed and do not establish a memory reduction.
In particular, ordinary 100k sampled tree RSS falls while its coordinator
high-water mark barely changes. Streaming still costs more tree RSS at 100k
and less at 750k.

## Privacy, Determinism And File Safety

Every concrete validator and normalization covers exactly the requested rows:
one ordinary entity, or 25 streaming tiles at 100k / 184 at 750k. Combined
validation executes once per entity/tile; duplicate mandatory/report entry
points remain unused. All four report sections pass, including actual runtime
privacy checks. Exclusive stage sums equal API time in every run.

After each measured child exits, the independent parent streams the CSV to
check the exact header, 25 fields, row count and ordered unique synthetic keys.
It checks report validity, synthetic/no-source-reuse flags, manifest counts and
engine, exact artifact set and all output SHA-256 values. Directories are 0700
and files 0600; all process groups are stopped, no staging remains and every
scratch directory is removed. Only metadata/hashes are retained. This parent
audit does not classify every CSV cell again; the unchanged real runtime
privacy validator checks every generated row.

All repetitions within each size/path are byte-identical and match every
corresponding repetition of the latest source-independent baseline. They also
match the harness's older privacy-validation reference. Ordinary and streaming
outputs differ because their existing seed namespaces differ; each retains its
exact previous output.

| Rows | Path | CSV bytes | SHA-256 |
| --- | --- | ---: | --- |
| 100,000 | Ordinary | 28,177,934 | `24e6f6833a83cebc9b17e52bc7b7c07449527741348be3221e64553d1b3ab462` |
| 100,000 | Streaming, 4 workers | 28,175,783 | `76330b20f138af1c8b49d42fe8780057cd0b735895a98b0d98713cf715ab9979` |
| 750,000 | Ordinary | 211,322,612 | `5b3a754438204d3fb5dce71e814a8cbac6c4cd749b0db5b55576394dce1923dc` |
| 750,000 | Streaming, 4 workers | 211,321,616 | `735b3374822b27e5afccaa73ebde1773ae43b7e93a1f9f06c43c8535f22a4405` |

This benchmark consumes a fictional specification and does not time source
adapters, relationships or business rules, or estimate real-world detector
accuracy. Existing cross-source, privacy, callback and publication regressions
passed before timing; see the verification document. No production data, source
rows, live databases or external AI providers were used.

## Evidence And Reproduction

Independent read-only review verifies raw summaries, row/validator coverage,
stage sums, audit flags, baseline/repeat equality and all 126 source hashes
against the final working tree. The benchmark driver and historical evidence
remain unchanged.

| Artifact | SHA-256 |
| --- | --- |
| Current `public-csv-results.json` | `8001de3b876dfbef3dc51dff012a61044df8c1492dec4fed6e902d864eb05da4` |
| Latest baseline `../source-independent-profiling/public-csv-results.json` | `e2a84aed6a266c85d59295f8f19eb2d4d3882712391f9f896f59bbb4add84330` |

The driver's built-in byte/hash baseline still points to
`privacy-validation-performance`; comparisons in the tables above explicitly
use the newer source-independent baseline. Both remain intact.

```bash
.venv/bin/python scripts/benchmark_public_csv.py \
  --rows 100000 750000 --repeats 3 \
  --output /private/tmp/schema-validation-public-csv.json
```

Use a new destination to preserve evidence. Local process-list access is required
for `ps` RSS sampling.
