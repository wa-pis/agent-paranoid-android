# Paired Public CSV Benchmark: Generation Dispatch

Protocol recorded on 2026-11-24 before the public measurements. All 32 measured
runs and four smoke runs succeeded. **Keep the shared dispatch change:** the
independent audit confirmed generation/IPC gains in 16/16 pairs and total API
gains in 15/16 pairs. The 100k ordinary sampled-memory increase remains an
explicit tradeoff below. This compares the shared
generator's previous eager distribution selection with selection inside the
existing scalar branches. The earlier CSV encoding guard remains in both arms.

## Profile And Selected Change

The bounded diagnostic in [dispatch-profile-results.json](dispatch-profile-results.json)
uses the existing fictional 10,000-row, 25-field specification. Its baseline
`cProfile` record contains 8,105,255 calls and 1.502792 seconds of instrumented
time. Selected cumulative times are 1.258787 seconds in `generate_field_value`
(250,000 calls), 0.461635 in `synthetic_string`, 0.155200 in `ranged_datetime`,
and 0.128854 in `weighted_choice`. These instrumented times are diagnostic,
not public API timings and not additive.

For each non-categorical scalar, the previous code selected six distribution
types before entering its field-type branch. Most selections cannot affect the
result. Move only the relevant `isinstance` checks into each existing branch;
leave categorical precedence, early returns, scalar operations and random calls
unchanged. No prepared-generator framework, row cache or new dependency is needed.

Nine alternating bounded pairs at seed 42 measured private candidate generation:
median before **0.418917 s**, after **0.376617 s**, median paired time change
**−9.629%**, with less time in all nine pairs. All 18 datasets have identical
content/hash. This diagnostic retains the private generator's existing work;
mandatory generated-row validation remains the public caller's responsibility.
It is not a substitute for the complete public benchmark below.

The measured candidate function's AST equals the applied function's AST.
Independent checks found identical ordinary and tiled results at 500 rows, and
identical rows plus `Random`/Faker states for 100 rows across three seeds and all
five generation modes. The full generator module differs from the frozen source
only at `generate_field_value`. The reversible patch is retained in
[generation-dispatch.patch](generation-dispatch.patch); other regression and
safety evidence belongs to the final validation report.

## Workload And Paired Order

Use the unchanged fictional specification from `benchmark_parallel_generation`:
one entity, 25 fields, seed 42, at 100,000 and 750,000 rows. Ordinary public CSV
generation remains serial. Streaming uses four processes and fixed 4,096-row
logical tiles, with its existing `tiled-v1` seed namespace. Compare exact bytes
within each path across versions and repeats; the legacy and tiled namespaces
intentionally produce different values.

There are four adjacent before/after pairs for each size/path: **32 measured
runs** in total. Four additional four-row smoke runs, one per arm/path, exercise
the unchanged measurement and audit before the main schedule and are excluded
from performance summaries. Run the full schedule first at 100,000 rows, then
at 750,000 rows. Version and path order alternate:

| Pair | Path order | Version order within each path |
| --- | --- | --- |
| 1 | Ordinary, streaming | Before, after |
| 2 | Streaming, ordinary | After, before |
| 3 | Ordinary, streaming | Before, after |
| 4 | Streaming, ordinary | After, before |

Keep every observation, including slow runs. Run cases serially without concurrent
tests or heavy verification. Use the same interpreter, dependencies, limits,
instrumentation and checks for both arms. The
[dispatch driver](../../../scripts/benchmark_generation_dispatch.py) reuses the
previous [paired driver](../../../scripts/benchmark_paired_csv.py) for scheduling,
fresh-process measurement and paired summaries; it does not replace generation,
validation, encoding or publication code.

## Source Isolation And Historical Binding

Freeze the complete pre-change package and the two original public/parallel
benchmark helpers before editing runtime code. The input fingerprint map must
exactly match all 126 source/helper hashes of the `after` arm of the preceding
[paired CSV experiment](../csv-encoding-performance/paired-results.json). Record
that artifact's SHA256 and assert the same dependency versions. Historical timing
observations are not included in the new paired statistics.

