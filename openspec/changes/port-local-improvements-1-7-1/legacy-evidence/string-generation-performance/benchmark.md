# Paired Public CSV Benchmark: String Generation

Protocol recorded on 2026-11-24 before the public measurements. All 32 measured
runs and four smoke runs succeeded. **Reject the runtime candidate:** the public
benefit is too small and inconsistent to justify the compatibility code. This
compares the shared `synthetic_string` helper's previous generator expression
with a compatible list comprehension. The preceding distribution-dispatch
change remains in both arms and in the final selected runtime.

## Profile And Measured Candidate

The bounded diagnostic in [string-profile-results.json](string-profile-results.json)
uses the existing fictional 10,000-row, 25-field specification. Its baseline
`cProfile` record contains 7,185,255 calls and 1.217313 seconds of instrumented
time. Selected cumulative times are 1.011091 seconds in `generate_field_value`
(250,000 calls), 0.406965 in `synthetic_string` (40,000 calls), 0.136390 in
`ranged_datetime`, and 0.114645 in `weighted_choice`. The string generator
expression has 0.066640 seconds of self time and 440,729 calls. Instrumented
times are diagnostic, not public API timings, and are not additive.

The measured candidate collects characters with a list comprehension before the
existing `str.join`. Preserve each `rng.choice(string.ascii_lowercase)` call,
including dynamic method/alphabet lookups, character order, length selection
and synthetic prefix. Do not replace random choices with bulk sampling or bind
their method/alphabet across characters. Row-metadata hoisting is outside scope:
callbacks can mutate entity or identifier-domain metadata between fields.

A plain generator-to-list replacement changes PEP 479 behavior if a custom RNG
raises `StopIteration`. The measured implementation constructs the character
range outside an exception guard, joins the list inside it, translates only
`StopIteration` to the previous `RuntimeError` message/cause, and concatenates
the prefix afterwards. This releases the temporary character list before final
concatenation and preserves exceptions from length/range setup and prefix
concatenation. No rows, values or privacy decisions are cached.

Nine alternating bounded pairs at seed 42 measured private candidate generation:
median before **0.351910 s**, after **0.345532 s**, median paired time change
**−1.907%**, with less time in all nine pairs. All eighteen datasets have identical
content/hash. Fifteen mode/seed combinations preserve rows and Random/Faker
states. Boundary and custom-RNG checks preserve dynamic lookups, exceptions,
cause/context and state after partial character generation. The diagnostic
supports a modest candidate; it does not establish a public-export speedup.

Only `synthetic_string` changes between the measured runtime arms. The reversible patch is retained
in [string-generation.patch](string-generation.patch); implementation and
regression evidence are recorded separately from public timing results.

## Workload And Paired Order

Use the unchanged fictional specification from `benchmark_parallel_generation`:
one entity, 25 fields, seed 42, at 100,000 and 750,000 rows. Ordinary public CSV
generation remains serial. Streaming uses four processes and fixed 4,096-row
logical tiles with its existing `tiled-v1` seed namespace. Compare exact bytes
within each engine across versions/repeats; legacy and tiled outputs intentionally
have separate seeded values.

Four adjacent before/after pairs per size/path give **32 measured runs**. Four
additional four-row smoke runs, one per arm/path combination, exercise the same
measurement and audit before the main schedule and are excluded from performance
summaries. Complete the schedule first at 100,000 rows, then at 750,000 rows.
Version and path order alternate:

| Pair | Path order | Version order within each path |
| --- | --- | --- |
| 1 | Ordinary, streaming | Before, after |
| 2 | Streaming, ordinary | After, before |
| 3 | Ordinary, streaming | Before, after |
| 4 | Streaming, ordinary | After, before |

Keep every observation, including regressions. Run cases serially without
concurrent tests or heavy verification. Both arms use the same interpreter,
dependencies, limits, instrumentation and complete checks. The
[generation benchmark driver](../../../scripts/benchmark_generation_dispatch.py)
accepts an explicit reference artifact while retaining its original default;
it reuses the unchanged [paired helper](../../../scripts/benchmark_paired_csv.py)
for fresh-process measurement, scheduling and paired summaries. No benchmark
function replaces generation, validation, encoding or publication behavior.

