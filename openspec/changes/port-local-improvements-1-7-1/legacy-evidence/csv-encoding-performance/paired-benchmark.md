# Paired Public CSV Encoding Benchmark

Protocol recorded on 2026-11-24, before the paired measurements. All 32 measured
runs and four smoke runs succeeded. **Keep the two-line guard:** encoding improved
in 15 of 16 pairs, with no material peak-memory regression observed. Raw metadata
is in [paired-results.json](paired-results.json). The earlier
[historical comparison](benchmark.md) remains evidence from separate runs; it does
not establish the guard's effect on total export time.

## Comparison And Order

Compare the current two-line early return in `io/writers.py` with the same source
tree after removing only that return. Both variants use the unchanged
`benchmark_public_csv.py` `measure`, `worker`, `instrument` and `audit` functions.
The thin [paired driver](../../../scripts/benchmark_paired_csv.py) controls source
selection, order and reporting; it does not replace validation or CSV encoding.

There are four adjacent before/after pairs for each case: ordinary and streaming
public CSV export, each with 100,000 and 750,000 rows and 25 fields. This gives
32 measured runs, four observations per variant per case. Odd pairs run before
then after; even pairs run after then before. Path order also alternates:

| Pair | Path order | Version order within each path |
| --- | --- | --- |
| 1 | Ordinary, streaming | Before, after |
| 2 | Streaming, ordinary | After, before |
| 3 | Ordinary, streaming | Before, after |
| 4 | Streaming, ordinary | After, before |

Run the complete schedule first at 100,000 rows, then at 750,000 rows. Runs are
serial, with no concurrent tests or other heavy verification. Keep every measured
observation; do not discard or replace a slow run. Four additional four-row smoke
runs, one per variant/path combination, check isolation and full audit execution
before the measured schedule and are excluded from performance summaries.

## Source Isolation And Provenance

Create two private temporary copies of `src/test_data_agent` and the unchanged
public-CSV and parallel-generation benchmark scripts. Exclude bytecode caches.
Source SHA256 maps must have identical paths and differ only at
`src/test_data_agent/io/writers.py`; the before copy removes exactly one occurrence
of the measured guard. No measured checkout is edited between observations.

Each run starts a fresh helper with the same absolute Python executable and
`PYTHONPATH` selecting its snapshot's source and scripts. The helper verifies that
the package, benchmark and relevant generation/export modules originate inside
that snapshot, and that streaming uses the shared writer's neutralizer. The
unchanged benchmark subprocess inherits this environment; spawned generation
workers inherit the coordinator's module search path. `PYTHONHASHSEED=0` and
`PYTHONDONTWRITEBYTECODE=1` apply equally to both variants.

Record each run's import origins and writer hash. Verify the source fingerprints
before each measured run and after the complete schedule. Record the paired
driver's hash, dependency versions, Python/platform information and the historical
CSV reference artifact's hash. Snapshots and generated bundles must be removed
after use; final completion requires successful cleanup and unchanged snapshots.
Raw results are retained in [paired-results.json](paired-results.json), without
generated rows.

## Workload And Retained Checks

Use the existing fictional 25-field specification and seed 42. Ordinary generation
retains its legacy seed namespace. Streaming retains `tiled-v1`, four workers and
fixed 4,096-row logical tiles. Compare exact CSV bytes within each engine across
variants and repeats; the two engines intentionally produce different seeded
values and are not required to match each other.

Keep the existing limits: 750,000 generation rows, 4 GiB output, 600 seconds for
the generation budget, 660 seconds for the benchmark's external deadline and
18,750,000 streaming cells. The unchanged worker and audit retain:

- Mandatory privacy, schema, relationship and constraint checks, plus all four
  validation-report sections; no report setting disables mandatory safety.
- Exact combined-validation, concrete-validator and normalization call/row counts:
  one ordinary batch, or one per streaming tile, covering every generated row.