Copy that baseline and the current candidate into separate private temporary
source roots, excluding bytecode caches. Their fingerprint maps must have the
same paths and differ only at
`src/test_data_agent/generation/entity_generator.py`. The old CSV and parallel
benchmark helpers remain byte-identical. Fingerprint each selected snapshot
before measurement and verify both again after the schedule.

Every run starts a fresh measurement helper whose working directory and
`PYTHONPATH` select its snapshot. The helper checks the package and relevant
generation/export module origins inside that root, and verifies that streaming
uses the shared CSV neutralizer. The unchanged measured worker inherits this
environment, and spawned tile workers inherit the coordinator's search path.
Origin assertions occur in the helper; they are not additional assertions inside
every measured worker. `PYTHONHASHSEED=0` and `PYTHONDONTWRITEBYTECODE=1` apply to
both arms. Record import origins, writer hash, full source maps and both driver
hashes. Recheck the original frozen input and historical artifact after the run.

## Checks And Resource Budgets

Reuse `benchmark_public_csv.py`'s `measure`, `worker`, `instrument` and `audit`
unchanged. Keep the 750,000-row limit, 4 GiB output limit, 600-second generation
budget, 660-second external worker deadline and 18,750,000 streaming-cell limit.
Every original budget check delegates to the real implementation.

The measured worker retains mandatory privacy/schema/relationship/constraint
checks and all four validation-report sections. Combined validation, every
concrete validator and normalization must cover each row once per ordinary
entity or streaming tile: one batch for ordinary generation, 25 tiles at 100,000
rows and 184 at 750,000 rows. Duplicate mandatory/report entry points remain
unused. Synthetic/no-source-copy markers and exact entity row counts must hold.
Exclusive stage sums must equal total measured API time.

After each measured subprocess exits, the independent parent audit parses the
CSV for its exact header, 25 cells per row, row count and ordered unique key
range. It verifies the complete successful report, manifest engine/count/flags,
exact artifact set and all manifest hashes. CSV SHA256 and byte count must match
the previous reference within the same size/path. This audit is outside the
measured process and API time; it does not repeat per-cell privacy classification.
The real runtime privacy validator and regression tests retain that boundary.

The original atomic writers remain unchanged. Audit output directories as 0700
and files as 0600; require no partial staging and removal of every generated
bundle scratch directory. Both benchmark-owned source copies must remain
unchanged and be removed after use. The separate pre-change input remains
read-only throughout the experiment. Success-only exports do not prove every
failure boundary; the retained privacy, budget, atomicity and failure-injection
tests provide that coverage.

## Time And Peak Memory

API time includes generation, solving/validation, CSV conversion/writes, control
artifacts, hashing and atomic publication. Imports, process startup and the later
parent audit are outside API timing. Stages are exclusive coordinator wall time:
setup/bookkeeping, generation/IPC, combined runner residual, privacy, schema,
relationships, constraints, normalization, streaming global checks, CSV encoding,
CSV/control-file writes, artifacts/hashing and publication. Both CSV encoding
stages include UTF-8 conversion.

Streaming generation/IPC measures coordinator work and exposed waiting while
producer processes run concurrently. It is not summed worker CPU time: faster
generation can be hidden behind coordinator validation and writing. Report the
whole API, each stage and each pair rather than treating that stage as total
worker computation. Medians of stages need not sum to the median API duration.

Record each arm's observed ranges and medians and the median of paired
after-minus-before differences/percentage changes. A negative time change means
less time. The median paired percentage change need not equal the percentage
change between separate arm medians. Inspect AB and BA subsets and preserve every
counterexample.

Peak tree RSS uses the unchanged concurrent coordinator-plus-descendant `ps`
sum at nominal 100 ms plus sampling overhead, including subprocess startup/export
and excluding the parent audit/helper. Brief peaks can be missed; shared pages
may be counted repeatedly. Coordinator `ru_maxrss` is its own separate high-water
mark. Report maxima per arm and paired changes for each metric; never add these
columns or sum separate process high-water marks. RSS is not exact physical
memory or a hard RSS cap.

## Predeclared Decision Rule

> Retain only with equivalent values/states and repeatable generation gains
> without a consistent material API-time or peak-memory regression; streaming
> generation/IPC is exposed coordinator time.