## Source Isolation And Historical Binding

Freeze the complete pre-change package and the two original public/parallel
benchmark helpers before runtime edits. Bind all 126 source/helper fingerprints
to the `after` arm of the preceding
[dispatch experiment](../generation-dispatch-performance/paired-results.json).
Record that artifact's SHA256 and verify identical dependency versions. Historical
timing observations do not enter the new paired statistics.

Copy the frozen input and candidate into separate private temporary source roots,
excluding bytecode caches. Their maps must have the same keys and differ only at
`src/test_data_agent/generation/entity_generator.py`. AST comparison further
confines the change to `synthetic_string`. The original public and parallel
benchmark helpers remain byte-identical. Fingerprint each selected snapshot
before every measurement and both snapshots again at the end.

Each fresh measurement helper uses its snapshot as working directory and
`PYTHONPATH`. It verifies package/relevant module origins within that root and
the shared streaming CSV neutralizer. The unchanged measured worker inherits
this environment; spawned tile workers inherit the coordinator's search path.
Origin assertions happen in the helper, rather than being additional assertions
inside every measured worker. `PYTHONHASHSEED=0` and
`PYTHONDONTWRITEBYTECODE=1` apply equally. Record origins, writer hash, full source
maps and driver hashes. Recheck the supplied input and historical reference
after the run. The driver leaves its read-only input intact; the task owner
removes that owned input separately after audit and replay verification.

## Checks And Resource Budgets

Reuse `benchmark_public_csv.py`'s `measure`, `worker`, `instrument` and `audit`
unchanged. Keep the 750,000-row limit, 4 GiB output limit, 600-second generation
budget, 660-second external worker deadline and 18,750,000 streaming-cell limit.
Every original budget check delegates to the real implementation.

The worker retains mandatory privacy/schema/relationship/constraint checks and
all four validation-report sections. Combined validation, each concrete validator
and normalization must cover every requested row once per ordinary entity or
streaming tile: one batch, or 25/184 tiles at 100k/750k. Duplicate mandatory/report
entry points remain unused. Synthetic/no-source-copy markers and exact counts
must hold. Exclusive stage sums must equal measured API time.

After subprocess exit, the independent parent parses the CSV for its exact header,
25 cells per row, count and ordered unique key range. It verifies complete reports,
manifest engine/count/flags, exact artifact set and every declared artifact hash.
CSV bytes and SHA256 must match every corresponding prior reference within the
same engine and size. The audit is outside the measured process/API time; it
does not repeat per-cell privacy classification. Real runtime privacy validation
and retained regressions enforce that boundary.

Atomic writers remain unchanged. Require 0700 output directories, 0600 files,
no partial staging and removal of every generated bundle scratch directory. Both
benchmark-owned source copies must remain unchanged and be removed. The supplied
pre-change input remains read-only during the experiment. Successful exports
alone do not prove failure paths; existing privacy, budget, atomicity and
failure-injection regressions provide that evidence.

## Time And Peak Memory

API time includes generation, solving/validation, CSV conversion/writes, control
artifacts, hashing and atomic publication. Imports, process startup and the later
parent audit are outside API timing. Stages are exclusive coordinator wall time:
setup/bookkeeping, generation/IPC, combined runner residual, privacy, schema,
relationships, constraints, normalization, streaming global checks, CSV encoding,
CSV/control-file writes, artifacts/hashing and publication. Encoding includes
UTF-8 conversion in both paths.

Streaming generation/IPC measures coordinator work and exposed waiting while
workers run concurrently. It is not summed worker CPU time; producer improvements
can overlap coordinator validation/writing. Report API, all stages and individual
pairs rather than treating exposed generation time as total worker computation.
Medians of stages need not sum to the median API duration.

Report arm medians/ranges and medians of paired after-minus-before differences
and percentage changes. Negative time change means less time. Median paired
ratios need not equal changes between separate arm medians. Inspect both AB
and BA subsets, retaining every counterexample.

