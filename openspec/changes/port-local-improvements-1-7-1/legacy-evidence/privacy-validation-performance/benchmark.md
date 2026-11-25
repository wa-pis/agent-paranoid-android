# Public CSV After Privacy Optimization

This repeats the [shared-validation public CSV benchmark](../shared-generation-validation/benchmark.md)
after preparing privacy field policy once per call and avoiding string-detector
calls for actual non-string scalars. String detectors, their ordering and
synthetic namespaces are unchanged. Raw measurements are in
[public-csv-results.json](public-csv-results.json).

## Results

Measured 2026-11-21. All 12 attempts succeeded; the whole recorded environment
and shared benchmark settings match the immediately preceding experiment.
API times are medians of three runs, with observed ranges.

| Rows × fields | Public path | Before, seconds | After, seconds (range) | Speedup |
| --- | --- | ---: | ---: | ---: |
| 100,000 × 25 | Legacy, serial | 9.552 | 7.019 (6.999–7.146) | 1.36× |
| 100,000 × 25 | Streaming, 4 workers | 6.084 | 3.624 (3.611–3.667) | 1.68× |
| 750,000 × 25 | Legacy, serial | 70.874 | 52.975 (52.638–53.046) | 1.34× |
| 750,000 × 25 | Streaming, 4 workers | 41.957 | 24.081 (24.024–24.325) | 1.74× |

Elapsed time fell by 26.5% / 25.3% for legacy and 40.4% / 42.6% for streaming
at 100k / 750k. Privacy itself improved by approximately 2.6× on both paths:

| Rows | Path | Privacy before, seconds | Privacy after, seconds |
| --- | --- | ---: | ---: |
| 100,000 | Legacy | 3.846 | 1.476 |
| 100,000 | Streaming | 3.943 | 1.521 |
| 750,000 | Legacy | 28.666 | 10.918 |
| 750,000 | Streaming | 29.610 | 11.488 |

Peak memory observations, MiB (maximum of three runs):

| Rows | Path | Before sampled tree RSS | After sampled tree RSS | Before coordinator high-water RSS | After coordinator high-water RSS |
| --- | --- | ---: | ---: | ---: | ---: |
| 100,000 | Legacy | 270.4 | 265.2 | 297.3 | 295.0 |
| 100,000 | Streaming | 562.1 | 547.4 | 143.4 | 140.8 |
| 750,000 | Legacy | 1,911.3 | 1,914.5 | 1,911.3 | 1,916.6 |
| 750,000 | Streaming | 764.9 | 755.9 | 233.2 | 231.4 |

Memory remains comparable; this change primarily saves CPU time. At 100k the
sampler misses a brief coordinator peak. Keep coordinator high-water RSS and
sampled concurrent tree RSS separate. Streaming continues to use more total
memory at 100k and less at 750k. No hard memory cap or automatic crossover was
introduced; the streaming global-key set still grows with row count.

Exclusive stage medians after optimization, seconds:

| Stage | 100k legacy | 100k streaming | 750k legacy | 750k streaming |
| --- | ---: | ---: | ---: | ---: |
| Setup / remaining bookkeeping | 0.013 | 0.009 | 0.102 | 0.028 |
| Generation / IPC / coordinator wait | 4.015 | 0.491 | 30.381 | 0.572 |
| Strict generated-row privacy | 1.476 | 1.521 | 10.918 | 11.488 |
| Schema / types / per-entity keys | 0.781 | 0.824 | 5.931 | 6.148 |
| Relationships | 0.000003 | 0.000026 | 0.000003 | 0.000196 |
| Constraints | 0.000001 | 0.000016 | 0.000001 | 0.000120 |
| Normalization | 0.246 | 0.263 | 1.841 | 1.955 |
| Combined-validation residual / report assembly | 0.000169 | 0.002958 | 0.000177 | 0.021786 |
| Streaming sequence / global keys | — | 0.012 | — | 0.097 |
| CSV formatting / UTF-8 encoding | 0.475 | 0.459 | 3.567 | 3.477 |
| File writes / atomic file finalization | 0.006 | 0.036 | 0.033 | 0.239 |
| Artifact construction / hashing / size checks | 0.025 | 0.018 | 0.174 | 0.088 |
| Complete directory publication | 0.000137 | 0.000123 | 0.000141 | 0.000139 |

