# Implementation Evidence — 2026-11-08

This is synthetic development evidence, not a release acceptance manifest or
manual human MCP acceptance. Numeric records are in
[benchmark-evidence.json](benchmark-evidence.json). The implementation remains
unreleased, on `codex/dataset-scale-estimation`.

## Reference Workload And Conditions

- One independent table, 750,000 complete distinct rows, 25 columns: synthetic
  integer primary key plus six each of integer, float, boolean and string.
  Seed 42, CSV, valid mode, normal mandatory privacy/schema checks enabled.
- macOS 26.6.2 arm64, 14 logical CPUs, 36 GiB RAM, Python 3.13.14. Exact
  dependency versions are recorded in the numeric artifact. No source files,
  databases or external providers were used.
- Baseline `0014efa4b652c26573447734330f405918d6e13b` in a separate checkout,
  with explicit benchmark-only generation count/time allowances. Three fresh
  Python processes per configuration, warm OS caches, default local temporary
  filesystem. Jobs execute serially; the host is not exclusively reserved and
  ordinary OS/development activity is not isolated. Accuracy and baseline-small
  runs did not overlap test jobs; the full-suite gate ran afterward. No cache
  dropping. Scalable
  batches: 2,000; policy: 1M total rows, 25M cells, 1 GiB memory, 512 MiB
  output/temp, 600 seconds. Forecast cache disabled in accuracy checks.
- These runs were captured during implementation. They do not assert exact
  release-SHA acceptance. A release must repeat its normal final artifact gates.
  The reported user 20-minute run was not reproduced on this host.

## Repeated End-To-End Measurements

Seconds are median (minimum–maximum), three repetitions per cell.

| Rows × 25 columns | Baseline legacy | Scalable 1 worker | 2 workers | 4 workers |
| --- | ---: | ---: | ---: | ---: |
| 10,000 | 1.830 (1.822–1.836) | 0.709 (0.706–0.712) | 0.735 (0.734–0.744) | 0.611 (0.607–0.615) |
| 100,000 | 18.074 (18.050–18.130) | 6.909 (6.804–6.967) | 4.495 (4.480–4.559) | 2.781 (2.763–2.811) |
| 750,000 | 138.161 (137.972–138.737) | 50.490 (50.041–51.084) | 31.514 (31.443–31.807) | 18.557 (18.469–18.612) |

The 750k four-worker speedup is **7.45×**, above the 2× target; one worker is
2.74× faster. The unchanged legacy stream also benefits from scoped metadata
work removal: 10k median 0.904 seconds, versus 1.830 baseline (no small-run
regression). Existing seeded fixtures remain unchanged.

CSV data bytes are exactly 2,269,394 / 22,699,041 / 170,244,749 for the three
scalable row counts, identical across workers and batch partitions. Statistics
timestamps and manifests are separate, nondeterministic control artifacts.
The largest final benchmark bundle is about 170.26 MB; one staging bundle is
the observed temporary-disk high-water mark in this no-existing-output case.
Replacement of an existing bundle needs additional space for that existing
bundle; this benchmark does not measure that case.

At 750k the baseline process RSS high-water mark is at most 1,632.83 MiB.
Scalable conservative process-tree RSS upper bounds are 147.77 / 222.73 /
373.56 MiB for 1/2/4 workers, under the 1 GiB policy. These are sums of
per-process high-water RSS, **not sampled simultaneous peaks or OS-enforced
memory guarantees**. They include idle process overhead. The raw artifact also
records generation/validation task CPU, parent waiting/writing and bundle bytes.

A cProfile-only 10k baseline took 7.08 seconds with about 49.6M calls (profiler
overhead; excluded from timing comparisons). Repeated privacy policy lookup and
Pydantic distribution parsing were measured hotspots. Their metadata is now
resolved once per validation invocation; every actual cell is still checked.

## Forecast Accuracy And Revalidation

