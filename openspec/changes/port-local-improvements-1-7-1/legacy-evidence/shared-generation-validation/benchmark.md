# Public CSV After Shared Validation

This repeats the [earlier public CSV experiment](../public-streaming-csv/public-csv-benchmark.md)
after removing redundant validation. New raw measurements are in
[public-csv-results.json](public-csv-results.json); the earlier JSON and report
remain unchanged historical evidence. Both ordinary and streaming CLI exports
reach the optimized bundle paths when no actual rule applier is supplied.

## Results

Measured 2026-11-21. All 12 attempts succeeded, with three repetitions per case,
no worker stderr, successful artifact audits and complete temporary cleanup.
The environment recorded by the old and new experiments matches exactly.

| Rows × fields | Public path | Before, seconds | After, seconds (range) | Speedup vs same path |
| --- | --- | ---: | ---: | ---: |
| 100,000 × 25 | Legacy, serial | 18.909 | 9.552 (9.491–9.555) | 1.98× |
| 100,000 × 25 | Streaming, 4 workers | 11.141 | 6.084 (6.069–6.114) | 1.83× |
| 750,000 × 25 | Legacy, serial | 140.921 | 70.874 (69.742–70.911) | 1.99× |
| 750,000 × 25 | Streaming, 4 workers | 80.160 | 41.957 (41.581–42.385) | 1.91× |

Numbers are API medians. This removes 49.5% / 49.7% of legacy elapsed time and
45.4% / 47.7% of streaming elapsed time at 100k / 750k. After optimization,
streaming remains 1.57× / 1.69× faster than serial export at these two sizes.
The baseline is the previously recorded series rather than interleaved old/new
checkouts. Identical dependencies, fixture, policies and CSV fingerprints support
the comparison; absolute timings remain specific to this machine and workload.

Peak memory observations, MiB (maximum of three runs):

| Rows | Path | Before sampled tree RSS | After sampled tree RSS | Before coordinator high-water RSS | After coordinator high-water RSS |
| --- | --- | ---: | ---: | ---: | ---: |
| 100,000 | Legacy | 301.9 | 270.4 | 304.4 | 297.3 |
| 100,000 | Streaming | 569.5 | 562.1 | 145.5 | 143.4 |
| 750,000 | Legacy | 1,939.3 | 1,911.3 | 1,940.6 | 1,911.3 |
| 750,000 | Streaming | 764.4 | 764.9 | 232.0 | 233.2 |

Memory is broadly comparable, with no material large-streaming memory increase.
At 100k the sampler misses a short coordinator peak, so sampled RSS alone must
not be interpreted as an equally large reduction in true peak memory. Streaming
still costs more total memory at 100k and less at 750k. Global key state remains
proportional to row count; no hard RSS cap or automatic size threshold was added.

Exclusive stage medians after optimization, seconds:

| Stage | 100k legacy | 100k streaming | 750k legacy | 750k streaming |
| --- | ---: | ---: | ---: | ---: |
| Setup / remaining bookkeeping | 0.015 | 0.011 | 0.100 | 0.021 |
| Generation / IPC / coordinator wait | 4.122 | 0.510 | 30.211 | 0.571 |
| Strict generated-row privacy | 3.846 | 3.943 | 28.666 | 29.610 |
| Schema / types / per-entity keys | 0.793 | 0.829 | 5.896 | 6.078 |
| Relationships | 0.000003 | 0.000036 | 0.000003 | 0.000183 |
| Constraints | 0.000001 | 0.000017 | 0.000001 | 0.000110 |
| Normalization | 0.246 | 0.261 | 1.819 | 1.975 |
| Combined-validation remaining work / report assembly | 0.000178 | 0.003473 | 0.000186 | 0.022184 |
| Streaming sequence / global-key checks | — | 0.014 | — | 0.094 |
| CSV formatting / UTF-8 encoding | 0.476 | 0.455 | 3.533 | 3.358 |
| File writes / atomic file finalization | 0.006 | 0.023 | 0.038 | 0.121 |
| Artifact construction / hashes / size checks | 0.026 | 0.020 | 0.113 | 0.089 |
| Complete directory publication | 0.000148 | 0.000133 | 0.000143 | 0.000157 |

