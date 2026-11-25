# Generation Dispatch Performance

## Status

Completed on 2026-11-24, unreleased. Retain the shared dispatch change: all 32
paired public CSV runs and four smoke runs succeeded; generation/IPC improves in
16/16 pairs and total time in 15/16. The [benchmark](benchmark.md) records the
larger ordinary-path gain, smaller streaming gain and the observed 100k sampled
RSS increase. [Verification](validation.md) preserves exact values/states and
all safety checks. No general memory or speed guarantee is claimed.

## Why

The previous public benchmark spends about 31 seconds in ordinary generation at
750,000 rows × 25 fields. The shared field generator eagerly selects every
distribution type before dispatching on the field type. Most selections cannot
affect that field's result. Remove this measured repeated work before introducing
new prepared-generator machinery, caching or dependencies.

## What Changes

- Select numeric, boolean, date, datetime and string distributions only inside
  their existing type branches in the shared field generator.
- Preserve categorical precedence, early null/invalid/identifier/sensitive/provider
  handling, random/Faker call order, errors and all generation/validation checks.
- Compare against a frozen previous dispatch implementation, including complete
  ordinary and tiled results, state transitions and source-derived specifications.
- Run four adjacent AB/BA pairs per public CSV path at 100,000 / 750,000 rows ×
  25 fields, retaining all previous stage, memory, safety and byte-equality checks.

## Safety And Scope

No public signature, seed namespace, backend, dependency, source access, budget,
constraint solver, validator, privacy classifier or atomic writer changes. The
same shared generator serves every source-derived specification. Benchmark only
fictional data; retain every observation and preserve historical evidence.
