# Verification: Generation Dispatch Performance

Completed on 2026-11-24, unreleased. Retain the shared dispatch optimization.
[benchmark.md](benchmark.md) records every paired observation and the memory
caveat; [paired-results.json](paired-results.json) contains metadata, not rows.

## Change And Safety Proof

Relative to the frozen previous tree, only
`src/test_data_agent/generation/entity_generator.py` differs. An AST comparison
finds one changed module node: `generate_field_value`. Its applied AST equals
the measured diagnostic candidate; only formatting differs from that candidate.

The categorical check still precedes scalar dispatch. Previously, six local
distribution selections ran before that dispatch; now each branch evaluates
only its relevant selection(s). The selected arguments, scalar helpers and
random calls in the branch reached are identical. No arithmetic, parsing,
rounding, string construction, weighted choice or date-generation helper changes.
Null, invalid, identifier, sensitive-string and semantic-provider handling keeps
its original priority and early returns.

No source label is consulted, and every source-derived specification reaches
the same generator. No source-row read, query, cache, dependency, seed namespace
or public signature is added. Existing per-call/per-tile distribution preparation
remains unchanged; later specification edits are observed. Budgets, constraint
solving, mandatory validation/privacy, reports and atomic publication are intact.

## Equivalence Regressions

`tests/test_generation_dispatch_equivalence.py` has **61 tests**, passing against
both the frozen previous source and the candidate. Its independent complete
previous field-dispatch function shares only unchanged scalar helpers. Coverage
includes six field types, all five generation modes, thirteen typed/raw/mismatched
distribution shapes, prepared/unprepared mappings, exact return types, exceptions,
Random/Faker states, null/primary-key/invalid/identifier/sensitive/provider priority,
provider rejection, complete ordinary and tile head/tail CSV output, mutation
visibility and ten source variants. The type/distribution matrix alone compares
9,360 value-or-error outcomes, including state after every call.

An additional independent source check compares actual before/after ordinary and
tiled generation for 500 rows and verifies row/RNG/Faker equality over fifteen
mode/seed combinations. The bounded nine-pair diagnostic preserves all eighteen
datasets. Its metadata and applied-source proof are retained in
[dispatch-profile-results.json](dispatch-profile-results.json).

The 99 focused existing distribution, parallel generation, semantic-provider and
identifier-pool tests passed before benchmarking. Existing suites also retain
mandatory raw privacy, callback mutation, relationships/rules, source policy,
1/2/4-worker determinism, budgets, formula encoding, failure cleanup and atomic
destination protection.

## Public Benchmark And Decision

All **32 measured runs plus four four-row smoke runs passed**. The unchanged
worker, instrumentation, memory sampler and parent audit perform every original
check. Each concrete validator and normalization covers every row exactly once
per ordinary entity or streaming tile (25/184 tiles at 100k/750k). All report
sections, exact counts/ordered keys, manifest/artifact hashes, synthetic/no-source-
reuse flags, 0700/0600 permissions, staging absence and output cleanup pass.
CSV bytes match every corresponding repeat of the previous paired series within
each engine; legacy and tiled seed namespaces intentionally differ.

Before/after copies contain 126 source/helper hashes each. Before exactly matches
the previous CSV paired report's final variant; after exactly matches the selected
working tree. Only the generator module differs. Helpers are byte-identical.
Fresh measurement helpers verify package/module origins, and measured workers
inherit the chosen snapshot environment; spawned workers inherit its search path.
Fingerprints remain unchanged, all measured bundle/snapshot scratch is removed,
and the read-only supplied baseline was independently verified then removed by
the task owner after replay verification.

Generation/IPC time wins **16/16 pairs**, total API time **15/16**. Both AB and BA
subsets improve per case. Ordinary median paired generation reductions are
8.96%/9.73%; total-time reductions are 6.15%/6.37% at 100k/750k. Streaming total
reductions are 0.49%/1.29%, with one 750k API pair 0.439% slower. Streaming
generation/IPC is exposed coordinator work/waiting, not total worker computation.

Keep the change with the measured memory caveat: 100k ordinary sampled peak tree
RSS rises **271.719 → 297.719 MiB**, and all four paired samples rise; coordinator
high-water maxima rise **300.281 → 302.141 MiB**. The high-water increase is only
1.859 MiB (0.619%), and the other three cases' coordinator maxima decrease.
Sampling/phase duration may contribute to the discrepancy, but this experiment
does not prove its cause or establish a memory improvement. There is no consistent
material high-water regression across workloads. Four local pairs and sampled
RSS do not provide a confidence interval or a general speed/memory guarantee.

## Regression Gates

- Full suite: **2,947 passed, 10 skipped** in **77.83 s**.
- Statement coverage: **92.0336%**, **12,396 / 13,469**, exceeding the 85% gate.
  Generator module: **96.30%**, **182 / 189**.
- Ruff across `src tests scripts`: passed. Mypy: passed for all 124 source files.
- Strict OpenSpec validation and strict MkDocs build: passed. Documentation tests
  after the report/guide edits: **49 passed** in **0.56 s**. `git diff --check`: passed.
- Independent raw audit recomputed all summaries, individual pairs, order subsets,
  stage sums, checks, source maps, output equality and cleanup; no findings.
- Reversing [generation-dispatch.patch](generation-dispatch.patch) in a private
  copy reproduces all 126 before fingerprints exactly; replay scratch is removed.

```text
.venv/bin/python -m pytest -q --cov=test_data_agent --cov-report=json:/private/tmp/apa-generation-dispatch-coverage.json --cov-fail-under=85
.venv/bin/ruff check src tests scripts
.venv/bin/mypy src
openspec validate generation-dispatch-performance --strict
.venv/bin/mkdocs build --strict
.venv/bin/python -m pytest -q tests/test_documentation.py
git diff --check
```

Only fictional fixtures were used. Live database integrations and external
providers were not exercised; ten environment-gated tests remain skipped.
No version, commit, tag, release or publication was selected. Historical evidence
remains unchanged.

## Evidence Digests

| Evidence | SHA256 |
| --- | --- |
| Before generator | `0bf42e8b42d9d28649a4c9baee4e664847e10ea5b983fabc53280aa50003ee9e` |
| After generator | `a8b6bea1fa60e16ef079e193c659b67c987e4a23551757547d22d7c2216697a3` |
| Paired raw results | `ee1ccb8a738271d34fe7158af13e2454e6891244c5de12482aa5725fa19a4b1c` |
| Bounded profile / applied-source proof | `9a3bcb41ac6ed80f4013ed5ba3939563a94b8c984a4d120d4621903edef7d79a` |
| Exact reversible runtime patch | `1b227d271fe5584d3c4bc55367c92dce852c89e53dfdbeaf8fd6f1b0f5657ada` |
| New paired driver | `7e022c3da60d3cd1d7c292f051c02b3a174310d91c1e58bb6762dc547d856ea5` |
| Frozen equivalence tests | `c47a30d6296699cae302835dbaad04ea63b57aa536982496df39d7ed5f7fae4a` |
| Paired-driver tests | `01e2fdd03cf5516f9c456e8a28fb990fbc92d950194a75e3c75e1672fd0741af` |
