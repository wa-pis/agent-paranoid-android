# Verification: String Generation Experiment

Evaluated on 2026-11-24, unreleased. **Reject and revert the runtime candidate.**
Keep the previous generator, the regression tests, the benchmark driver's explicit
reference option and all evidence. [benchmark.md](benchmark.md) records every
stage, pair and memory observation; [paired-results.json](paired-results.json)
contains metadata and hashes, not generated rows.

## Scope And Compatibility

Only `synthetic_string` differed in the measured runtime candidate; a module AST
comparison excludes other changes. Its list comprehension preserves each dynamic
`rng.choice(string.ascii_lowercase)` lookup, draw order, length and synthetic
prefix. An exception guard preserves the generator expression's PEP 479 behavior
when custom character selection raises `StopIteration`. Length/range setup and
prefix concatenation remain outside that guard. These compatibility lines are
part of the cost considered in rejecting the optimization.

The final selected source matches all 126 fingerprints in the raw **before** map,
including the previous distribution-dispatch improvement. The raw **after** map
describes the measured, rejected candidate; it must not match the final checkout.
Keep the exact [runtime patch](string-generation.patch) for reproducibility.
Historical benchmark artifacts are unchanged.

No seed namespace, source-row access, SQL policy, cache, dependency, public API,
privacy classifier, validator, work/output budget or atomic writer changes.
Generation and policy remain shared across source-derived specifications.
The reusable driver adds only `--reference`, retaining its previous default;
relative and absolute references have focused regression coverage. Original
measurement, worker, instrumentation, memory sampler and output-audit helpers
remain byte-identical.

## Executable Equivalence Evidence

The 75 tests in `tests/test_string_generation_equivalence.py` pass against both
the frozen previous source and measured candidate. They compare an independent
previous string helper over exact values/types, length and prefix boundaries,
raw/prepared metadata, nullability, invalid bounds, Random state, dynamic method
and alphabet lookup, exception type/message/cause/context and partial-draw state.
All five generation modes compare ordinary and tile head/tail CSV output and
Random/Faker state. Further cases cover metadata mutation between calls and ten
source variants without adding source reads.

The combined string, distribution-dispatch and driver regression run passes
**147 tests**. The bounded diagnostic preserves all eighteen generated datasets,
fifteen mode/seed combinations, forty boundary cases and custom-RNG exception
checks; its metadata is retained in
[string-profile-results.json](string-profile-results.json).
Existing suites retain privacy failures, relationships/rules, source policy,
worker-count determinism, budgets, formula encoding, cleanup and atomic
destination protection.

## Public Benchmark And Rejection

All **32 measured runs plus four smoke runs pass**. The unchanged real worker
and audit retain full reports, privacy/schema/relationship/constraint checks,
row coverage, exact headers/counts/ordered unique keys, manifests and artifact
hashes. Validation/normalization covers every row once per ordinary entity or
streaming tile (25/184 tiles at 100k/750k). Synthetic/no-source-reuse flags,
0700 directories, 0600 files, staging absence and bundle cleanup pass. Every CSV
matches all corresponding historical reference runs within its engine; ordinary
and tiled engines retain their distinct seed namespaces.

The independent audit recomputes all summaries, ranges, paired differences,
stage sums and call/count checks. Both 126-file maps are verified, only the
generator differs, and dependency versions/reference/helper hashes match.
Fresh measurement helpers verify package/module origins; measured coordinators
inherit the chosen snapshot environment and spawned workers its search path.
This does not claim an additional origin assertion inside every worker.
Benchmark-owned source snapshots and output scratch are removed; the supplied
baseline is verified read-only before owner cleanup.

An independent replay applies the retained patch to a private selected-source
copy and reproduces all 126 candidate fingerprints. Its AST differs only in
`synthetic_string` and matches the measured diagnostic candidate. Reversing the
patch reproduces all 126 previous fingerprints. Replay scratch is removed.
After this audit the task owner rechecks the supplied baseline against both the
raw before map and selected checkout, removes that owned input and its pointer,
and verifies their absence. Raw driver flags describe cleanup at measurement
time; this later owner cleanup does not alter the raw artifact.