Apply the rule after all measured cases and integrity checks complete. The
bounded diagnostic motivates the candidate; the public paired comparison must
support the final decision. Four pairs per case form a local experiment, not a
statistical confidence interval or a guarantee for all specifications, source
adapters, machines or runs.

## Public Paired Results

Times are seconds. Each arm has four observations per size/path. These are
separate arm medians; percentage changes in the next table are medians of paired
ratios, which need not equal changes between these arm medians. Generation/IPC
is serial generation work in the ordinary path and exposed coordinator time in
the streaming path. All observations remain in the raw
[paired-results.json](paired-results.json).

| Rows | Path | API median before → after | Generation/IPC median before → after | CSV median before → after |
| --- | --- | --- | --- | --- |
| 100,000 | Ordinary | 6.332619 → 5.939268 | 4.192014 → 3.810739 | 0.467051 → 0.463321 |
| 100,000 | Streaming, 4 workers | 2.804333 → 2.794124 | 0.558034 → 0.535281 | 0.455148 → 0.448866 |
| 750,000 | Ordinary | 46.095292 → 43.578235 | 30.595485 → 27.818441 | 3.429734 → 3.468610 |
| 750,000 | Streaming, 4 workers | 17.504686 → 17.349507 | 0.685735 → 0.633346 | 3.409415 → 3.292992 |

Negative percentage changes mean less time. Wins count individual pairs where
the after arm took less time; equality would not count as a win.

| Rows | Path | Paired API change / wins | Paired generation/IPC change / wins | Paired CSV change / wins |
| --- | --- | ---: | ---: | ---: |
| 100,000 | Ordinary | -6.150% / 4/4 | -8.957% / 4/4 | -0.560% / 4/4 |
| 100,000 | Streaming, 4 workers | -0.493% / 4/4 | -3.252% / 4/4 | -1.613% / 2/4 |
| 750,000 | Ordinary | -6.371% / 4/4 | -9.734% / 4/4 | +0.826% / 1/4 |
| 750,000 | Streaming, 4 workers | -1.293% / 3/4 | -8.091% / 4/4 | -3.415% / 4/4 |

Generation/IPC takes less time in **16/16 pairs**, including both AB and BA
orders for every case. Total API time takes less time in **15/16 pairs**.
The exception is the final 750,000-row streaming BA pair: API time is **0.439%
higher** even though generation/IPC is **9.326% lower**. That observation is
retained. Streaming API gains are smaller because producer work overlaps the
coordinator stages. Changes in unchanged validation/CSV stages are observations,
not attributed encoder or validator optimizations.

Observed API ranges, without discarding or replacing any run:

| Rows | Path | Before minimum–maximum | After minimum–maximum |
| --- | --- | --- | --- |
| 100,000 | Ordinary | 6.320313–6.446023 | 5.927400–5.952251 |
| 100,000 | Streaming, 4 workers | 2.796277–2.820914 | 2.778176–2.805080 |
| 750,000 | Ordinary | 45.422834–47.911412 | 42.488726–44.996802 |
| 750,000 | Streaming, 4 workers | 17.049143–18.213300 | 16.957354–17.943202 |

## Exclusive Stage Medians

Before → after, seconds rounded to six decimal places. `—` denotes a stage
absent from ordinary generation. The relationship and constraint validators
still execute on this fixture without relationships or business constraints.