Twelve supported cases: 10k and 100k rows, each with CSV/JSON/Snappy Parquet,
using both the simple 25-column fixture and a typed fixture with exact decimal,
date/datetime, nullable fields, long strings and fictional Unicode/escaped
categories. Each forecast used a fresh bounded 2,000-row synthetic calibration
on the same host and four-worker policy.

- All actual sizes and times lie within their predicted ranges.
- Maximum file-size expected relative error: **0.69%**; threshold 25% for
  CSV/JSON and 40% for Parquet. Maximum duration expected relative error:
  **22.01%**, below 40%. Range ratios are 2.0 for bytes and 2.31 for time,
  below the 3× low-confidence cutoff.
- Cold Parquet import was initially extrapolated per row. The failing numeric
  run led to a fix separating fixed format setup from scalable writing. The
  successful records use that fix; no precision claim is made for arbitrary
  storage/CPU contention or unrelated specs.
- Full separate streamed revalidation of 750k × 25 took **20.31 seconds**.
  It checked counts, exact key ranges/order, mandatory privacy/schema and
  manifest hashes without borrowing the source/profiling cell allowance.

Six additional default legacy-engine cases at 10k rows cover both fixtures and
all three formats. All passed; maximum size error 2.28%, duration error 13.81%.
Fixed Parquet import/setup remains a one-time cost in this route too. A focused
load-test case checks effective row counts when a multiplier exceeds the
calibration sample size. Numeric legacy accuracy records are included separately.

Logical database payload and PostgreSQL heap/page formulas have independently
derived unit cases. No PostgreSQL server was contacted; physical estimates
remain low-confidence assumptions, with wide/TOAST or out-of-int64 values
unknown. Indexes, WAL, replicas, backups and auxiliary storage are excluded.

## Safety, Compatibility And Scope

Focused tests cover cross-worker CSV/JSON byte identity and Parquet logical
identity, disjoint multi-table key domains, stale policy fingerprints, real SDK
stdio approval/recovery (fictional test approval only), worker error, deadline,
cancellation, disk failure, no partial publication and child cleanup. Revalidation
also rejects duplicate keys, unsafe content and untracked files even when data
hashes are recomputed. Cache tests confirm only numbers are reused, never
cached free-form strings. Legacy contract output is preserved.

`scalable-v1` rejects linked tables, global/native/business rules, scenarios and
negative/mixed/load-test modes before output creation. A bounded linked-table
case verifies rejection and the still-working legacy route. Relational parallel
speedup, OS hard-RSS limits and live database/provider acceptance are not claimed.

The additive `public-contract-overlay.patch` keeps historical transformation
activation patches reversible against the new CLI/MCP contract fixtures.
It adds no transformation authority and does not edit historical gate patches.
The serial route carries the parent's end-to-end/invocation budget through
row generation inside each batch; a controlled-clock regression checks that
it cannot restart the allowance per batch. Parallel waiting retains the
parent's deadline and terminates workers on expiry.
Real SDK 1.28.1 compatibility also passed eight focused stdio/roundtrip/budget
tests in an isolated environment; the locked SDK 2 environment passed the normal
workflow tests. Neither run is manual human acceptance.

## Reproduce Offline

Final local `scripts/check_release.sh` passed: **4,867 passed, 23 skipped,
91.88% coverage**, plus lint/types/compile, dependency and operational budgets,
schema freshness and quickstart. Strict OpenSpec/MkDocs checks passed. Live
database/provider and independent release-artifact acceptance remain outside
this implementation evidence.

Use the locked development/all extras on the same machine; run larger jobs
explicitly, outside ordinary unit tests:

```bash
python benchmarks/run_dataset_scale.py --result scalable.json
python benchmarks/run_dataset_scale.py --baseline-root /path/to/baseline --result baseline.json
python benchmarks/run_dataset_scale.py --counts 10000 --legacy --result legacy-small.json
python benchmarks/check_dataset_capacity.py --count 100000 --result accuracy.json --large-validation
python benchmarks/check_dataset_capacity.py --legacy --result legacy-accuracy.json
```

Scripts use fictional specifications, bounded subprocesses and private temporary
output, save numeric evidence only, and remove generated rows afterward.
