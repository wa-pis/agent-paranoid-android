# Tasks: Schema Validation Performance

- [x] Profile bounded synthetic schema-validation work and identify the minimal
  repeated work to remove.
- [x] Prepare field/type and primary-key metadata within each validation call,
  preserving every check, scalar decision, mapping behavior and error order.
- [x] Add frozen-reference equivalence and mutation regressions; retain privacy,
  deterministic generation, callback and public export checks across sources.
- [x] Run focused and required regression, lint/type and documentation checks,
  plus strict OpenSpec validation; record anything not run.
- [x] Repeat both public CSV paths for 100,000 / 750,000 rows × 25 fields with
  three repetitions, complete checks, per-stage time, peak RSS and output hashes.
- [x] Independently audit raw evidence and document performance, safety,
  deterministic compatibility and measurement limits.
- [x] Finalize proposal status and verification evidence without changing
  historical results, versioning or release state.