| Stage | 100k ordinary | 100k streaming | 750k ordinary | 750k streaming |
| --- | --- | --- | --- | --- |
| Setup and bookkeeping | 0.015545 → 0.015085 | 0.010802 → 0.011842 | 0.104505 → 0.109039 | 0.010271 → 0.010464 |
| Generation / IPC | 4.192014 → 3.810739 | 0.558034 → 0.535281 | 30.595485 → 27.818441 | 0.685735 → 0.633346 |
| Combined runner residual | 0.000310 → 0.000300 | 0.006356 → 0.006358 | 0.000292 → 0.000295 | 0.043039 → 0.043456 |
| Privacy validation | 1.185139 → 1.177256 | 1.211187 → 1.237558 | 8.558380 → 8.740161 | 9.279586 → 9.343661 |
| Schema validation | 0.327537 → 0.326908 | 0.361942 → 0.361120 | 2.388929 → 2.431278 | 2.754730 → 2.764902 |
| Relationship validation | 0.000004 → 0.000003 | 0.000040 → 0.000041 | 0.000003 → 0.000003 | 0.000230 → 0.000231 |
| Constraint validation | 0.000001 → 0.000001 | 0.000017 → 0.000018 | 0.000001 → 0.000001 | 0.000124 → 0.000125 |
| Normalization | 0.125717 → 0.123770 | 0.132403 → 0.134862 | 0.911787 → 0.927778 | 1.047939 → 1.005900 |
| Streaming global checks | — | 0.014710 → 0.016294 | — | 0.114851 → 0.108568 |
| CSV encoding | 0.467051 → 0.463321 | 0.455148 → 0.448866 | 3.429734 → 3.468610 | 3.409415 → 3.292992 |
| CSV / control-file writes | 0.005362 → 0.005336 | 0.023860 → 0.018398 | 0.023467 → 0.024723 | 0.104080 → 0.094415 |
| Artifacts and hashing | 0.019746 → 0.019590 | 0.020027 → 0.020313 | 0.085219 → 0.088392 | 0.090976 → 0.090204 |
| Atomic publication | 0.000142 → 0.000140 | 0.000135 → 0.000140 | 0.000127 → 0.000139 | 0.000133 → 0.000129 |

## Peak Memory Results

MiB. Each maximum is independent over four observations. Paired deltas are
medians of after-minus-before values; paired percentages are medians of ratios,
not ratios between independent maxima. Coordinator values use `ru_maxrss`.

| Rows | Path | Maximum tree RSS before → after | Maximum coordinator RSS before → after | Paired tree delta, MiB / % | Paired coordinator delta, MiB / % |
| --- | --- | --- | --- | --- | --- |
| 100,000 | Ordinary | 271.719 → 297.719 | 300.281 → 302.141 | +13.492 / +4.980% | +2.820 / +0.942% |
| 100,000 | Streaming, 4 workers | 565.000 → 563.672 | 142.703 → 139.078 | -2.000 / -0.352% | -0.078 / -0.055% |
| 750,000 | Ordinary | 1918.812 → 1925.453 | 1926.000 → 1925.469 | -0.359 / -0.019% | -1.648 / -0.086% |
| 750,000 | Streaming, 4 workers | 772.125 → 780.188 | 229.766 → 229.062 | +2.508 / +0.324% | +2.008 / +0.889% |

The 100,000-row ordinary path has **higher sampled tree peaks in all four
pairs**, with a median paired increase of **4.980%** and maximum-over-runs
increase of **26.000 MiB**. Its coordinator high-water maximum rises by
**1.859 MiB (0.619%)**; its paired coordinator median rises by **0.942%**.
The sampled before maximum is below its own coordinator high-water mark,
illustrating that sampling can miss brief peaks. This does **not** prove that
the entire observed difference is sampling error. Retain this result when
assessing the tradeoff; do not claim unchanged or reduced memory.

The other three cases have lower after-arm coordinator maxima, while tree
maxima and paired changes have mixed signs. Neither RSS metric establishes
a general memory saving. The original buffer/row retention strategy is unchanged,
but execution timing and sampled RSS remain workload- and schedule-dependent.

## Individual Pairs

AB means before then after; BA means after then before. Changes are after
minus before. Memory deltas are MiB. Generation means the measured generation/IPC
stage, including its streaming interpretation above.