The bounded diagnostic improves in 9/9 pairs (median paired −1.907%). Public
generation/IPC improves in **10/16 pairs**, total API time in **12/16**.
Median paired API changes are −0.161%, −0.213%, −0.935% and −0.353% for 100k
ordinary/streaming and 750k ordinary/streaming. The 750k ordinary API improves in
all four pairs, but the 100k ordinary separate-arm medians worsen. Small streaming
generation changes sign with AB/BA order. These results support at most a modest
local effect, insufficiently repeatable to justify extra compatibility code.
The rejection does not establish a performance regression.

Memory also provides no reason to retain it: every 100k streaming sampled tree
peak rises, with maxima **560.391 → 582.609 MiB**; paired coordinator high-water
change has median **+8.549%** although its independent maximum decreases.
At 750k ordinary, all four coordinator peaks rise slightly; the maximum increases
**1,921.859 → 1,925.328 MiB** (+3.469 MiB). Preserve both metrics and every
counterexample; the experiment does not prove the cause of these variations.
Tree RSS is a nominal 100 ms sample of summed processes, counting shared pages
repeatedly and possibly missing short peaks. Coordinator high-water RSS excludes
worker peaks. Streaming generation/IPC is exposed coordinator work/waiting, not
summed worker CPU. Four local pairs provide neither a confidence interval nor a
general speed or memory guarantee.

## Regression Gates

The measured candidate's full suite passes **3,024 tests**, with **10 skipped**,
in **82.52 s**. Statement coverage is **92.0365%** (12,401 / 13,474), exceeding
the 85% gate.

The final selected runtime also passes **3,024 tests**, with **10 skipped**, in
**75.95 s**. Coverage is **92.0336%** (12,396 / 13,469); the generator is
**96.30%** (182 / 189). Ruff across `src tests scripts` and mypy across all
124 source files pass. Strict OpenSpec validation and strict MkDocs build pass;
the final documentation tests pass **49 tests** in **0.53 s**.
`git diff --check` passes. Independent raw and replay audits find no
correctness, provenance or cleanup issue; their performance recommendation is
to reject the candidate.

```text
.venv/bin/python -m pytest -q --cov=test_data_agent --cov-report=json:/private/tmp/apa-string-generation-final-coverage.json --cov-fail-under=85
.venv/bin/ruff check src tests scripts
.venv/bin/mypy src
openspec validate string-generation-performance --strict
.venv/bin/mkdocs build --strict
.venv/bin/python -m pytest -q tests/test_documentation.py
git diff --check
```

Only fictional fixtures were used. Live database integrations and external
providers were not exercised; ten environment-gated tests remain skipped.
No commit, version, release or publication was selected.

## Evidence Digests

| Evidence | SHA256 |
| --- | --- |
| Selected / measured-before generator | `a8b6bea1fa60e16ef079e193c659b67c987e4a23551757547d22d7c2216697a3` |
| Rejected measured-after generator | `6be6560fdcce994497b0b05bba276a49fd380f95a00386bf756fece3b6f06a1a` |
| Paired raw results | `e60c24be5cd63dae48e55e8200ec9fe10b5d9152531759f0cb634e176f0afab5` |
| Bounded profile / candidate proof | `3d48b3083f6618ddfdf9520f4026f5fc6891ae024e0e01570031f149e5471dcd` |
| Exact reversible candidate patch | `b26654622552ebf30de3ce46b6ac92291b9dcff0f18a6cd28153182ed7d99791` |
| Reused driver with explicit reference | `5a4dbbab58052a690ece326176571cdd6461aaca83e0b8ec903fb7de41744a99` |
| Frozen string equivalence tests | `362f2570d5a3c9291a698487b9040f1aa0462b66b02ff3867cc70931684d9c49` |
| Driver tests | `35ffa532875c0fc8cef25f128d601e077afefe5d395b2a8487afbb2dc76b5492` |