Peak tree RSS is the unchanged concurrent coordinator-plus-descendant `ps` sum,
sampled at nominal 100 ms plus sampling overhead during startup/export and
excluding the parent audit/helper. Brief peaks can be missed and shared pages
counted repeatedly. Coordinator `ru_maxrss` is a separate process high-water
mark. Report maxima and paired changes for both metrics; never add their values
or sum independent process high-water marks. RSS is not exact physical memory
or a hard RSS limit. Preserve observed increases without attributing their cause
to sampling or the code change without evidence.

## Predeclared Decision Rule

Retain the change only with equivalent values/states/errors and repeated local
generation gains without a consistent material API-time or high-water-memory
regression. Preserve every RSS increase and counterexample. The driver's retained
rule also requires equivalent values/states and repeatable generation gains,
with no consistent material API-time or peak-memory regression, and identifies
streaming generation/IPC as exposed coordinator time.

Apply the rule after all 32 measured runs and safety checks complete. The bounded
diagnostic motivates the candidate; public paired evidence must support the
decision. Four pairs per case and sampled RSS provide bounded local evidence,
not confidence intervals, a general speed/memory guarantee or a claim about
every source adapter, machine or workload.

## Public Paired Results

All 32 measured runs and four smoke runs succeeded. Times are seconds. Each arm
has four observations per case. The first table contains independent arm medians;
paired percentages below need not equal changes between those medians. Streaming
generation/IPC remains exposed coordinator work and waiting, not summed worker CPU.

| Rows | Path | API median before → after | Generation/IPC median before → after | CSV median before → after |
| --- | --- | --- | --- | --- |
| 100,000 | Ordinary | 5.700847 → 5.726442 | 3.639840 → 3.657807 | 0.448609 → 0.454197 |
| 100,000 | Streaming, 4 workers | 2.747308 → 2.726564 | 0.537313 → 0.525573 | 0.454332 → 0.447083 |
| 750,000 | Ordinary | 44.404845 → 44.231498 | 28.292355 → 28.144816 | 3.519306 → 3.514645 |
| 750,000 | Streaming, 4 workers | 17.490057 → 17.431969 | 0.660623 → 0.644368 | 3.359031 → 3.328295 |

Negative percentages mean less time. Wins count pairs where after took less time.

| Rows | Path | Paired API change / wins | Paired generation/IPC change / wins | Paired CSV change / wins |
| --- | --- | ---: | ---: | ---: |
| 100,000 | Ordinary | -0.161% / 2/4 | -0.415% / 2/4 | +1.309% / 0/4 |
| 100,000 | Streaming, 4 workers | -0.213% / 3/4 | -0.200% / 2/4 | -1.467% / 2/4 |
| 750,000 | Ordinary | -0.935% / 4/4 | -0.923% / 3/4 | +0.104% / 2/4 |
| 750,000 | Streaming, 4 workers | -0.353% / 3/4 | -4.367% / 3/4 | -0.885% / 3/4 |

Generation/IPC wins **10/16 pairs**, total API time **12/16**. All four paired
case medians are negative, but individual results are mixed. At 100k ordinary,
generation and API are slower in pairs 2 and 3; its separate arm API median rises
although the median paired ratio falls. At 100k streaming both AB generation pairs
are slower (+8.730% and +0.034%), while both BA pairs are faster. Do not describe
the public effect as uniform across orders. At 750k ordinary all API pairs improve,
but generation is 0.700% slower in pair 2. The final 750k streaming BA pair has
0.989% more API time and 1.849% more generation/IPC time. Every counterexample
remains in the record. Changes in unchanged stages are observations, not separate
validator/encoder improvements or proof that the helper caused every API movement.

Observed minimum–maximum ranges preserve every run:

| Rows | Path | Metric | Before range | After range |
| --- | --- | --- | --- | --- |
| 100,000 | Ordinary | API | 5.626098–5.788735 | 5.603717–5.740360 |
| 100,000 | Ordinary | Generation/IPC | 3.583196–3.729151 | 3.548799–3.663328 |
| 100,000 | Ordinary | CSV encoding | 0.443403–0.452203 | 0.449284–0.459824 |
| 100,000 | Streaming, 4 workers | API | 2.720794–2.751892 | 2.709916–2.768265 |
| 100,000 | Streaming, 4 workers | Generation/IPC | 0.524535–0.568056 | 0.512648–0.593574 |
| 100,000 | Streaming, 4 workers | CSV encoding | 0.442256–0.462462 | 0.443260–0.455282 |
| 750,000 | Ordinary | API | 43.374708–44.996654 | 42.675487–44.347026 |
| 750,000 | Ordinary | Generation/IPC | 27.673594–28.817388 | 27.230679–28.402166 |
| 750,000 | Ordinary | CSV encoding | 3.401917–3.548460 | 3.419866–3.537248 |
| 750,000 | Streaming, 4 workers | API | 17.345787–17.575352 | 17.284349–17.702337 |
| 750,000 | Streaming, 4 workers | Generation/IPC | 0.650944–0.694048 | 0.625770–0.665170 |
| 750,000 | Streaming, 4 workers | CSV encoding | 3.346701–3.428651 | 3.321218–3.391455 |

## Exclusive Stage Medians

Before → after, seconds rounded to six places. `—` denotes an absent stage.
Relationship/constraint validators execute on this fixture without such rules.

| Stage | 100k ordinary | 100k streaming | 750k ordinary | 750k streaming |
| --- | --- | --- | --- | --- |
| Setup and bookkeeping | 0.013934 → 0.014211 | 0.009720 → 0.009765 | 0.113525 → 0.114365 | 0.011239 → 0.010122 |
| Generation / IPC | 3.639840 → 3.657807 | 0.537313 → 0.525573 | 28.292355 → 28.144816 | 0.660623 → 0.644368 |
| Combined runner residual | 0.000291 → 0.000292 | 0.006006 → 0.006024 | 0.000298 → 0.000296 | 0.044837 → 0.044915 |
| Privacy validation | 1.133774 → 1.132877 | 1.189396 → 1.188948 | 8.925102 → 8.850233 | 9.417683 → 9.399522 |
| Schema validation | 0.317548 → 0.318811 | 0.350611 → 0.351702 | 2.470419 → 2.460281 | 2.714280 → 2.712832 |
| Relationship validation | 0.000004 → 0.000003 | 0.000038 → 0.000038 | 0.000003 → 0.000004 | 0.000274 → 0.000270 |
| Constraint validation | 0.000001 → 0.000001 | 0.000017 → 0.000018 | 0.000001 → 0.000001 | 0.000126 → 0.000128 |
| Normalization | 0.121657 → 0.120920 | 0.131870 → 0.136198 | 0.932205 → 0.932182 | 1.016272 → 1.004799 |
| Streaming global checks | — | 0.013581 → 0.013651 | — | 0.113443 → 0.115193 |
| CSV encoding | 0.448609 → 0.454197 | 0.454332 → 0.447083 | 3.519306 → 3.514645 | 3.359031 → 3.328295 |
| CSV / control-file writes | 0.005420 → 0.005414 | 0.025733 → 0.018097 | 0.026541 → 0.026083 | 0.086105 → 0.092110 |
| Artifacts and hashing | 0.017671 → 0.018421 | 0.018595 → 0.018492 | 0.094501 → 0.089997 | 0.090946 → 0.091663 |
| Atomic publication | 0.000128 → 0.000122 | 0.000138 → 0.000168 | 0.000128 → 0.000127 | 0.000132 → 0.000149 |

## Peak Memory Results

MiB. Each maximum is independent over four observations; paired deltas are
medians of after-minus-before values, percentages are medians of paired ratios.
Coordinator values use `ru_maxrss`.

| Rows | Path | Maximum tree RSS before → after | Maximum coordinator RSS before → after | Paired tree delta, MiB / % | Paired coordinator delta, MiB / % |
| --- | --- | --- | --- | --- | --- |
| 100,000 | Ordinary | 296.031 → 268.359 | 298.875 → 299.000 | -4.391 / -1.622% | +0.062 / +0.021% |
| 100,000 | Streaming, 4 workers | 560.391 → 582.609 | 143.812 → 141.047 | +20.516 / +3.779% | +11.102 / +8.549% |
| 750,000 | Ordinary | 1919.188 → 1922.609 | 1921.859 → 1925.328 | +2.711 / +0.141% | +3.711 / +0.193% |
| 750,000 | Streaming, 4 workers | 784.469 → 779.344 | 232.297 → 230.812 | -2.398 / -0.305% | -2.648 / -1.143% |

