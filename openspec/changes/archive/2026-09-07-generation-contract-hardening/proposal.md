# Change Proposal: generation-contract-hardening

## Summary

Correct six reproduced generation and validation defects: rejected constraints
execute, formula dependencies depend on list order, valid-mode failures can be
published, nullable foreign keys lose nulls, required identifiers pass with null,
and generated string lengths exceed their configured bounds. Revalidation must
also inspect row privacy rather than only the specification.

## Scope

Implement these corrections in the existing deterministic pipeline, with direct
API and adapter regression tests. Preserve schema version 1.0 and existing
command/tool shapes. Statistical synthesis, new integrations, and product pilots
are outside this corrective release.

## Safety And Compatibility

Keep source-row, database, filesystem, and provider boundaries intact. Share the
existing generated-value privacy policy between generation and validation; never
include offending values in errors. Explicit mixed/negative modes retain their
controlled-invalid reports. Inferred rules in an explicitly supplied spec remain
executable for compatibility; rejected rules and relationships do not execute.
Changed seeded values and newly rejected invalid bundles require migration notes.
Release through 1.3.2rc1 acceptance before a metadata-only 1.3.2 promotion.

## Completed Release Sequence

Published RC1 contained the corrective runtime. A pre-existing malformed SQL
property-test input surfaced during stable preparation, so the safety-test
correction passed a new RC2 acceptance cycle. Stable 1.3.2 promotes accepted
RC2 with metadata/documentation changes only; public verification passed.
