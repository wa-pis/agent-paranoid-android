# Numeric CSV Fields And Phone Inference

## Status

Implementation and verification completed, unreleased, 2026-11-22. The full
suite passed with 2,176 tests and 10 skips. See [verification](validation.md).
This change selects no version, tag, release or publication.

## Why

The conservative content detector recognizes bare digit strings and dotted
numeric strings as possible phone numbers. Profiling currently turns that
weak signal into a phone semantic type, replacing ordinary numeric fields
with string fields and causing generated values to become phone numbers.
Folder profiling also bypasses the existing CSV numeric-content checks, making
single-file and folder decisions inconsistent for negative fractional measures.

## What Changes

- Keep a neutral all-finite-numeric CSV column numeric and omit the inferred
  phone semantic when phone is the only weak content classification.
- Preserve explicit phone names and nonnumeric formatted phones, stronger
  SSN/card/secret classifications, conservative sensitivity and exact-summary
  suppression for ambiguous numeric content.
- Apply the existing CSV numeric-content normalization consistently to folder
  profiling, including its narrow negative-fraction exception.
- Increment the folder profile cache format from 5 to 6 so existing false-phone
  profiles are recomputed.

## Safety And Compatibility

This corrects profile type and semantic inference; it does not declassify an
ambiguous phone-like value as safe. Strict content detection, masking,
local-category checks and generated-row privacy keep their existing policy.
No new numeric-content exemption, dependency, raw-value artifact or random call
is added. Reprofiling can intentionally change profile fingerprints and inferred
specifications; previously saved plans and artifacts are not silently rewritten.
Historical benchmark evidence remains unchanged.
