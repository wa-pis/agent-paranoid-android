# Verification: CSV Encoding Performance

The [paired follow-up](paired-benchmark.md) and its
[raw results](paired-results.json) are the current keep/revert evidence. The
initial implementation and historical measurements below remain intact; the
follow-up verification is recorded at the end of this document.

Implementation and regressions verified on 2026-11-23; evidence finalized on
2026-11-24, unreleased. All twelve public CSV runs succeeded.
[benchmark.md](benchmark.md) records stage times, ranges, peak
RSS and the measured total-time increases; raw metadata is retained in
[public-csv-results.json](public-csv-results.json).

## Minimal Change And Equivalence Argument

Only `io/writers.py` differs among the 126 measured source/benchmark files from
the latest value-normalization baseline. The change adds two lines to the
shared `neutralize_csv_cell`, used for headers/cells by ordinary and streaming
CSV paths. Encoding loops, schema checks, C CSV formatting, UTF-8 conversion,
buffers, output limits and atomic writers remain unchanged.

After the existing string/empty guard, an exact built-in string returns unchanged
when its first character is outside ` \t\r\n=+-@`. The original ASCII `lstrip`
cannot remove that character, and neither original formula condition can match.
All whitespace/control/operator prefixes still execute the original logic.
Every string subclass also keeps its original method dispatch, including
overridden truth, stripping, indexing and concatenation. Non-string handling
is unchanged. No synthetic-prefix bypass, value cache or dependency was added.

The output object, byte format and formula policy remain unchanged. Source
labels do not select another encoder. No source reads, SQL, classifier, seed,
random-call order, validation setting, callback or trust boundary changed.
Mandatory checks still precede encoding/writes; temporary permissions, byte/time
bounds, fsync, cleanup and atomic file/bundle publication remain in force.

## Exact Bytes, Errors And Publication Regressions

The new `tests/test_csv_encoding_equivalence.py` contains **88 tests** with a
frozen previous neutralizer and CSV walk. They compare exact bytes, return
identity, exceptions and non-mutation for supported native scalars, floats,
date/datetime, Unicode, delimiters, quotes, newlines and control characters.

Cases cover every formula prefix in headers and cells, ASCII stripping versus
other Unicode whitespace, empty/missing/extra/reordered fields, schema and
mapping quirks, native/string subclasses and overridden bool/lstrip/index/add
methods. They include 100 fixed-seed mixed datasets, row/call edits, ten inferred
source labels and streaming tile boundaries 1/2/4. An encoding/UTF-8 failure
regression verifies the previous target survives and private temporary files
are removed. Existing full-suite tests retain broader privacy, mandatory-check
order, disabled reports, resource limits, interruption, symlink/race and atomic
publication checks.

An independent probe compared **5560 neutralizer cases**, including 5000
fixed-seed strings and ASCII/Unicode/subclass boundaries: zero return, identity
or exception differences. These finite checks are not a real-world privacy
accuracy estimate.

## Bounded Encoder Diagnostic

The original writer source was frozen before editing; its hash equals the latest
public baseline's recorded writer. Generate the same fictional 10,000 rows × 25
fields once, seed 42. Eleven alternating old/new-order passes per workload run
without concurrent heavy verification. Generation and byte/hash comparisons
are outside timers; only metadata is retained in
[encoding-profile-results.json](encoding-profile-results.json).

| Isolated workload | Previous median, s | Current median, s | Less encoding time |
| --- | ---: | ---: | ---: |
| `rows_to_csv` returning text | 0.048042500 | 0.046076667 | 4.09% |
| Streaming encoding expression, including UTF-8 | 0.044819875 | 0.042370375 | 5.47% |

The streaming diagnostic uses the existing StringIO/newline/writerows/UTF-8
expression without validation or filesystem I/O; it is not public export time.
Every diagnostic output is byte-identical. Full public CSV measurements show
**1.31–3.91% less encoding time**, but **1.17–3.22% more total API time**. They
do **not** establish an end-to-end export speedup. Other stages also increased;
the historical comparison does not identify the cause of those changes. All
repeats, including the slower 49.790613-second ordinary 750k run, remain recorded.

## Executed Gates

- Full suite with the existing 85% coverage gate: **2855 passed, 10 skipped**
  in **82.37 seconds**.
- Total line coverage: **92.014842301%**, 12,399 / 13,475 statements.
- `rows_to_csv`: **100%**, 12 / 12 statements; `neutralize_csv_cell`:
  **100%**, 8 / 8 statements. The whole mixed-format writer module is 188 / 219.
- Ruff over `src tests scripts`: passed.
- Mypy over 124 source files: passed.
- Strict MkDocs build and strict OpenSpec validation: passed.
- `git diff --check`: passed.
- Independent implementation review and raw-results audit: no findings.

```bash
.venv/bin/python -m pytest -q --cov=test_data_agent \
  --cov-report=json:/private/tmp/apa-csv-encoding-coverage.json --cov-fail-under=85
```

No tests or other heavy verification ran concurrently with public measurement.
Every real schema/privacy/relationship/constraint validator and normalization
covered every requested row: one ordinary entity, or 25/184 streaming tiles.
Combined validation ran once per entity/tile, all report sections passed and
exclusive stage sums equal API time in every run.

