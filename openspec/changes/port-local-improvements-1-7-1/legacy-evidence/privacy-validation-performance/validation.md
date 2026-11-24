# Verification: Privacy Validation Performance

Validated 2026-11-21. Full regression: **2,153 passed, 10 skipped**, 70.45 seconds;
package coverage **91.5790%**, above the existing 85% gate. Ruff (`src tests
scripts`), mypy (125 configured source files), strict MkDocs and strict OpenSpec
passed. Whitespace checks passed and historical evidence hashes are unchanged.

The new differential tests freeze the original privacy walk and namespace
policy, comparing it with the candidate across the existing recognition corpus,
all field types/name heuristics/sensitive semantics, actual versus declared
types, strict/report numeric parsing, Unicode, namespaces/detection precedence,
malformed rows/composites/error order and missing values. They also exercise
fresh row/spec mutations across calls and 80 seeded mixed two-entity datasets.
Operation-count checks prove name sensitivity is prepared once per field and
actual string values still reach the original detector, including unexpected
strings in numeric fields. The existing corpus independently verifies detector
classifications. Mandatory checks with disabled report sections and all modes,
callback mutation, streaming global keys, deterministic output and atomic
publication remain covered by the full suite.

Read-only review found no remaining safety blocker: only per-call ordered field
metadata and actual non-string handling changed. The core classifier, its
priority, strict/report policies, row values and random calls are unchanged.

## Repeated Public CSV Benchmark

All **12/12** measured attempts passed. The [full report](benchmark.md) and
[raw JSON](public-csv-results.json) record three fresh runs per path/size with
identical environment/settings, complete concrete validator coverage, exclusive
stages, tree/coordinator RSS and source fingerprints. Every CSV byte count and
SHA-256 matches both prior experiments; report/manifest/permission audits and
complete staging/scratch cleanup succeeded. No worker stderr was emitted and
no heavy verification ran concurrently with measurements.

Independent evidence review checked every attempt, independently recomputed the
stored summary, verified exact stage sums and all 125 source hashes, and
confirmed core classifier and historical evidence hashes remain unchanged.
The cleaned CSV artifacts were audited by the harness; independent review uses
the recorded results and reviewed executable assertions rather than retained
row data.

Relative to shared validation, ordinary medians changed from 9.552 to 7.019
seconds at 100k and 70.874 to 52.975 seconds at 750k. Streaming changed from
6.084 to 3.624 and 41.957 to 24.081 seconds. Privacy takes approximately 61–62%
less time; memory remains broadly comparable. All original limits and publication
checks remain active. This comparison does not introduce a hard RSS cap or
change the streaming key set's row-proportional state.

## Bounded Privacy-Only Profile

Measured 2026-11-21 with Python 3.11.2, 10,000 rows × 25 fields from the existing
`scripts/benchmark_parallel_generation.py:fictional_spec`, seed 42. Generate the
synthetic rows once; profile only the privacy validator, then time three calls
per implementation against those unchanged rows. No live source is accessed,
no row values are retained in the evidence and both implementations return `[]`.

The baseline function was extracted with Python AST from
`git show 26af69043cfd8d46df48ed43e18d5e168d223d3a:src/test_data_agent/safety.py`
and executed in an isolated copy of the current safety module namespace. It
matches the pre-change function. The candidate is the actual edited validator;
the core classifier is unchanged. Source SHA-256 fingerprints:

| Source | SHA-256 |
| --- | --- |
| Baseline function, AST source segment | `59a82eee115dd13044ae0ad12e8da72039dfaed8f7e667e287eb619121b0d3ac` |
| Candidate function, source without trailing whitespace | `d10b319531400c14be5d5c5d6ee24b0d1a694e72e3224df3b371dd858056f023` |
| `src/test_data_agent/core/privacy.py` | `869e021711edf9f2f4f42b075d1cbb48dcf8b76f0d6cbf5135efe8729481abd9` |

The diagnostic probe preceded an equivalent final line-wrapping edit. The final
validator function SHA-256 is
`76858bd0cfaf17c8f9f65df6a665dfdb93b83ea910b123fac8b38e42c90e2a61`;
the public benchmark records the complete final source snapshot. No detector or
policy branch changed between those formatting revisions.

| Privacy-only measurement | Baseline | Candidate |
| --- | ---: | ---: |
| Wall seconds, three repetitions | 0.377316 / 0.382724 / 0.383892 | 0.141587 / 0.141801 / 0.142670 |
| Median wall seconds | 0.382724 | 0.141801 |
| cProfile total seconds | 1.586272 | 0.471260 |
| `is_sensitive_field` calls | 250,000 | 25 |
| `is_sensitive_field` cumulative seconds | 0.968688 | 0.000113 |
| `infer_sensitive_value_type` calls | 250,000 | 120,000 |
| `infer_sensitive_value_type` cumulative seconds | 0.405367 | 0.343515 |
| `looks_high_entropy_token` calls | 80,000 | 80,000 |
| `is_iso_date` calls | 120,000 | 120,000 |

cProfile cumulative times include nested calls and must not be added together or
compared directly with unprofiled wall times. The reduced detector count omits
only non-string values; all string content checks remain. These sequential,
in-process diagnostic repetitions do not establish public export speedup or
peak-memory behavior. The completed public experiment above is the evidence for
end-to-end performance and memory observations.

## Historical Evidence

The immediately preceding public benchmark is
[shared-generation-validation](../shared-generation-validation/benchmark.md).
Keep both files unchanged and write new evidence under this change:

| Historical file in `../shared-generation-validation/` | SHA-256 |
| --- | --- |
| `public-csv-results.json` | `423108624a2edadecc4d432314520fd5dd3a45ec1c60dc4170e24b387228a1d7` |
| `benchmark.md` | `d427475f9fd6108db0660407f13d0a59f156c2efb3bce4985a89d94fe3c10586` |

The earlier `public-streaming-csv` evidence also remains historical. No version
bump, commit, release build, tag, push or publication is part of this change.
