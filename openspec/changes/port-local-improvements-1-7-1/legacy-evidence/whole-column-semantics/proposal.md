# Whole-Column CSV Semantics

## Status

Implementation and verification completed, unreleased, 2026-11-22. The final
full suite passed: 2,228 tests, 10 skips. See [verification](validation.md).
This change selects no version, tag or publication.

## Why

CSV semantic inference currently combines a first-100-value sample with the
first recognizable sensitive value. A single email or phone can therefore
assign a whole column that semantic, and changing row order can change the
decision. Substring name hints also turn numeric fields such as `email_count`
into contact fields. Both effects can produce inappropriate generation specs.

## What Changes

- Use one deterministic semantic resolver for single-file and folder CSV
  profiling, including their batch helpers and streaming accumulators.
- Count detector outcomes over all nonempty values in the existing profiling
  pass without retaining additional raw values or serializing the counters.
- Require 80% content support for email, phone or SSN semantics; retain the
  existing any-secret priority and return no semantic for conflicting evidence.
- Split name hints into words, account for numeric role words and make resolved
  CSV semantics authoritative for type inference.
- Keep any-sensitive-content protection separate from semantic selection and
  invalidate older folder profiles through cache format 7.

## Safety And Compatibility

A rare sensitive value still makes the field sensitive and suppresses raw
categories and exact numeric summaries. Existing content classifiers,
conservative name-based sensitivity, strict generated-row checks, masking,
local-category guards and bounded numeric normalization retain their policy.

Only semantic, type and sensitivity decisions are invariant under row
permutations; existing reservoir statistics, category ordering and bounded
pattern samples can still change full profile serialization. An inferred
specification may intentionally change, while generation from the same corrected
specification remains deterministic with an explicit seed. Saved plans and
profiles are not rewritten in place. Historical benchmark evidence remains
unchanged. No dependency, CLI option or artifact field is added.
