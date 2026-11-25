# Verification: Schema Validation Performance

Implemented and locally verified, unreleased, 2026-11-23. All twelve public CSV
attempts succeeded; stage timings, memory and output hashes are recorded in
[benchmark.md](benchmark.md) and [public-csv-results.json](public-csv-results.json).

## Implementation And Boundaries

Only `validation/schema_validator.py` changed among the 126 measured source and
benchmark files relative to the latest source-independent profiling series.
Prepare ordered field names, nullability, scalar predicates and optional length
bounds once per entity/call. Resolve the primary-key predicate lazily on the
first eligible value, preserving previous missing-field exception behavior.

Scalar predicates retain the previous expressions and parsers: integer/bool and
subclass distinctions, finite floats, numeric strings, temporal prefix/parsing
behavior and string acceptance. Entity/count/shape, required-value, length,
type and primary-key checks retain their diagnostics and order. No row, verdict
or specification is cached across calls. Fresh specification edits are observed
on the next invocation; input rows and specifications are not mutated.

The shared validator serves mandatory generation and report validation for both
CSV paths and all source-derived specifications. No adapter/source branch,
source read, SQL, budget, privacy classifier, normalization, callback boundary,
writer, random-call order or seed algorithm changes. All safety and publication
checks continue to run. No dependency, setting, option or public API was added.

## Exact Equivalence

The new `tests/test_schema_validation_equivalence.py` contains **33 tests** with
an independent frozen previous walk/type dispatcher. It compares exact returned
errors and exception types/arguments across all six field types, native and
string scalars, bool/int/float subclasses, non-finite numbers, Decimal, temporal
prefixes/timezones, conversion failures and huge integers.

Coverage includes nullable values and pattern bounds independently of declared
type; primary-key required/type/uniqueness and duplicate diagnostics; invalid
entity/count/row shapes; `UserDict`, `MappingProxyType` and unusual mappings;
lazy lookup of a removed primary-key field; specification/row edits between
calls; 100 fixed-seed mixed datasets and ten inferred source labels. Existing
full-suite adapter regressions remain in place; these source-label cases do not
introduce source reads or claim content evidence from schema-only sources.

An independent synthetic probe additionally compared **8,392 scalar outcomes**
and **2,506 full-row outcomes**, finding zero result or exception differences.
These bounded equivalence checks do not estimate real-world privacy accuracy.

## Bounded Validator Profile

The frozen pre-change source was captured before editing and its hash equals
the latest public baseline's recorded schema-validator hash. Generate the same
fictional 10,000-row × 25-field fixture once, seed 42, then validate unchanged
rows in nine alternating old/new-order passes. Generation, parity probes and
other heavy verification are outside authoritative timing. Only metadata is
retained in [schema-profile-results.json](schema-profile-results.json).

| Implementation | Median schema time, s |
| --- | ---: |
| Frozen previous validator | 0.080485208 |
| Prepared current validator | 0.032581416 |

This is **2.47× faster**, or **59.52% less schema time**. It measures only the
validator. Full public API measurements separately show **55.91–59.59% less
schema time**, **6.02–6.31% less ordinary API time** and **13.45–16.77% less
streaming API time**, against the historical latest baseline.

## Executed Gates

- Full suite with the existing 85% coverage gate: **2737 passed, 10 skipped**
  in **82.73 seconds**.
- Total line coverage: **91.982777819%**, 12,391 / 13,471 statements;
  schema validator: **100%**, 89 / 89 statements.
- Ruff over `src tests scripts`: passed.
- Mypy over 124 source files: passed.
- Strict MkDocs build and `openspec validate schema-validation-performance
  --strict`: passed.
- `git diff --check`: passed.
- Independent implementation review and raw-results audit: no findings.

The coverage command was:

```bash
.venv/bin/python -m pytest -q --cov=test_data_agent \
  --cov-report=term --cov-report=json:/private/tmp/apa-schema-coverage.json \
  --cov-fail-under=85
```

No tests or other heavy verification ran concurrently with the public timing.
Each real schema, privacy, relationship, constraint and normalization validator
covered every requested row exactly once per complete ordinary entity or tile.
The independent parent audited counts/keys, report and manifest flags, all
artifact hashes, 0700/0600 permissions, staging absence and scratch removal.
The parent does not repeat per-cell privacy classification; runtime checks and
the retained privacy regression suites provide that evidence.

All three repeats of every size/path have the same CSV bytes and SHA-256, also
matching every corresponding repeat of the latest source-independent baseline
and the harness's older privacy-validation baseline. Ordinary and tiled output
remain different because their established seed namespaces differ. All 126
current source hashes and the environment/settings match the recorded candidate.

## Provenance

| File / snapshot | SHA-256 |
| --- | --- |
| Previous schema validator, matching latest baseline | `b2879d0f714ed7ee154e147bb9e57552d3a0653873411e79dd02d3e3b16399ce` |
| Current schema validator | `6e59175eebc14fbb5ee6a21db324bfa281258d100e914349bf4362f13d672cb6` |
| New frozen-reference test file | `d36a608c833f37a199d878e2697f03fbb70702d196a2a1846fa39750b58e366b` |
| `schema-profile-results.json` | `a4f816c0b44563d42ff6fe959424dc6e0cab5a5643647f3dfc1614a4c98b6306` |
| `public-csv-results.json` | `8001de3b876dfbef3dc51dff012a61044df8c1492dec4fed6e902d864eb05da4` |
| Latest baseline `../source-independent-profiling/public-csv-results.json` | `e2a84aed6a266c85d59295f8f19eb2d4d3882712391f9f896f59bbb4add84330` |

Historical benchmark artifacts and the driver remain unchanged. All fixtures
and measurements are fictional; benchmark artifacts retain no generated rows.
Live database integrations were not run; the ten environment-gated tests remain
skipped. RSS is sampled and may miss peaks or count shared pages repeatedly;
the historical API comparison is not a paired old/new experiment. No version,
commit, tag, release or publication was selected.
