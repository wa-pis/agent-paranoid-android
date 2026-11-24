# Streaming profiling validation

Local validation on 2026-11-21. This is unreleased implementation evidence,
not publication or release acceptance.

## Full-profile equality and memory

All **24 full-pipeline runs** compared the complete sanitized profile dictionaries,
not only distinct counts; all matched across backends and all three repeats.
Every run also recorded the same profile fingerprint for the same fixture and
sample policy. Focused tests separately compare inferred DatasetSpecs and their
fingerprints, local-category policy and cache round trips.

Apple M4 Max, 14 physical/logical cores, 36 GiB RAM, macOS 26.6.2 arm64;
CPython 3.11.2, DuckDB 2.0.1, PyArrow 25.0.0, Pydantic 2.13.4. Each measurement
used a fresh process; timed workers ran sequentially. This is a normal desktop
host without CPU affinity or an OS cache purge. The fixture has 25 string fields,
a synthetic identifier and a late duplicate of the first row. No real source
or production data was used.

The checker calls `profile_example_folder` with cache disabled, including CSV
reading, normalization, full sensitivity/type/distribution work, bounded rule
samples, relationship/constraint inference and sanitization. `set` is the same
current profiler with the handoff disabled; `auto` uses the production 1,000,000
entry threshold. These comparisons do not measure the pre-change checkout.

Time is parent wall time including process startup, imports and safe profile
serialization, excluding synthetic CSV construction and parent equality checks.
Memory is fresh-worker peak RSS including Python, Arrow, DuckDB and rule samples.
Tables show **median [minimum–maximum]** over three runs; MiB = 1,048,576 bytes.

| Rows × fields | Rule sample rows | Path | Total seconds | Peak RSS, MiB |
| --- | ---: | --- | ---: | ---: |
| 10,000 × 25 | 2,000 | set | 1.07 [1.04–1.09] | 105.7 [100.4–107.0] |
| 10,000 × 25 | 2,000 | auto | 1.05 [1.04–1.08] | 105.0 [104.7–106.5] |
| 100,000 × 25 | 2,000 | set | 8.31 [8.08–8.40] | 425.8 [416.9–426.5] |
| 100,000 × 25 | 2,000 | auto | 10.00 [9.92–10.22] | 412.1 [373.0–413.3] |
| 250,000 × 25 | 2,000 | set | 20.30 [20.03–20.39] | 913.9 [903.8–916.1] |
| 250,000 × 25 | 2,000 | auto | 24.90 [24.73–25.67] | 382.0 [375.1–393.9] |
| 250,000 × 25 | 50,000 | set | 20.03 [19.77–20.07] | 1027.7 [1024.6–1028.8] |
| 250,000 × 25 | 50,000 | auto | 24.39 [24.36–24.42] | 520.9 [509.8–533.2] |

With the **default 50,000-row rule sample**, automatic counting used a median
521 MiB versus 1,028 MiB at 250k × 25: about half the memory, with 24.39 s versus
20.03 s (22% longer). The earlier pure-distinct benchmark's 7.8× memory reduction
and 9% time cost must not be presented as whole-profiler results.

At 100k × 25 with a 2k sample, the RSS reduction was only about 3%, with a 20%
time cost. The internal threshold limits growing set state; it is not a claim
that DuckDB always improves total RSS immediately after switching. Small and
low-cardinality profiles retain sets and avoid backend imports.

The 250k × 25 fixture has 6.25 million cells and remains within the existing
row/cell/file/byte budgets. The offline checker explicitly allows 600 seconds;
all measured calls finished below the normal 120-second deadline. No product
input budget was raised. The first 18 runs used an explicit 2k sample; the final
six used the default 50k sample. Bounded samples remain a separate memory cost.

Reproduce from a checkout with the profiling extra installed:

```sh
python scripts/check_duckdb_profiling.py --rows 10000 100000 \
  --rule-sample-rows 2000 --output /tmp/full-profile-results.json
python scripts/check_duckdb_profiling.py --rows 250000 \
  --rule-sample-rows 2000 --output /tmp/full-profile-large-results.json
python scripts/check_duckdb_profiling.py --rows 250000 \
  --output /tmp/full-profile-default-sample-results.json
```

Raw results: [small/medium](full-profile-results.json),
[large with 2k sample](full-profile-large-results.json),
[large with default sample](full-profile-default-sample-results.json).
The [checker](../../../scripts/check_duckdb_profiling.py) verifies complete
profile equality and retained late-duplicate pool sizes before recording a run.

## Sensitive scratch and failures

`tests/test_duckdb_distinct_security.py` uses synthetic canaries and a real
300,001-distinct query at a 16 MiB buffer limit to force and inspect active spill.
It checks the private directory's POSIX mode 0700 and absence of raw canary,
unkeyed SHA-256 and invocation keys. Arrow receives only ordinal integers and
32-byte HMAC tokens, different across invocations. The default 128 MiB setting
is a buffer limit, not a process RSS guarantee.

A forced 1 KiB spill cap fails safely. Tests exercise generic native and producer
errors, original structured input/profile budgets, native query timeout,
KeyboardInterrupt/SystemExit during query and producer work, cleanup failure,
close-before-removal order, context/message/log redaction and no partial cache.

An additional isolated process test sent a real **SIGINT after the producer
finished**, while native aggregation still ran over two million synthetic
digests with a 16 MiB buffer. It raised KeyboardInterrupt and left zero scratch
entries. This does not test cleanup after SIGKILL of the owner process.

Only ephemeral keyed digests can remain after abrupt process death; their key
is not persisted. There is no promise of secure erasure, a hard whole-process
memory limit, protection against a compromised owner process, or cleanup after
SIGKILL/machine failure.

## Compatibility and packaging evidence

- Complete profile tests cover both public folder entry points, inferred
  relationships and all four constraint types, sampling/category boundaries,
  UTF-8 BOM/semicolon, Latin-1, Unicode whitespace, multiline values, null/empty
  entities, leading zeros, large integers, floats, boolean/date/timestamp values,
  late sensitive evidence and duplicates, local allowlists, cache hits and exactly
  one text read of the source across handoff.
- The optional extra stays outside base dependencies. The lock added only
  DuckDB 2.0.1; existing locked versions did not move. Dependency policy,
  minimum constraints, CLI doctor and installed wheel checks include profiling.
- Final wheel: 270,670 bytes, all 120 package Python files matched the checkout.
  SHA-256: `5c5b0da79f0b8b4cc5f4a6c7fe1b1ca80939ef6f7cd7ffaa130afd2b6df31398`.
- Final wheel passed isolated base and profiling minimum installation checks,
  synthetic demo/CSV/JSON smoke and doctor. The minimum profiling runtime used
  DuckDB 2.0.1, PyArrow 15.0.0, Pydantic 2.7.0 and Faker 25; 12 runtime
  distributions had approved licenses. After adding pytest, 32 focused
  equivalence/security/overflow checks passed under these minimum versions.
- Full local regression: **1,886 passed, 10 skipped**, with **91.33% coverage**
  against the required 85% gate. Ruff, strict mypy
  (122 checked files), compile checks, public contracts, dependency compatibility,
  lock freshness, license checks and strict MkDocs build passed.

Not run: Python 3.12–3.14 locally, live external DB/provider tests, all hardware
and dependency combinations, or release/publishing gates. CI contains the
supported Python matrix and a focused minimum-profiling job. No release was
created and cache format 5/profile semantics remain unchanged.
