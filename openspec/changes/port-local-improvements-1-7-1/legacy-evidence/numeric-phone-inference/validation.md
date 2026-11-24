# Verification: Numeric CSV Fields And Phone Inference

Completed 2026-11-22 with synthetic fixtures only. No source data, database
access, provider calls, release action or historical benchmark edits.

## Behavior And Safety

- All finite numeric evidence is accumulated across every nonempty row, not
  only the first 100 semantic samples. Neutral numeric columns retain integer
  or float type and no longer claim phone semantics or phone mask labels.
- The conservative content-sensitive flag remains independent. Ambiguous
  numeric content still has no raw categories, exact extrema or percentiles.
- Explicit phone names and nonnumeric formatted phones retain their previous
  semantics. SSN, payment-card and secret classification retains its priority;
  normalized exponent encodings cannot disclose their numeric bounds.
- Folder profiling now uses the unchanged single-CSV numeric-content policy,
  including its existing narrow negative-fraction exception. Strict shared
  detectors, generated-row privacy, masking and local-category guards are
  unchanged. Their frozen-policy equivalence tests still pass unchanged.
- Cache format 6 invalidates a matching old version-5 entry, recomputes corrected
  metadata and then reuses the new safe cache. Saved profiles/plans are not
  rewritten; reprofile them to obtain corrected inference.

## Executed Checks

- New `tests/test_numeric_phone_inference.py`: 17 focused cases covering four
  profiling views, public CSV/folder workflows, numeric inference, strong
  detections, late outliers, cache invalidation and deterministic generation
  of actual integer/float objects. Profile/spec payloads exclude sensitive
  input spellings. Numeric generation passes ordinary dataset validation.
- Focused regression selection: **144 passed** in 2.72 seconds, including CSV
  pipeline, detector and privacy equivalence, DuckDB/set profile equality,
  distinct overflow and domain-agnostic inference.
- Full suite: **2,176 passed, 10 skipped** in 81.59 seconds, with coverage above
  the existing 85% minimum. No skip was added by this change.
- Ruff over `src tests scripts`: passed.
- Mypy over 125 configured source files: passed.
- Strict MkDocs build, strict OpenSpec validation and `git diff --check`: passed.
- Independent read-only review found no actionable bug; additional bounded
  checks covered ten synthetic case groups across all four profiling views,
  including non-finite values and mixed columns.

An existing category/conditional-rule test used exponent notation that expands
to a nine-digit SSN candidate and previously escaped folder content checks.
Its ordinary numeric fixture now uses three-digit measures; its original
category/condition assertions remain. A separate new exponent-SSN regression
requires suppression in every profiling view rather than preserving that leak.

The large public CSV performance experiment was not rerun: this task changes
source-profile inference, while that experiment uses a fixed handwritten
specification. Earlier timing and source-fingerprint evidence remains immutable.
Corrected inferred specifications can intentionally generate different output
from an old false-phone specification; each corrected specification remains
deterministic with an explicit seed.