At 100k streaming sampled tree RSS increases in **all four pairs**: its independent
maximum rises **22.219 MiB**, median paired growth **3.779%**. Its coordinator maximum
decreases by 2.766 MiB, while its median paired coordinator change is **+8.549%**.
Independent maxima and paired ratios describe different observations; preserve
both. At 750k ordinary coordinator high-water increases in **all four pairs**:
the maximum grows **3.469 MiB (0.180%)**, paired median **+0.193%**. Other memory
metrics have mixed signs. No memory saving or equal physical memory is established.
Sampling, process overlap and allocation schedules can affect observations, but
the experiment does not prove their cause. Row/buffer retention is unchanged.

## Individual Pairs

AB means before then after; BA means after then before. Deltas are after minus
before. Memory deltas are MiB; generation means the measured generation/IPC stage.

| Rows | Path | Pair / order | API change | Generation/IPC change | CSV change | Tree RSS delta | Coordinator RSS delta |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| 100,000 | Ordinary | 1 / AB | -0.398% | -0.960% | +1.326% | -28.094 | -0.906 |
| 100,000 | Ordinary | 2 / BA | +0.075% | +0.130% | +0.721% | -2.500 | +1.031 |
| 100,000 | Ordinary | 3 / AB | +0.921% | +0.912% | +1.292% | +1.078 | +2.188 |
| 100,000 | Ordinary | 4 / BA | -0.930% | -1.816% | +2.167% | -6.281 | -2.500 |
| 100,000 | Streaming, 4 workers | 1 / AB | +0.642% | +8.730% | +0.227% | +2.859 | +11.000 |
| 100,000 | Streaming, 4 workers | 2 / BA | -0.114% | -0.435% | -3.431% | +4.375 | -4.625 |
| 100,000 | Streaming, 4 workers | 3 / AB | -0.313% | +0.034% | +1.971% | +37.328 | +11.203 |
| 100,000 | Streaming, 4 workers | 4 / BA | -1.525% | -9.754% | -3.161% | +36.656 | +14.281 |
| 750,000 | Ordinary | 1 / AB | -1.612% | -1.601% | +0.528% | +2.688 | +2.688 |
| 750,000 | Ordinary | 2 / BA | -0.011% | +0.700% | -0.951% | -1.703 | +4.734 |
| 750,000 | Ordinary | 3 / AB | -0.259% | -0.245% | -0.319% | +2.734 | +5.859 |
| 750,000 | Ordinary | 4 / BA | -1.948% | -2.909% | +0.696% | +8.094 | +0.812 |
| 750,000 | Streaming, 4 workers | 1 / AB | -0.354% | -5.899% | -2.799% | +0.328 | -6.156 |
| 750,000 | Streaming, 4 workers | 2 / BA | -0.575% | -3.867% | -0.681% | +12.219 | +3.375 |
| 750,000 | Streaming, 4 workers | 3 / AB | -0.352% | -4.867% | -1.088% | -5.125 | -0.047 |
| 750,000 | Streaming, 4 workers | 4 / BA | +0.989% | +1.849% | +0.927% | -8.516 | -5.250 |

## Safety, Determinism And Source Results

All measured and smoke runs passed the original checks: validator/normalizer row
and call counts, full reports, synthetic/no-source-copy markers, exact header/count/
ordered unique keys, manifest flags/engine/artifact set, every output hash,
0700/0600 permissions, no partial staging and scratch removal. Exclusive stages
sum to API time. Raw privacy remains before export; no row or verdict is cached.

All eight observations per case have identical CSV bytes and match all
corresponding preceding dispatch references. Seed namespaces remain distinct.