- Synthetic-output markers, no-source-row-copy markers, exact entity row counts
  and exclusive-stage accounting equal to total measured API time.
- Independent CSV parsing for the exact header, 25 cells per row, total count,
  ordered unique key range and SHA256/byte-count equality against the existing
  reference for that engine and size.
- Successful complete reports, manifest engine/count/validation markers, exact
  artifact membership and matching hashes for every declared output.
- Private output directories/files (0700/0600), no partial staging artifacts and
  removal of each temporary bundle.

The guard changes neither the atomic writers nor their failure boundaries.
Failure-injection, formula-neutralization and edge-case equivalence tests remain
the separate regression evidence in [validation.md](validation.md); successful
benchmark exports alone do not prove every failure path.

## Timing And Memory

API time includes generation, validation, CSV conversion/writes, control artifacts,
hashing and atomic publication. Imports, process startup and the independent parent
audit are outside API timing. Stage times are exclusive coordinator wall time:
setup/bookkeeping, generation/IPC, combined-runner residual, privacy, schema,
relationships, constraints, normalization, streaming global checks, CSV encoding,
CSV/control-file writes, artifacts/hashing and publication. Both paths' encoding
stage includes UTF-8 conversion. Streaming generation/IPC measures exposed waiting
and coordinator work while workers run concurrently, not summed worker CPU time.

Report each variant's total/stage medians and observed ranges, paired after-minus-
before differences and paired percentage changes. A positive time change means
slower. Count encoding wins and inspect the individual AB and BA pairs. Medians of
stages need not sum to the median total; a median of paired percentage changes need
not equal the percentage change between the two variant medians.

Peak tree RSS uses the existing concurrent coordinator-plus-descendant `ps` sum,
sampled at nominal 100 ms plus sampling overhead during the benchmark subprocess.
Brief peaks may be missed and shared pages may be counted repeatedly. Coordinator
`ru_maxrss` is a separate process high-water mark. Report both metrics, maxima per
variant and paired changes; never add their values or sum separate process maxima.
The parent audit and orchestration helpers are outside the sampled tree. These are
RSS observations, not exact physical-memory measurements or hard memory caps.

## Predeclared Decision Rule

> Retain only if paired encoding gains repeat without a consistent API-time or
> peak-memory regression; consider individual pairs and AB/BA order, not historical
> medians.

Apply this rule after all 32 measured runs and safety/equality checks complete.
Inspect both paths and sizes, order effects and all paired observations. Do not
infer a public API speedup from an isolated encoder improvement or from the
earlier historical series. If the evidence does not support retaining the guard,
remove only its two lines and preserve the safety/equivalence tests and benchmark
records. Four pairs per case provide a bounded local experiment, not a confidence
interval or a claim about every workload, machine or source adapter.

## Paired Results

All times are seconds unless stated otherwise. Each variant has four observations
per case. Percentage changes are medians of the four paired ratios; negative means
less time. Wins count pairs where the after variant took less time.

| Rows | Path | API median before → after | Encoding median before → after | Paired API change | API wins | Paired encoding change | Encoding wins |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| 100,000 | Ordinary | 6.342866 → 6.338153 | 0.481385 → 0.460098 | -0.586% | 3/4 | -4.499% | 3/4 |
| 100,000 | Streaming, 4 workers | 2.833280 → 2.806237 | 0.476568 → 0.452260 | -0.920% | 2/4 | -4.873% | 4/4 |
| 750,000 | Ordinary | 47.397296 → 47.157732 | 3.655337 → 3.476291 | -0.604% | 4/4 | -3.846% | 4/4 |
| 750,000 | Streaming, 4 workers | 17.711361 → 17.401265 | 3.589489 → 3.375135 | -1.547% | 4/4 | -5.944% | 4/4 |

Observed API minimum/maximum ranges, with no observation discarded:

| Rows | Path | Before range | After range |
| --- | --- | --- | --- |
| 100,000 | Ordinary | 6.230170–6.414212 | 6.248857–6.404272 |
| 100,000 | Streaming, 4 workers | 2.820319–2.861029 | 2.760851–3.112789 |
| 750,000 | Ordinary | 47.106788–48.069762 | 46.890777–47.405383 |
| 750,000 | Streaming, 4 workers | 17.584107–17.824840 | 17.347661–17.571833 |

Encoding wins in all eight AB pairs and seven of eight BA pairs. Total API time
wins in 13 of 16 pairs, including all eight 750,000-row pairs. At 100,000 rows the
API outcome is mixed: the streaming after variant is 8.800% slower in pair 2,
despite 25.825 ms less encoding time, and 0.184% slower in pair 3. The ordinary
after variant is 2.273% slower overall in pair 1, and its encoding is 11.568 ms
slower in pair 2. All these observations remain in the results. The experiment
supports a repeatable encoder gain; it does not guarantee faster total exports
for every run or attribute movements in unchanged stages to the guard.

## Exclusive Stage Medians

Each cell shows before → after, in seconds, rounded to six decimal places.
`—` is absent in ordinary generation. Relationship and constraint checks still
execute on this fixture without relationships or business constraints.

| Stage | 100k ordinary | 100k streaming | 750k ordinary | 750k streaming |
| --- | --- | --- | --- | --- |
| Setup and bookkeeping | 0.014822 → 0.014990 | 0.011255 → 0.010786 | 0.112179 → 0.112020 | 0.017753 → 0.010754 |
| Generation / IPC | 4.174455 → 4.216277 | 0.562919 → 0.572089 | 31.331065 → 31.221657 | 0.704704 → 0.686851 |
| Combined runner residual | 0.000295 → 0.000289 | 0.006197 → 0.006177 | 0.000287 → 0.000293 | 0.044551 → 0.044288 |
| Privacy validation | 1.185869 → 1.167390 | 1.224958 → 1.199535 | 8.853135 → 8.746510 | 9.224245 → 9.164589 |
| Schema validation | 0.328318 → 0.329773 | 0.365716 → 0.363786 | 2.446602 → 2.422941 | 2.764920 → 2.774273 |
| Relationship validation | 0.000003 → 0.000003 | 0.000043 → 0.000038 | 0.000004 → 0.000004 | 0.000307 → 0.000301 |
| Constraint validation | 0.000001 → 0.000001 | 0.000017 → 0.000018 | 0.000001 → 0.000001 | 0.000123 → 0.000134 |
| Normalization | 0.122458 → 0.126667 | 0.134729 → 0.135126 | 0.929107 → 0.927576 | 1.032640 → 1.040081 |
| Streaming global checks | — | 0.014040 → 0.014756 | — | 0.114496 → 0.110636 |
| CSV encoding | 0.481385 → 0.460098 | 0.476568 → 0.452260 | 3.655337 → 3.476291 | 3.589489 → 3.375135 |
| CSV / control-file writes | 0.005112 → 0.005436 | 0.020699 → 0.037198 | 0.028163 → 0.024548 | 0.105520 → 0.096800 |
| Artifacts and hashing | 0.019278 → 0.019243 | 0.020108 → 0.019828 | 0.135686 → 0.182895 | 0.093870 → 0.090085 |
| Atomic publication | 0.000154 → 0.000173 | 0.000134 → 0.000158 | 0.000136 → 0.000159 | 0.000135 → 0.000136 |

## Peak Memory Results

MiB. Maxima are taken independently over the four runs of each variant. Paired
deltas are medians of the four after-minus-before observations. Paired percentage
changes are medians of the ratios, not ratios of these independent maxima.

