# Tasks: String Generation Performance

- [x] Freeze the previous source and profile bounded fictional generation.
- [x] Apply the smallest compatible string-generation candidate for measurement.
- [x] Verify frozen-reference strings, values/errors/states, dynamic RNG behavior,
  ordinary/tiled output, mutation visibility and source-independent policy.
- [x] Run four paired before/after repetitions for both public CSV paths at
  100,000 / 750,000 rows × 25 fields with unchanged checks and stage/RSS metrics.
- [x] Independently audit the evidence; reject and revert only the runtime
  candidate because its public benefit does not justify its compatibility code.
- [x] Complete regression, coverage, lint/type, documentation and OpenSpec gates;
  record limits and reproducible evidence while preserving historical results.