| Rows | Path | CSV bytes | SHA256 |
| --- | --- | ---: | --- |
| 100,000 | Ordinary | 28,177,934 | `24e6f6833a83cebc9b17e52bc7b7c07449527741348be3221e64553d1b3ab462` |
| 100,000 | Streaming, 4 workers | 28,175,783 | `76330b20f138af1c8b49d42fe8780057cd0b735895a98b0d98713cf715ab9979` |
| 750,000 | Ordinary | 211,322,612 | `5b3a754438204d3fb5dce71e814a8cbac6c4cd749b0db5b55576394dce1923dc` |
| 750,000 | Streaming, 4 workers | 211,321,616 | `735b3374822b27e5afccaa73ebde1773ae43b7e93a1f9f06c43c8535f22a4405` |

The before map exactly matches all **126** source/helper hashes of the preceding
dispatch experiment after arm. Only `generation/entity_generator.py` differs;
AST comparison confines runtime changes to `synthetic_string`. The original
worker, public/parallel helpers, tiled generator, CSV helper, validators and atomic
writers remain unchanged. The reused generation driver adds an explicit reference
option/path handling while retaining its prior default; its separate hash follows.

Fresh helpers verify their origins/writer hash; unchanged workers inherit the
selected environment. Source copies remain unchanged and are removed; all bundle
scratch is removed. The frozen input/reference remain unchanged during measurement.
The driver preserves its supplied input; final owned-input cleanup and reverse-
patch replay proof are recorded in [validation.md](validation.md). The input
and its pointer were removed after their fingerprints and replay were verified;
the raw measurement-time flags remain unchanged.

## Environment And Evidence Digests

Python 3.11.2, macOS 26.6.2 arm64, 14 logical CPUs; package metadata 1.5.0,
Faker 40.35.0, Pydantic 2.13.4 and PyYAML 6.0.3. Both arms use the same absolute
`.venv/bin/python`, protocol limits, workers, seed/hash seed, no-bytecode policy
and timing/RSS method. Only fictional data; no live adapter or production rows.

| Evidence | SHA256 |
| --- | --- |
| Paired raw results | `e60c24be5cd63dae48e55e8200ec9fe10b5d9152531759f0cb634e176f0afab5` |
| Bounded profile and applied-source evidence | `3d48b3083f6618ddfdf9520f4026f5fc6891ae024e0e01570031f149e5471dcd` |
| Reversible string-generation patch | `b26654622552ebf30de3ce46b6ac92291b9dcff0f18a6cd28153182ed7d99791` |
| Reused generation driver | `5a4dbbab58052a690ece326176571cdd6461aaca83e0b8ec903fb7de41744a99` |
| Unchanged paired CSV helper | `f525002f47cd2ff2466fecbd67e13f8551e4690761be87624e063b8641174044` |
| Unchanged public CSV benchmark | `0d7dd4a458bf37ae1d381447319ac6ff31c453f90e3e2deb151b41879d4ea83e` |
| Unchanged parallel helper | `07b5fd3ac63d84b98f21076328866a97115b0241da99678520170bea011a0204` |
| Unchanged tiled generator | `f0a9ad63a54b037c07f81b3d6cadfc502bb41ded7208018417bca06ffedf6bec` |
| Unchanged CSV writer | `47b9196b219de8b03fafb56b031159e67122a60fc1fcb6c00d8c3b9f17c15bc4` |
| Previous dispatch source/reference artifact | `ee1ccb8a738271d34fe7158af13e2454e6891244c5de12482aa5725fa19a4b1c` |
| Before generator; final selected runtime | `a8b6bea1fa60e16ef079e193c659b67c987e4a23551757547d22d7c2216697a3` |
| After generator; rejected measured candidate | `6be6560fdcce994497b0b05bba276a49fd380f95a00386bf756fece3b6f06a1a` |

## Reproduction

The measured configuration used the candidate checkout and this historical
invocation (the temporary input has since been removed):

```sh
.venv/bin/python scripts/benchmark_generation_dispatch.py \
  --before-source /private/var/folders/kh/0kc0tcyj5z5_lg7s2qdzc3rm0000gn/T/apa-row-generation-before-m0_vzkmy \
  --reference openspec/changes/generation-dispatch-performance/paired-results.json \
  --rows 100000 750000 --pairs 4 \
  --output openspec/changes/string-generation-performance/paired-results.json
```

This historical command is not a direct replay on the final selected checkout:
the runtime was restored to before, and the required input no longer exists.

