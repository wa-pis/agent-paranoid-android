# Port Local Improvements To 1.7.1

## Why

The local profiling, privacy and generation improvements were developed on an
older branch. Port their behavior onto the exact published 1.7.1 tree while
retaining every released contract, security boundary and deterministic engine.

## What Changes

- Merge shared privacy/semantic inference and bounded exact CSV distinct counts.
- Adapt generation, validation and CSV optimizations to DatasetSpec 1.1 and the
  released scalable, relational, DECIMAL, rule and transformation workflows.
- Preserve local opt-in tiled generation/export capabilities without changing
  the existing release engines or their seed namespaces.
- Retain regression and historical benchmark evidence with explicit provenance;
  old timings do not establish performance against 1.7.1.

## Safety

No source-row reuse, database permission expansion, provider calls or publication.
Existing local transformation approval gates and all released privacy, budget,
validation and atomic-publication boundaries remain in force.

## Impact

Shared profiling/privacy policy, exact distinct storage, optional generation and
CSV export, deterministic validation/calculation internals, dependency metadata,
focused regression tests and current guides. DatasetSpec remains at schema 1.1;
the package version remains 1.7.1 on this development branch. Publication and
release qualification require a separately authorized candidate.
