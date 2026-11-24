# Validation consistency hardening

## Summary

Make DatasetSpec validation agree across equivalent in-memory, JSON and CSV
values. Preserve integer precision and order formula/aggregate dependencies.
Implementation is local; no release or publication is claimed.

## Scope and compatibility

- Normalize validation views by declared field type without mutating input rows.
- Report malformed row shapes and composite keys without backend exceptions.
- Share numeric comparison and preserve integer sum/count precision.
- Order formula and aggregate writers by dependencies and reject cycles/conflicts.

Public names, schema version, report sections, validation flags and explicit
tolerances remain. Previously misvalidated inputs may now fail. Existing mixed
and negative generation semantics remain; no general constraint solver, decimal
field type, database access or new dependency is introduced.
Temporal/conditional repairs join the dependency graph; static cycles are rejected
even if a previous declaration order happened to converge. Review this stricter
compatibility behavior as release-candidate work before publication.

## Safety

Preserve unconditional post-generation privacy checks, approval fingerprints,
source-row non-reuse checks and atomic publication. Use synthetic test fixtures
only. Invalid inputs produce value-free diagnostics.
