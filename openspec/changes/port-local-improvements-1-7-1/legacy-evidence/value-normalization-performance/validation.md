# Verification: Value Normalization Performance

Implemented and locally verified, unreleased, 2026-11-23. All twelve public CSV
runs succeeded. [benchmark.md](benchmark.md) records every stage and peak RSS;
[public-csv-results.json](public-csv-results.json) preserves metadata-only runs.

## Implementation And Safety Boundaries

Only `validation/values.py` changed among the 126 measured runtime/benchmark
files relative to the latest schema-validation series. The scalar-type tuple is
built once per call, and field names map to prepared parser/nullability pairs.
Every field remains represented, including fields without a parser, preserving
the previous last-entry behavior for mutable duplicate names.

Every value still passes the original scalar eligibility check. Only afterward
can actual non-string values skip string-decoding metadata work. Row iteration,
integer/float/boolean parsers, nullable empty-string rules, failed parsing,
structural filtering, ordered value-free errors, row copying and return identity
remain unchanged. Preparation is rebuilt on each call; no row, conversion result
or verdict is cached across invocations, and input rows/specifications are not
mutated.

Identity is part of the shared validation contract: combined validation reuses
mandatory checks only when normalization returns the original dataset object.
Successful conversion still copies its row and marks the dataset changed, even
when a string subclass compares equal to its decoded value. Input errors still
force the previous new outer/list containers while retaining unchanged rows.

Both report validation and checked generation use this shared normalizer for
every source-derived specification. Strict raw-value privacy remains before
combined normalization, separate from report decoding. No schema, relationship,
constraint, classifier, callback, writer, source read, SQL, budget, random-call
order or seed algorithm changed. No option, public API or dependency was added.

## Exact Equivalence And Mutation Checks

The new `tests/test_normalization_equivalence.py` contains **30 tests** with a
frozen previous implementation. They compare exact normalized values, ordered
errors, exceptions, outer/list/row identities and input non-mutation across all
six declared types and nullability settings.

Cases include numeric/boolean parsing boundaries, Unicode, NaN/inf, huge integers,
native and string subclasses, parser/copy/iteration exceptions, malformed rows
and entity collections, unknown fields/entities and unsupported scalar values.
They retain copy-on-write for mixed converted/unchanged/error rows, duplicate
mutable field names, fresh specification/row edits, 100 fixed-seed mixed datasets
and ten inferred source labels. Existing adapter regressions also pass; source
parity introduces no new reads or content evidence for metadata-only sources.

An independent probe compared **1000 seeded mixed datasets**, including outcomes,
errors, exceptions, identities and input/specification non-mutation: zero
differences. These finite equivalence checks do not estimate real-world detector
accuracy.

## Bounded Normalization Profile

The original source was frozen before editing; its hash equals the latest
public baseline's recorded normalizer. Use 10,000 fictional rows × 25 fields,
seed 42, with the same native rows and their CSV-loaded string representation.
Nine alternating old/new-order passes per workload run without concurrent heavy
verification. Generation, serialization/loading and parity checks are outside
timing. Arrays and source hashes are retained in
[normalization-profile-results.json](normalization-profile-results.json).

| Workload | Previous median, s | Prepared median, s | Less normalization time |
| --- | ---: | ---: | ---: |
| Native generated scalars | 0.023928333 | 0.011833583 | 50.55% |
| CSV-loaded strings | 0.042359875 | 0.031469916 | 25.71% |

The native case retains original dataset identity; CSV decoding returns a new
dataset as before. These are normalization-only diagnostics. Full public CSV
measurements separately show **49.10–50.65% less normalization time**, with
**1.51–2.03% less ordinary API time** and **4.31–4.50% less streaming API time**
against the historical latest baseline.

## Executed Gates

- Full suite with the existing 85% coverage gate: **2767 passed, 10 skipped**
  in **78.35 seconds**.
- Total line coverage: **91.998812440%**, 12,395 / 13,473 statements;
  normalizer: **100%**, 43 / 43 statements.
- Ruff over `src tests scripts`: passed.
- Mypy over 124 source files: passed.
- Strict MkDocs build and strict OpenSpec validation: passed.
- `git diff --check`: passed.
- Independent implementation review and raw-results audit: no findings.

```bash
.venv/bin/python -m pytest -q --cov=test_data_agent \
  --cov-report=term --cov-report=json:/private/tmp/apa-normalization-coverage.json \
  --cov-fail-under=85
```

No tests or other heavy verification ran concurrently with public timing.
All real schema/privacy/relationship/constraint validators and normalization
covered exactly every requested row: one ordinary entity, or 25/184 streaming
tiles. All report sections passed. Per-run exclusive stage sums equal API time.

The independent parent audited CSV headers/counts/ordered unique keys, report
and manifest flags/counts/engine, exact artifact set, hashes, 0700 directories,
0600 files, staging absence and scratch removal. It does not repeat per-cell
privacy classification; real runtime privacy checks and unchanged privacy
regressions provide that evidence.

All repetitions within each size/path have identical CSV bytes/SHA-256 and
match every corresponding latest schema-validation repeat and the driver's older
privacy-validation reference. Ordinary/tiled outputs remain different because
their existing seed namespaces differ. All 126 recorded source hashes match the
final working tree, and environment/settings equal the latest baseline.

## Provenance And Limits

| File / snapshot | SHA-256 |
| --- | --- |
| Previous normalizer, matching latest baseline | `0f125b1187c483f38ca47ad700a751d688ae6da7f28023e29fde57be2da89e93` |
| Current normalizer | `795bac3f7307f244a1520a2a63569aafb6704560f6c2f75b10351b6313c966c4` |
| New frozen-reference test file | `5c724d1d5b4cdae5d4b7f512584250341c55f8b1a77e3f5e1ed82b50eff0f7e6` |
| `normalization-profile-results.json` | `5c3411d20740900ff2018899a057968b9494b376c3ebcb8635904116d354ba8e` |
| `public-csv-results.json` | `65e588a7784c6591e7e7d30517ef4ba3c3f93cdd081cc7701d79d6ee7520eb24` |
| Latest baseline `../schema-validation-performance/public-csv-results.json` | `8001de3b876dfbef3dc51dff012a61044df8c1492dec4fed6e902d864eb05da4` |

Historical benchmark artifacts and the driver remain unchanged. All fixtures
and probes are fictional; benchmark artifacts retain no rows. Live database
integrations were not run; ten environment-gated tests remain skipped. No
production data or external AI provider was used. RSS is sampled and may miss
peaks or count shared pages repeatedly; the historical API comparison is not a
paired old/new experiment. No version, commit, tag, release or publication was
selected.