| Rows | Path | Pair / order | API change | Generation/IPC change | CSV change | Tree RSS delta | Coordinator RSS delta |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| 100,000 | Ordinary | 1 / AB | -8.038% | -11.537% | -1.661% | +21.781 | -0.625 |
| 100,000 | Ordinary | 2 / BA | -6.083% | -8.889% | -0.392% | +1.438 | +2.500 |
| 100,000 | Ordinary | 3 / AB | -5.956% | -9.005% | -0.587% | +5.203 | +3.516 |
| 100,000 | Ordinary | 4 / BA | -6.217% | -8.910% | -0.534% | +26.344 | +3.141 |
| 100,000 | Streaming, 4 workers | 1 / AB | -0.561% | -3.137% | +0.022% | -14.609 | -0.984 |
| 100,000 | Streaming, 4 workers | 2 / BA | -0.647% | -5.397% | -3.247% | +6.875 | +1.906 |
| 100,000 | Streaming, 4 workers | 3 / AB | -0.303% | -3.116% | +0.107% | +1.719 | +0.828 |
| 100,000 | Streaming, 4 workers | 4 / BA | -0.425% | -3.366% | -4.501% | -5.719 | -8.578 |
| 750,000 | Ordinary | 1 / AB | -7.117% | -10.632% | +1.170% | -2.594 | -5.703 |
| 750,000 | Ordinary | 2 / BA | -3.596% | -7.315% | +3.597% | +8.125 | +5.078 |
| 750,000 | Ordinary | 3 / AB | -6.094% | -9.873% | +0.482% | +1.875 | +1.875 |
| 750,000 | Ordinary | 4 / BA | -6.649% | -9.594% | -0.693% | -3.141 | -5.172 |
| 750,000 | Streaming, 4 workers | 1 / AB | -1.102% | -5.411% | -2.350% | +16.141 | +4.797 |
| 750,000 | Streaming, 4 workers | 2 / BA | -1.483% | -6.856% | -2.247% | -0.875 | +3.516 |
| 750,000 | Streaming, 4 workers | 3 / AB | -1.631% | -9.516% | -4.718% | -9.891 | +0.500 |
| 750,000 | Streaming, 4 workers | 4 / BA | +0.439% | -9.326% | -4.479% | +5.891 | -3.172 |

## Safety, Determinism And Source Results

All 32 measured runs and four smoke runs succeeded. Each measured run retains
every original worker and parent-audit assertion: concrete validator/normalizer
call and row counts, complete reports, synthetic/no-source-copy markers, exact
header/count/ordered unique keys, manifest flags/engine/artifact set, all output
hashes, 0700/0600 permissions, no partial staging and scratch removal. Exclusive
stage sums equal API time. Runtime raw-string privacy remains before export;
no output row or privacy verdict is cached.

Within each size/path, all eight CSV observations are byte-identical across
arms and repeats and match the preceding historical reference. The different
legacy and tiled hashes retain the existing separate seed namespaces.

| Rows | Path | CSV bytes | SHA256 |
| --- | --- | ---: | --- |
| 100,000 | Ordinary | 28,177,934 | `24e6f6833a83cebc9b17e52bc7b7c07449527741348be3221e64553d1b3ab462` |
| 100,000 | Streaming, 4 workers | 28,175,783 | `76330b20f138af1c8b49d42fe8780057cd0b735895a98b0d98713cf715ab9979` |
| 750,000 | Ordinary | 211,322,612 | `5b3a754438204d3fb5dce71e814a8cbac6c4cd749b0db5b55576394dce1923dc` |
| 750,000 | Streaming, 4 workers | 211,321,616 | `735b3374822b27e5afccaa73ebde1773ae43b7e93a1f9f06c43c8535f22a4405` |

The before fingerprint map exactly matches all **126** source/helper hashes
of the preceding paired experiment’s after arm. The candidate differs in exactly
one file, `generation/entity_generator.py`; the original public/parallel benchmark
helpers, tiled generator, CSV helper, validators and atomic writers are unchanged.
Each helper’s selected import origins and writer hash passed; unchanged workers
inherit that selected environment. Both benchmark-owned snapshots remained
unchanged and were removed; every generated bundle scratch directory was removed.
The separate pre-change input and preceding reference remained unchanged during
the run. Final input cleanup and reverse-patch replay evidence are recorded in
the final validation report; the benchmark driver does not delete that input.

## Environment And Evidence Digests

Python 3.11.2, macOS 26.6.2 arm64, 14 logical CPUs; installed package metadata
1.5.0, Faker 40.35.0, Pydantic 2.13.4 and PyYAML 6.0.3. Both arms use
`/Users/agrudin/dev/my/agent-paranoid-android/.venv/bin/python`. Both use the protocol’s identical limits, workers, seed,
hash seed, bytecode-cache policy and timing/RSS methods. Only fictional data
was generated; no live source adapter or production rows were used.