The independent parent audited CSV headers/counts/ordered unique keys, report
and manifest flags/counts/engine, exact artifact set, every artifact hash, 0700
directories, 0600 files, staging absence and scratch removal. It does not repeat
per-cell privacy classification; the unchanged real runtime privacy validator
and retained privacy regressions provide that evidence.

Every repetition within each size/path has identical CSV bytes/SHA-256, matching
all three corresponding latest value-normalization repeats and all three older
driver-reference repeats. Ordinary/tiled outputs retain distinct existing seed
namespaces. All 126 source hashes match the final tree; environment/settings
equal the latest baseline. The streaming module and publication code are unchanged.

## Provenance And Limits

| File / snapshot | SHA-256 |
| --- | --- |
| Previous writer, matching latest baseline | `2b3a824796ea8c074b3d92a476df89a6efd63f49ce3ead687c30280920d56ef8` |
| Current writer | `47b9196b219de8b03fafb56b031159e67122a60fc1fcb6c00d8c3b9f17c15bc4` |
| New frozen-reference test file | `13d972d939551fbf882c0a2a4acfce5e4059c876377020cb629dd021cca2a620` |
| `encoding-profile-results.json` | `0d8888696c6b3d500cb502dd8bb1f8af123700116e904ccf2344a78a5d20ae8c` |
| `public-csv-results.json` | `3bcb174e80561d2fa26b06f52786a62a6b04656f95017b36caff80ecf280d937` |
| Latest baseline `../value-normalization-performance/public-csv-results.json` | `65e588a7784c6591e7e7d30517ef4ba3c3f93cdd081cc7701d79d6ee7520eb24` |

Historical artifacts and the benchmark driver remain unchanged. All fixtures
and probes are fictional; benchmark artifacts retain no rows. Live database
integrations were not run; ten environment-gated tests remain skipped. No
production data or external AI provider was used. RSS sampling can miss peaks
and count shared pages repeatedly; historical API runs are not a paired old/new
experiment. No version, commit, tag, release or publication was selected.

## Paired Follow-up: 2026-11-24

All 32 measured runs and four four-row smoke runs succeeded. Each size/path has
four adjacent before/after pairs, balanced AB/BA, with the original
`benchmark_public_csv.py` worker, instrumentation, memory sampler and parent audit.
The two temporary source copies differ only by the two-line writer guard; all
126 source/helper fingerprints also exactly match their respective historical
before/after reports. Import origins and the streaming neutralizer alias were
checked, source fingerprints remained unchanged, and all owned scratch was removed.

Every existing validator, report, row/count/key/hash, permission and staging check
passed. CSV bytes and hashes match across variants, repeats and the previous
reference within each engine. The 88 frozen-reference encoding tests remain;
22 focused protocol tests additionally cover pairing, provenance, paired
statistics, incomplete evidence, private failure reporting and cleanup.

Retain the guard: encoding wins 15/16 pairs; median paired encoding changes are
−4.499%, −4.873%, −3.846%, −5.944% for 100k ordinary/streaming and 750k
ordinary/streaming. Total API time wins 13/16 pairs, including every 750k pair.
The one slower ordinary encoding pair and the 100k streaming API increase of
8.800% remain in the record. RSS changes are mixed and do not establish a memory
improvement. Four pairs are a bounded local experiment; no confidence interval or
general export speed guarantee is claimed. Full tables, raw hashes and limits
are in [paired-benchmark.md](paired-benchmark.md).

Follow-up regression gates:

- Full suite with coverage: **2,877 passed, 10 skipped** in **78.05 s**;
  **92.0223%** statement coverage (**12,400 / 13,475**), above the 85% gate.
  Coverage JSON: `/private/tmp/apa-csv-paired-coverage.json`.
- Focused protocol, original benchmark and CSV equivalence tests:
  **128 passed** in **1.26 s**.
- Ruff across `src tests scripts`: passed. Mypy: passed for all 124 source files.
- Strict OpenSpec validation of `csv-encoding-performance`: passed.
- Strict MkDocs build: passed. Documentation regression tests after final
  report edits: **49 passed** in **1.40 s**. Final `git diff --check`: passed.
- Independent audit recomputed every arm/pair summary, both order subsets,
  stage sum, validator count, source map, output check and cleanup flag; it
  confirmed the keep decision. All historical artifacts and the original
  benchmark helpers remain byte-identical.

Commands:

```text
.venv/bin/python scripts/benchmark_paired_csv.py --output openspec/changes/csv-encoding-performance/paired-results.json
.venv/bin/python -m pytest -q tests/test_paired_csv_benchmark.py tests/test_public_csv_benchmark.py tests/test_csv_encoding_equivalence.py
.venv/bin/python -m pytest -q --cov=test_data_agent --cov-report=json:/private/tmp/apa-csv-paired-coverage.json --cov-fail-under=85
.venv/bin/ruff check src tests scripts
.venv/bin/mypy src
openspec validate csv-encoding-performance --strict
.venv/bin/mkdocs build --strict
.venv/bin/python -m pytest -q tests/test_documentation.py
git diff --check
```

The benchmark used local synthetic data only. No live database integration or
external provider was exercised; ten environment-gated tests remain skipped.
