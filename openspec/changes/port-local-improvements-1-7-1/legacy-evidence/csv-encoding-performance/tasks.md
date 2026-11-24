# Tasks: CSV Encoding Performance

- [x] Profile bounded fictional CSV encoding and choose the smallest improvement
  supported by measurement.
- [x] Apply the change to the relevant ordinary/streaming encoding paths while
  retaining all formatting, formula, schema and exception behavior.
- [x] Add frozen-reference byte-equivalence and mutation regressions; retain
  source-variant, privacy, deterministic output, budget and atomic-write coverage.
- [x] Run focused and required regression, coverage, lint/type, documentation
  and strict OpenSpec checks; record anything not run.
- [x] Repeat both public CSV paths for 100,000 / 750,000 rows × 25 fields with
  three repetitions, complete checks, stage time, peak RSS and output hashes.
- [x] Independently audit implementation and raw evidence; document performance,
  privacy, deterministic compatibility and measurement limits.
- [x] Finalize status and verification evidence without modifying historical
  results, versioning or release state.
- [x] Freeze and verify before/after source copies, then run four adjacent
  alternating pairs for each public CSV path at 100,000 / 750,000 rows × 25 fields.
- [x] Compare paired stage times, total time and peak RSS with all existing
  checks; retain the guard and preserve every observation and historical artifact.

