# ADR-0030: One generation contract for every source and output

- Status: Accepted — owner direction; implementation evidence is tracked below.
- Recorded: 2026-10-16.
- Authority: owner's explicit requirement for a complete source/output matrix,
  uniform DatasetSpec field types/options and uniform business rules.

## Context

Source acquisition supplies safe evidence, not a separate generation language.
## Decision

Every supported source reaches the same reviewed DatasetSpec and deterministic
engine. Output adapters encode logical values; they do not choose rule or setting
semantics. New sources and formats extend the matrix and its regression tests.
Source observations may differ, and absent information still requires review.

Use one common contract for all FieldType values, distributions, generation and
validation options, relationships and business rules. Preserve decimal precision,
typed conditions and null semantics after saving/reloading. Do not declare a
matrix cell implemented solely because the common engine exists.

## Alternatives and consequences

Keep adapter-specific parsing, access control and physical encoding at the
boundaries. Native Arrow columns remain the default. Explicit marked scalar
encodings preserve wide integers, timestamp offsets and requested malformed
negative cells where Arrow types cannot. CSV encoding is manifest-bound and
legacy unmarked artifacts keep their behavior. This extends ADR-0004's reviewed
contract and ADR-0013's shared application policy to every source/output pair. Retain read-only database budgets and source-free synthesis. This
record grants no data access, transformation activation or release approval.
Independent generators for each source/output pair duplicate rule policy and
permit semantic drift. One reviewed contract keeps safety checks common while
allowing explicit physical encodings at the boundary.

## Evidence

The maintained [source/output matrix](../reference/source-output-matrix.md)
describes the public contract. `openspec/changes/source-output-contract-parity`
records requirements. Executable anchors are `tests/test_source_output_matrix.py`,
`tests/test_portable_scalar_artifacts.py` and the existing universal business-rule,
source, interface, privacy and budget suites. Database evidence is fictional,
not live deployment acceptance.

## Revisit when

A new source, format, field type or option must extend the executable matrix.
Changed physical encodings need explicit version markers and migration guidance;
a different logical rule meaning requires a successor decision.