Median total shared-validation time, aggregated within each run before taking
the median, is 4.884 / 5.039 seconds at 100k and 36.431 / 37.693 seconds at 750k
(legacy / streaming). Privacy is now the largest measured stage. The fixture
contains no relationships or constraints, but those validators still execute;
nonempty rules are covered by regression tests rather than this performance case.

Every concrete validator and normalization covered all rows exactly once: one
call per complete legacy entity, 25 / 184 calls for streaming at 100k / 750k.
Every run's exclusive stage total equals its API wall time. All 12 output hashes
and byte counts match the pre-optimization reference for that path/size, and all
three repetitions within each case are identical. The source snapshot stayed
unchanged throughout the series. Independent review recomputed the summaries
and verified the original evidence files remain unmodified.

## Method

Use the unchanged fictional fixture, seed 42, 100,000 / 750,000 rows × 25 fields,
and public `generate_dataset_bundle` API. Legacy generation remains serial;
streaming uses four workers and fixed 4,096-row tiles. All four report sections
and all mandatory checks stay enabled. Three fresh subprocesses per path/size
run in alternating order, one at a time, with no concurrent heavy verification.

The same `.venv` and machine as the baseline are used: Python 3.11.2,
Faker 40.35.0, Pydantic 2.13.4, PyYAML 6.0.3, Apple M4 Max, 14 logical CPUs,
36 GiB RAM, macOS 26.6.2 arm64. Each run retains finite limits of 750,000 rows,
4 GiB output and 600 seconds, with an external 660-second deadline. Streaming
additionally limits cells to 18,750,000. Package defaults are unchanged.

`scripts/benchmark_public_csv.py` still wraps original public operations and
observes streaming budget phases, delegating all real checks. It now also counts
and times concrete schema, privacy, relationship, constraint and normalization
calls. For this canonical fixture every validator and normalization must run
exactly once per row mapping/tile, covering exactly the requested rows. The
combined runner also runs once per mapping/tile; its exclusive timing excludes
those nested validators. Shared-validation total is the sum of the five concrete
stages plus `combined_validation` (report assembly and remaining mandatory work).

Normalization-changing inputs have separate regression tests: a passed raw
schema cannot authorize normalized aliases such as primary keys `1` and `"1"`.
They retain every needed normalized check, even if that requires another pass.
Any actual business callback retains checks before and after possible mutation.

API wall time includes bundle generation, checks, CSV, artifacts/hashes and atomic
publication. Imports, process startup and the parent audit are outside API time.
Stages are exclusive coordinator wall time; worker computation overlaps tile
validation and is not represented by the streaming generation/wait stage alone.
Per-stage medians need not sum to the median total. Shared control-file atomic
writes are counted in the file-write stage as in the baseline.

The parent samples concurrent coordinator-plus-descendant RSS with `ps` at a
nominal 100 ms interval plus sampling overhead. Report maximum sampled tree RSS
across repeats, separately from the coordinator's `ru_maxrss`; do not add their
peaks. Shared pages can be counted repeatedly and brief peaks can be missed.
Sampling includes subprocess startup, but excludes the later independent audit.

## Result Checks

The parent streams each finished CSV to verify the exact header, 25 columns,
requested count and ordered unique key range. It checks all report sections,
manifest flags/row counts/actual engine, every required artifact/hash, 0700 output
directories, 0600 files, no remaining staging entries and removal of the private
scratch directory. Process groups are stopped before auditing/cleanup.

Every benchmark CSV must have exactly the same SHA-256 and byte count as its
pre-optimization public-path reference; mismatch is recorded as a failed run.
Repeat hashes must also match within each path/size. Legacy and `tiled-v1` retain
different seed namespaces; cross-engine row equality is not expected.
Only metadata/hashes are retained. Failed attempts remain in the JSON and prevent
successful completion. New source hashes and the baseline JSON hash are recorded.

## Reproduction

```bash
.venv/bin/python scripts/benchmark_public_csv.py \
  --rows 100000 750000 --repeats 3 \
  --output /private/tmp/shared-validation-public-csv.json
```

This command uses the recorded baseline in the checkout for byte-identity checks.
The benchmark script's default output is the new change's raw-results file;
use a separate destination to preserve this recorded run.
