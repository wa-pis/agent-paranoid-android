# Verification: Privacy Detector Performance

## Status

Implementation and verification completed, 2026-11-22. All twelve public CSV
attempts succeeded. Timings, memory and detailed checks are recorded in
[benchmark.md](benchmark.md), with metadata-only runs in
[public-csv-results.json](public-csv-results.json).

The final candidate passed the full suite: **2,159 passed, 10 skipped** in
80.49 seconds, with **91.5790% coverage** (existing minimum: 85%). Ruff over
`src tests scripts`, mypy over 125 configured source files, strict MkDocs and
`openspec validate privacy-detector-performance --strict` passed. A separate
100-row public-export smoke experiment passed for both paths.

The focused detector/corpus/privacy-walk suite passed all 15 tests. The new
independent frozen-policy oracle compares exact recognition tags, not only
sensitive/non-sensitive decisions. It covers the existing recognition corpus,
targeted synthetic boundaries, 1,600 fixed-seed random strings and 600 mutations;
Unicode case folding, newlines, classification priority, entropy thresholds,
long separated card candidates and hostile string subclasses are included.
The final built-in-membership implementation does not invoke overridden
`__contains__` methods, including ones that hide characters or raise exceptions.
Existing full-suite tests retain shared consumer, strict/report policy,
deterministic generation, validation and atomic-publication coverage.

## Bounded Classifier Profile

Measured 2026-11-22 with Python 3.11.2. Generate exactly 10,000 fictional rows
once from `scripts/benchmark_parallel_generation.py:fictional_spec`, seed 42,
then collect their 120,000 actual string values. Time classification over those
unchanged values. No live source is accessed, no source or generated rows are
retained in this evidence, and only aggregate counts and timings are reported.

The final timing probe loads the original source directly from
`git show 26af69043cfd8d46df48ed43e18d5e168d223d3a:src/test_data_agent/core/privacy.py`
into one isolated module namespace and captures the implemented working-tree
source in another. The candidate uses `str.__contains__(text, literal)` for all
three necessary-character tests, preserving underlying-string behavior even
when a string subclass overrides membership. The earlier operator-membership
prototype timings are superseded and are not evidence for the final candidate.

| Captured source | SHA-256 |
| --- | --- |
| Frozen original `core/privacy.py`, matching the latest public baseline | `869e021711edf9f2f4f42b075d1cbb48dcf8b76f0d6cbf5135efe8729481abd9` |
| Implemented built-in-membership candidate `core/privacy.py` | `642dfde5ce68f256bc2a0bcd833f97d603104f509e82008a6c5c00c87af0c23f` |
| `/private/tmp/apa_detector_builtin_profile.py` | `be0186423c8f11917e129e9ffbc7eff607b116bedfef6e64b969dbba22ad8b35` |

The metadata-only result is `/private/tmp/apa-detector-builtin-profile-results.json`.
These temporary files are diagnostic provenance, not shipped APIs or persistent
benchmark dependencies. The original is read from the fixed revision, rather
than from the edited module. The public experiment records the authoritative
final source snapshot separately.

The initial pre-change diagnostic used per-pattern timing proxies that delegate
each original regex call, measure only that call and retain call counts and
elapsed seconds. Its largest regex cost was
80,000 secret-assignment searches, 0.035655 seconds. Email full matches took
0.014095 seconds over 75,572 calls; ISO-date full matches took 0.013474 seconds
over 120,000 calls. Each remaining regex accounted for less than 0.0082 seconds.
Proxy measurements include timing overhead and are diagnostic; they are not
summed into or compared directly with uninstrumented wall times.

Seven interleaved uninstrumented passes compare the frozen original with the
implemented candidate that adds only the assignment and email guards through
built-in string membership. Each pass runs the original before the candidate:

| Pass | Original seconds | Built-in-membership candidate seconds |
| --- | ---: | ---: |
| 1 | 0.119600 | 0.082769 |
| 2 | 0.119019 | 0.081953 |
| 3 | 0.118113 | 0.081957 |
| 4 | 0.118485 | 0.082513 |
| 5 | 0.119043 | 0.082824 |
| 6 | 0.119063 | 0.082908 |
| 7 | 0.119799 | 0.083017 |
| Median | 0.119043 | 0.082769 |

The median classifier time fell by 30.47%. These in-process measurements exclude
generation, validation traversal, encoding, writing, artifacts and publication.
They do not establish public API performance or peak-memory behavior.

The final diagnostic also compared the original with the implemented candidate
across all 120,000 generated strings and the recognition corpus plus 9,000
fictional edge constructions from seed 11022 (9,029 cases in total), including
Unicode keyword variants, separators, embedded assignments, whitespace and
newlines. It found zero mismatches in both groups. These bounded checks
supplement the necessary-character proof and the completed executable regression
gates, including string-subclass compatibility checks.

## Public Experiment And Independent Audit

The final experiment used the actual public API, seed 42, 25 fields, 100,000 /
750,000 rows and three fresh processes per path/size. The entire environment
and settings records equal the immediately preceding privacy-validation
baseline. No tests or other heavy verification ran concurrently with timing.

An independent read-only audit recomputed the complete summary from the raw
twelve successful attempts. It verified exact per-run stage sums, all concrete
validator and normalization call counts and row coverage, all report/manifest/
artifact checks, private permissions, staging cleanup and scratch removal.
Every CSV byte/hash pair matches all corresponding historical repeats in the
privacy-validation, shared-validation and public-streaming series. Every one
of the 125 recorded source hashes matches the measured working tree.

An AST comparison with the frozen original confirms that only
`infer_sensitive_value_type` changed in the detector module. All regexes,
helpers and models remain unchanged. The shared row-privacy implementation
also matches the preceding experiment's source hash. The benchmark driver
changes only its baseline and default result paths, preserving instrumentation,
budgets, validation and independent audits.

The new raw-results SHA-256 is
`31d9d79ab3f9ff0fd1cdee5f2195e259f13ab38155cc301d790be5bdcfd047c2`.
Public privacy-stage medians fell by 21.77–23.85%; total API medians fell by
1.93–3.79% for ordinary export and 7.99–9.65% for streaming. Peak-memory changes
are small and mixed. The baseline is a prior series rather than interleaved
before/after checkouts; measured benefits depend on workload and timing noise.

## Historical Evidence

The immediately preceding baseline is
[privacy-validation-performance](../privacy-validation-performance/benchmark.md).
Record new public evidence under this change and keep both historical files
unchanged:

| Historical file in `../privacy-validation-performance/` | SHA-256 |
| --- | --- |
| `public-csv-results.json` | `ed54cd83c855384c4e2a70486604a939f7aec7aec11e238fde3dc6b0723cf88c` |
| `benchmark.md` | `f1887d98e04c0c74592b616ac7768223fbb5be624ef0f50ea88b9b1fd70ae09e` |

The earlier shared-validation and public-streaming evidence also remains
historical. No version bump, commit, release build, tag, push or publication is
part of this change.
