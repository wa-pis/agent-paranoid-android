# CSV-folder distinct tracking

## Summary

Remove the separate 10,000-unique-value ceiling from CSV-folder profiling.
Complete folder profiles count all normalized non-null values allowed by the
existing input and work budgets, using internal SHA-256 fingerprints.

## Scope and compatibility

New folder profiles report exact distinct ratios and can infer identifier pools
or key candidates above the former ceiling. Profile cache format 5 invalidates
older cached counts. Existing saved profiles remain readable; legacy
`lower_bound` evidence keeps its conservative semantics until explicitly
reprofiled. Profile/spec schema versions and public command names remain.

The generation row cap, database result caps and single-file CSV profiler's
separate fingerprint cap are unchanged. No release or publication is claimed.

## Safety and resources

Retain existing input-byte, row, cell, sample and deadline budgets. Fail closed
on budget exhaustion without publishing a partial profile. Memory scales with
distinct fingerprints; this change does not promise unlimited input or constant
memory. Fingerprints and source rows are not persisted or returned. Existing
PII masking, source-row non-reuse and local-category boundaries remain.
