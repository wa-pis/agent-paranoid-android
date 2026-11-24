# Privacy Signal Strength Verification

Implemented and locally verified, unreleased, 2026-11-22.

## Behavior

Weak SSN digits, Luhn checksums, entropy and JWT shapes remain sensitive.
They establish semantics only with compatible word-based name context and at
least 80% support over the full nonempty population. Structured SSN formatting
uses the same threshold; strong credential formats retain any-occurrence
priority. Unknown semantics never permit raw categories or exact sensitive
numeric summaries.

The four CSV views share fixed signal counters and retain the existing bounded
numeric normalization. Trino and legacy top-value adapters use validated integer
weights and full non-null counts without expanding frequencies into rows.
Partial top lists use the full denominator; unknown, invalid or contradictory
coverage permits only strong credential priority. Explicit saved semantics are
preserved. No SQL, allowlist, query count or database budget changed.

Folder cache format 8 rejects earlier entries. Saved profiles and plans are not
rewritten; reprofile sources to obtain corrected inference.

## Synthetic Accuracy Corpus

The 67 columns in `tests/fixtures/privacy_semantic_accuracy.json` have manually
assigned semantic and conservative privacy labels, independent of classifier
outputs. Cases cover positive examples, hard negatives, misleading names,
mixed columns, threshold boundaries and late evidence. All data is synthetic.

The baseline is the exact local pre-task snapshot, including prior uncommitted
whole-column semantics work, rather than repository HEAD. Source and fixture
SHA-256 values, aggregate metrics and scope are recorded in
[`accuracy-results.json`](accuracy-results.json). Metrics are computed through
`accuracy_report` in `tests/test_privacy_semantic_accuracy.py`.

| Family | Cases | Semantic false positives before → after | Expected semantics found after |
| --- | ---: | ---: | ---: |
| SSN | 15 | 6 → 0 | 7 / 7 |
| Cards | 21 | 11 → 0 | 9 / 9 |
| Entropy / JWT | 14 | 7 → 0 | 7 / 7 |
| Strong credentials | 10 | 0 → 0 | 7 / 7 |
| Benign | 5 | 0 → 0 | — |
| Email / phone | 2 | 0 → 0 | 2 / 2 |
| Total | 67 | 24 → 0 | 32 / 32 |

Semantic precision on this corpus rises from 57.14% to 100%; recall remains
100%. Privacy labels have zero false positives and false negatives before and
after under the deliberately conservative policy. These bounded synthetic
results do not estimate real-world accuracy or prevalence.

## Safety And Determinism

- All four CSV views match the labels under original, reversed and fixed-seed
  shuffled row orders. Semantic/type/sensitivity decisions remain invariant;
  existing bounded distribution ordering is not claimed to be byte-identical.
- Weak evidence still rejects raw local categories and sensitive generated-row
  content. Public CSV/folder profiles and inferred specs contain no source
  spellings; repeated generation with seed 42 matches and passes validation.
- Independent differential checks against the pre-task snapshot cover 14,054
  strings and 15 other values: zero raw/CSV type-tag or exception mismatches.
  Another 700 synthetic groups show no sensitivity downgrade, sensitive-bound
  or category leak, or semantic/type/sensitivity permutation mismatch.
- Aggregate review checks 17 scenarios across two adapters and two orders
  (68 checks). The persisted 83 aggregate regressions cover weighted thresholds,
  missing/partial/malformed/conflicting coverage, safe errors, explicit semantics
  and rare strong evidence. Numeric counts are never expanded into rows.

## Executed Checks

- Focused privacy, semantic, CSV, distinct-tracking and aggregate regressions:
  **370 passed** in 2.43 seconds.
- Full suite with coverage: **2402 passed, 10 skipped** in 72.41 seconds;
  line coverage **91.87%** (12,299 / 13,387 statements).
- `ruff check src tests scripts`: passed.
- `mypy src/test_data_agent`: passed, 124 source files.
- Strict MkDocs build, strict `openspec validate privacy-signal-strength`,
  and `git diff --check`: passed.
- Independent code review: no remaining actionable findings.

Live database integration and performance benchmarks were not run. No live
source data or external AI provider was used. This change makes no performance
or real-world accuracy claim and does not select a release version or publish.