| Rows | Path | Maximum tree RSS before → after | Maximum coordinator RSS before → after | Paired tree delta, MiB / % | Paired coordinator delta, MiB / % |
| --- | --- | --- | --- | --- | --- |
| 100,000 | Ordinary | 299.266 → 300.172 | 304.125 → 304.125 | -2.969 / -1.035% | -0.430 / -0.143% |
| 100,000 | Streaming, 4 workers | 572.922 → 573.578 | 141.641 → 140.094 | -1.727 / -0.307% | -3.266 / -2.305% |
| 750,000 | Ordinary | 1927.062 → 1927.797 | 1932.234 → 1927.828 | +1.805 / +0.094% | +1.023 / +0.053% |
| 750,000 | Streaming, 4 workers | 778.734 → 778.297 | 227.625 → 226.438 | +0.164 / +0.023% | -1.320 / -0.583% |

Memory changes have mixed signs. The 750,000-row ordinary path has higher tree
RSS in three pairs, by 0.063–5.656 MiB, and lower RSS in one pair, by 7.531 MiB;
its paired median change is +0.094%. The 750,000-row streaming paired median is
+0.023%, while both 100,000-row medians are negative. No material peak-memory
regression is observed across these cases. This is not a claim of identical
physical memory use; the sampling and shared-page limitations above still apply.

## Individual Pairs

AB means before then after; BA means after then before. All deltas are after
minus before. CSV deltas are milliseconds; memory deltas are MiB.

| Rows | Path | Pair / order | API change | Encoding change | Encoding delta, ms | Tree RSS delta | Coordinator RSS delta |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| 100,000 | Ordinary | 1 / AB | +2.273% | -3.231% | -15.425 | -32.391 | -1.328 |
| 100,000 | Ordinary | 2 / BA | -0.155% | +2.462% | +11.568 | +25.703 | +2.438 |
| 100,000 | Ordinary | 3 / AB | -1.068% | -6.652% | -32.282 | -3.641 | -3.469 |
| 100,000 | Ordinary | 4 / BA | -1.018% | -5.768% | -28.041 | -2.297 | +0.469 |
| 100,000 | Streaming, 4 workers | 1 / AB | -2.167% | -3.937% | -18.424 | -3.312 | +0.125 |
| 100,000 | Streaming, 4 workers | 2 / BA | +8.800% | -5.402% | -25.825 | -0.141 | -6.656 |
| 100,000 | Streaming, 4 workers | 3 / AB | +0.184% | -4.344% | -20.635 | +24.516 | +5.500 |
| 100,000 | Streaming, 4 workers | 4 / BA | -2.024% | -6.883% | -33.430 | -19.812 | -7.391 |
| 750,000 | Ordinary | 1 / AB | -1.382% | -5.449% | -199.336 | +5.656 | +4.641 |
| 750,000 | Ordinary | 2 / BA | -0.749% | -4.410% | -161.175 | -7.531 | +0.531 |
| 750,000 | Ordinary | 3 / AB | -0.459% | -2.596% | -92.179 | +3.547 | +1.516 |
| 750,000 | Ordinary | 4 / BA | -0.260% | -3.283% | -120.023 | +0.062 | -5.094 |
| 750,000 | Streaming, 4 workers | 1 / AB | -2.164% | -5.588% | -199.907 | +3.188 | -2.266 |
| 750,000 | Streaming, 4 workers | 2 / BA | -1.003% | -7.136% | -257.232 | +7.750 | +5.078 |
| 750,000 | Streaming, 4 workers | 3 / AB | -1.255% | -5.521% | -197.612 | -2.859 | -0.375 |
| 750,000 | Streaming, 4 workers | 4 / BA | -1.840% | -6.300% | -226.761 | -16.797 | -7.719 |

## Safety, Determinism And Cleanup Results

All 32 measured subprocesses exited successfully without stderr. Each run passed
every worker assertion and independent audit listed above: full validation report,
exact counts/header/ordered unique keys, synthetic/no-source-copy markers, all
manifest hashes, private output permissions and no partial staging. Each concrete
validator and normalization covered every row exactly once per ordinary batch or
streaming tile (25 tiles at 100,000 rows; 184 at 750,000 rows). Exclusive-stage sums
match each measured API duration. All four smoke runs also passed.

