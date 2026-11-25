# Privacy Validation Performance

## Status

Implementation and verification in progress, unreleased, 2026-11-21. This
internal execution change selects no version, tag or publication.

## Why

The [shared-validation benchmark](../shared-generation-validation/benchmark.md)
identified strict generated-row privacy as the largest remaining export stage.
The validator repeatedly infers the same field sensitivity for each row and
calls a string-only detector for actual non-string values. This work can be
removed without changing recognizable-sensitive-value detection.

## What Changes

- Prepare field names, types, semantic types and sensitivity once per entity in
  each privacy-validation call.
- Reject composite values before skipping actual non-string scalars, which the
  existing detector cannot classify and string namespace policy does not inspect.
- Preserve the content classifier for every eligible string, strict raw-value
  checking, report-only numeric decoding, error order and value-free failures.
- Verify safety and deterministic compatibility, then record fresh public CSV
  measurements separately from the shared-validation baseline.

## Safety And Compatibility

No detector policy, source-row policy, public signature, option, dependency,
artifact schema, generator algorithm, random-call order or seed changes. The
prepared plan is local to one invocation; no row verdict or mutable spec is
cached across calls. All existing generation, callback, revalidation and
publication boundaries continue to call the same privacy validator.