Run from the repository root with the recorded dependencies and final selected
runtime. The script reconstructs the rejected candidate in a private copy, then
reverse-patches a separate before copy. Both complete 126-file maps must match
the immutable raw evidence before measurement. It never patches the checkout.
The explicit `--reference` selects the preceding dispatch experiment; the
driver's older default remains unchanged. A new output preserves the recorded
raw results. This repeats all 32 measured runs and four smoke runs.

```sh
.venv/bin/python - <<'PY'
from hashlib import sha256
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

root = Path.cwd().resolve()
change = root / "openspec/changes/string-generation-performance"
recorded = json.loads((change / "paired-results.json").read_text())
helpers = ("benchmark_public_csv.py", "benchmark_parallel_generation.py")

def fingerprints(path):
    files = [*sorted((path / "src/test_data_agent").rglob("*.py")),
             *(path / "scripts" / name for name in helpers)]
    return {str(file.relative_to(path)): sha256(file.read_bytes()).hexdigest()
            for file in files}

with tempfile.TemporaryDirectory(prefix="apa-string-replay-") as temporary:
    candidate = Path(temporary) / "candidate"
    before = Path(temporary) / "before"
    shutil.copytree(root / "src/test_data_agent", candidate / "src/test_data_agent",
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    (candidate / "scripts").mkdir()
    for name in (*helpers, "benchmark_generation_dispatch.py", "benchmark_paired_csv.py"):
        shutil.copyfile(root / "scripts" / name, candidate / "scripts" / name)
    assert fingerprints(candidate) == recorded["source_sha256"]["before"]
    patch = change / "string-generation.patch"
    with patch.open("rb") as handle:
        subprocess.run(["patch", "-p1", "-d", str(candidate)], stdin=handle, check=True)
    assert fingerprints(candidate) == recorded["source_sha256"]["after"]
    shutil.copytree(candidate, before)
    with patch.open("rb") as handle:
        subprocess.run(["patch", "-R", "-p1", "-d", str(before)], stdin=handle, check=True)
    assert fingerprints(before) == recorded["source_sha256"]["before"]
    environment = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONHASHSEED": "0",
                   "PYTHONPATH": os.pathsep.join([str(candidate / "src"),
                                                  str(candidate / "scripts")])}
    subprocess.run([
        sys.executable, str(candidate / "scripts/benchmark_generation_dispatch.py"),
        "--before-source", str(before),
        "--reference", str(root / "openspec/changes/generation-dispatch-performance/paired-results.json"),
        "--output", "/private/tmp/apa-string-replay-results.json",
    ], cwd=candidate, env=environment, check=True)
PY
```

Independent replay verification already proved the forward 126-file candidate
map and exact candidate AST, confined the AST change to `synthetic_string`, then
proved the reverse 126-file before map and scratch removal. See
[validation.md](validation.md) for checks and owned-input cleanup.

## Decision

**Reject and revert the runtime candidate.** The bounded generation diagnostic
improves in 9/9 pairs, but public generation/IPC improves in 10/16 pairs and API
time in 12/16. Paired API changes range from −0.161% to −0.935% across cases.
The 100k streaming generation result changes sign with AB/BA order, while its
sampled tree RSS increases in every pair. The 750k ordinary API improves in all
four pairs, which supports a small local effect, but does not establish enough
repeatable public benefit for the exception-compatibility code. This is an
inconclusive benefit, not a proven general slowdown.

The final selected runtime is restored to the complete raw **before** map,
including generator hash `a8b6bea1…`. The raw **after** map, generator hash
`6be6560f…`, describes the measured rejected candidate; it is not a fingerprint
of the final checkout. Preserve the raw measurements, profile and exact patch
unchanged. Retain the benchmark driver's explicit reference option and
equivalence regressions. Checks, privacy, deterministic outputs and atomic
publication remain unchanged across source adapters.

The candidate's full suite passed **3,024 tests, 10 skipped**, with **92.04%**
coverage. After restoration, the selected runtime passed **3,024 tests, 10
skipped**, with **92.03%** coverage; Ruff and mypy also pass. These checks and
replay evidence are detailed in [validation.md](validation.md). No uniform API
speedup or memory improvement is claimed.