CSV byte counts and SHA256 values match across all eight observations in each
case, between source variants and against the historical reference. The different
legacy and `tiled-v1` hashes are expected seed-namespace behavior.

| Rows | Path | CSV bytes | SHA256 |
| --- | --- | ---: | --- |
| 100,000 | Ordinary | 28,177,934 | `24e6f6833a83cebc9b17e52bc7b7c07449527741348be3221e64553d1b3ab462` |
| 100,000 | Streaming, 4 workers | 28,175,783 | `76330b20f138af1c8b49d42fe8780057cd0b735895a98b0d98713cf715ab9979` |
| 750,000 | Ordinary | 211,322,612 | `5b3a754438204d3fb5dce71e814a8cbac6c4cd749b0db5b55576394dce1923dc` |
| 750,000 | Streaming, 4 workers | 211,321,616 | `735b3374822b27e5afccaa73ebde1773ae43b7e93a1f9f06c43c8535f22a4405` |

Every generated bundle scratch directory was removed. Both source snapshots
remained unchanged throughout the measured schedule and were removed after it.
Every fresh helper's import-origin and writer-hash checks passed. Exactly one of the 126 measured
source/benchmark files differs between the variants: `io/writers.py`. Each variant
also matches all 126 hashes of its corresponding historical source artifact,
and those artifacts record the same dependency versions. Historical timings are
not included in the paired statistics.

## Environment And Evidence Digests

Python 3.11.2, macOS 26.6.2 arm64, 14 logical CPUs; installed package metadata
1.5.0, Faker 40.35.0, Pydantic 2.13.4 and PyYAML 6.0.3. Both variants use
`/Users/agrudin/dev/my/agent-paranoid-android/.venv/bin/python`. All limits,
workers, seed, hash seed, bytecode-cache policy and timing/RSS methods are those
recorded in the protocol and raw report. No live source adapter or production
rows are involved.

| Evidence | SHA256 |
| --- | --- |
| Paired raw results | `a49dc561b99be67cae219c06f109b23a2f475432be0ab9dd89bf27bb20f1c95f` |
| Paired driver | `f525002f47cd2ff2466fecbd67e13f8551e4690761be87624e063b8641174044` |
| Before writer | `2b3a824796ea8c074b3d92a476df89a6efd63f49ce3ead687c30280920d56ef8` |
| After writer | `47b9196b219de8b03fafb56b031159e67122a60fc1fcb6c00d8c3b9f17c15bc4` |
| Unchanged public CSV benchmark | `0d7dd4a458bf37ae1d381447319ac6ff31c453f90e3e2deb151b41879d4ea83e` |
| Unchanged parallel benchmark helper | `07b5fd3ac63d84b98f21076328866a97115b0241da99678520170bea011a0204` |
| Unchanged streaming CSV exporter | `14e6b1d24908034e009803254a08413f7c7a4ecd9975ae1030253059d41b218a` |
| Historical before source/reference artifact | `65e588a7784c6591e7e7d30517ef4ba3c3f93cdd081cc7701d79d6ee7520eb24` |
| Historical after source/CSV reference artifact | `3bcb174e80561d2fa26b06f52786a62a6b04656f95017b36caff80ecf280d937` |

## Decision

**Keep the two-line shared encoding guard.** The predeclared rule is satisfied:
encoding wins in 15 of 16 adjacent pairs across both version orders, with median
paired reductions of 3.846–5.944% across the four cases. Total API observations
also favor the after variant in 13 of 16 pairs and all eight large-workload pairs,
while measured peak-memory changes show no material regression. Full privacy,
validation, determinism, output integrity and cleanup checks pass for both variants.

Keep the existing safety/equivalence tests and atomic writers. Do not add a new
backend, dependency, encoding loop or cache for this result. The total API
improvement is modest and the 100,000-row outcomes remain mixed; four local pairs
per case do not establish a guaranteed export speedup, statistical confidence or
performance on other workloads, machines or source adapters.

