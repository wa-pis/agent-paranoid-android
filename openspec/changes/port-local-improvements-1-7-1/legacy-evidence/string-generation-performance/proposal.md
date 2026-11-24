# String Generation Performance

## Status

Evaluated on 2026-11-24. Reject the runtime candidate and keep the previous
string generator. All 32 paired public CSV runs and four smoke runs passed;
the measured benefit is too small and inconsistent to justify the compatibility
code. Retain the evidence, regression tests and reusable benchmark reference option.
This internal experiment is unreleased.

## Why

The shared random-string helper spends time yielding each character through a
generator expression into `str.join`, which already materializes that iterable.
A bounded nine-pair experiment supported trying only that collection step.
The expected benefit was modest; public measurements must justify its cost
without changing random choices or compatibility.

## What Was Evaluated

- Use a list comprehension for the existing per-character `rng.choice` calls.
  Preserve dynamic method/alphabet lookups, length selection and synthetic prefixes.
- Preserve the previous generator expression's PEP 479 conversion for a custom
  RNG's `StopIteration`; exceptions outside character collection remain unchanged.
- Reuse the existing paired benchmark driver with an explicit reference artifact,
  retaining the old default and all measurement, validation and audit helpers.
- Compare four adjacent AB/BA pairs for each CSV path at 100,000 / 750,000 rows
  × 25 fields. Preserve every observation, output hash and memory metric.

## Safety And Compatibility

Only `synthetic_string` differed in the measured candidate. Its change is reverted;
the selected runtime exactly matches the frozen previous source. No public signature, dependency,
source access, cache, distribution policy, provider priority, scalar choice,
validation, privacy classifier, budget or atomic writer changes. Ordinary and
tiled generation retain their separate namespaces and exact previous values.
Shared behavior applies to every source-derived specification. See
[benchmark.md](benchmark.md) for all stages and memory measurements, and
[validation.md](validation.md) for the decision, checks and replay proof.