| Evidence | SHA256 |
| --- | --- |
| Paired raw results | `ee1ccb8a738271d34fe7158af13e2454e6891244c5de12482aa5725fa19a4b1c` |
| Bounded dispatch profile and applied-source evidence | `9a3bcb41ac6ed80f4013ed5ba3939563a94b8c984a4d120d4621903edef7d79a` |
| Reversible generation patch | `1b227d271fe5584d3c4bc55367c92dce852c89e53dfdbeaf8fd6f1b0f5657ada` |
| Dispatch paired driver | `7e022c3da60d3cd1d7c292f051c02b3a174310d91c1e58bb6762dc547d856ea5` |
| Reused paired CSV driver | `f525002f47cd2ff2466fecbd67e13f8551e4690761be87624e063b8641174044` |
| Before generator | `0bf42e8b42d9d28649a4c9baee4e664847e10ea5b983fabc53280aa50003ee9e` |
| After generator | `a8b6bea1fa60e16ef079e193c659b67c987e4a23551757547d22d7c2216697a3` |
| Unchanged public CSV benchmark | `0d7dd4a458bf37ae1d381447319ac6ff31c453f90e3e2deb151b41879d4ea83e` |
| Unchanged parallel benchmark helper | `07b5fd3ac63d84b98f21076328866a97115b0241da99678520170bea011a0204` |
| Unchanged tiled generator | `f0a9ad63a54b037c07f81b3d6cadfc502bb41ded7208018417bca06ffedf6bec` |
| Unchanged CSV writer | `47b9196b219de8b03fafb56b031159e67122a60fc1fcb6c00d8c3b9f17c15bc4` |
| Previous paired CSV source/reference artifact | `a49dc561b99be67cae219c06f109b23a2f475432be0ab9dd89bf27bb20f1c95f` |

## Reproduction

Use the recorded candidate source and dependency versions. Reconstruct the
pre-change package in a fresh private temporary directory by reversing the
retained patch; never reverse it in the working checkout. The driver rejects
historical-source drift and source differences beyond the generator module.
The original temporary input path in the raw record is not a permanent artifact.

```sh
.venv/bin/python - <<'PY'
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

root = Path.cwd()
with tempfile.TemporaryDirectory(prefix="apa-generation-replay-") as temporary:
    before = Path(temporary)
    shutil.copytree(
        root / "src/test_data_agent", before / "src/test_data_agent",
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
    )
    (before / "scripts").mkdir()
    for name in ("benchmark_public_csv.py", "benchmark_parallel_generation.py"):
        shutil.copyfile(root / "scripts" / name, before / "scripts" / name)
    patch = root / "openspec/changes/generation-dispatch-performance/generation-dispatch.patch"
    with patch.open("rb") as handle:
        subprocess.run(["patch", "-R", "-p1", "-d", str(before)], stdin=handle, check=True)
    subprocess.run([
        sys.executable, str(root / "scripts/benchmark_generation_dispatch.py"),
        "--before-source", str(before),
        "--output", "/private/tmp/apa-generation-replay-results.json",
    ], cwd=root, check=True)
PY
```

The output filename deliberately preserves the measured raw artifact. Existing
runtime checks and external process deadlines remain active on replay. Successful
private cleanup and unchanged source fingerprints are prerequisites for completion.

## Decision

**Keep the shared distribution-dispatch change.** The independent audit verified
all raw calculations and checks. Generation/IPC wins 16/16 adjacent pairs and
improves in both order subsets for every case; paired median changes are
−8.957%, −3.252%, −9.734% and −8.091%. Total API time wins 15/16 pairs, and
both order subsets improve for every case. Equivalent values/states, exact CSV
bytes, full privacy/validation, source integrity and private cleanup satisfy the
predeclared safety conditions.

Accept the observed 100k ordinary sampled-RSS increase as an explicit tradeoff:
its sampled maximum rises 26 MiB, while the coordinator high-water maximum rises
1.859 MiB (0.619%) and the other three cases have lower coordinator maxima.
The measurements do not establish equal physical memory or a memory saving.
The last large streaming API regression remains in the evidence; streaming
generation overlaps coordinator work, so its total gain remains modest.

Keep the original random calls, seed namespaces, validation and atomic writers.
No new backend, dependency, cache or generator framework is needed for this
result. Four local pairs per case do not establish a statistical confidence
interval, guaranteed API speedup or performance on every workload/source adapter.