Total shared-validation medians, aggregated within each run before taking the
median, are 2.496 / 2.610 seconds at 100k and 18.698 / 19.613 at 750k
(legacy / streaming). Privacy remains the largest coordinator stage, with the
unchanged string-content detectors dominating its remaining cost. No value
cache, detector bypass or weakened policy was used to obtain the speedup.

All 12 CSV SHA-256 values and byte counts match every corresponding repeat in
both the immediately preceding and original public benchmarks. Report sections,
manifest flags/engine/counts/hashes, private permissions and complete scratch
cleanup passed in every run; worker stderr was empty. Each concrete validator,
normalization and the combined runner executed once per complete legacy entity
or streaming tile (25 / 184 tiles at 100k / 750k), covering every requested row.
Every run's exclusive stages sum exactly to API time. Independent review
recomputed the whole summary and checked all 125 source hashes remain unchanged,
the classifier hash matches both baselines, and historical evidence is intact.

## Method And Checks

The fixture, public `generate_dataset_bundle` API, seed 42 and all checks are
unchanged: 100,000 / 750,000 rows × 25 fields; serial ordinary export versus
four-worker streaming with fixed 4,096-row tiles. Each case has three fresh
subprocesses, alternating order, one at a time. No heavy tests run during the
measurement series. The preceding environment is retained: Python 3.11.2,
Faker 40.35.0, Pydantic 2.13.4, PyYAML 6.0.3; Apple M4 Max, 14 logical CPUs,
36 GiB RAM, macOS 26.6.2 arm64.

Both paths retain finite 750,000-row, 4 GiB output and 600-second limits, with
an external 660-second deadline. Streaming also limits cells to 18,750,000.
No package defaults, public options, dependencies or CSV eligibility changed.

Instrumentation delegates original functions and budget checks. Each concrete
validator and normalization must execute exactly once per complete legacy entity
or streaming tile and cover every row. Their exclusive times plus the combined
runner's residual form total shared-validation time. Streaming generation and
IPC time is coordinator wall time; workers also run while earlier tiles are
validated. Independently calculated stage medians need not sum to median total.
Shared atomic writes for control files remain in the file-write stage.

API timings include generation, every check, CSV encoding/write, control
artifacts, output hashing and complete atomic bundle publication. Imports,
process startup and the parent verification scan are outside API time. RSS
sampling covers subprocess startup and export but excludes that later audit.
The parent samples concurrent coordinator-plus-descendant RSS with `ps` at a
nominal 100 ms plus sampling overhead. Report maxima across repeats separately
from coordinator `ru_maxrss`; brief peaks may be missed and shared pages counted
more than once. This is not a physical-memory measurement or hard RSS cap.

After each worker exits, the parent streams the CSV to check exact header,
25 columns, row count and ordered unique synthetic key range. It checks all four
report sections, manifest flags/counts/engine, the exact output hash map, private
0700/0600 permissions, absence of staging files and removal of its scratch
directory. Process groups are stopped before audit and cleanup. Only metadata
and hashes remain, not generated rows. Independent review checks those recorded
results and the audit implementation; the cleaned output files are not retained.

Every CSV byte count and SHA-256 must match the corresponding pre-optimization
shared-validation reference. Repeated hashes must match within each path/size;
the legacy and tiled seed namespaces still differ from each other. Failed
attempts remain in the raw JSON and prevent successful completion. The complete
current source snapshot and reference JSON hash are recorded. The original
historical evidence files remain immutable.

## Reproduction

```bash
.venv/bin/python scripts/benchmark_public_csv.py \
  --rows 100000 750000 --repeats 3 \
  --output /private/tmp/privacy-performance-public-csv.json
```

The script defaults to this change's new raw-results file; use a separate path
to retain the recorded experiment. Before/after comparison uses the prior series,
rather than interleaved old/new checkouts, on matching dependencies and hardware.
