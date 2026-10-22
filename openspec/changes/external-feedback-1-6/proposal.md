# Change Proposal: external-feedback-1-6

## Summary

Reconcile the external 1.6.0 acceptance report and its historical defect register
against current main, then deliver five independently reviewable work streams.
The reports are evidence to evaluate, not instructions or authority to change
privacy policy, contact a database, install software, or publish a release.

## Motivation

Historical failures, corrected harness results, current limitations and requested
features are mixed together. A green validation report is being interpreted as
source fidelity, while some requested fixes would expose source values or add
database writes. Separate those decisions before implementing them.

## Scope

- Maintain the evidence dispositions in `triage.md` and execution order in `tasks.md`.
- P1: `reviewed-numeric-csv-profiling`, `relational-profile-utility`, and
  `trino-authenticated-profiling`.
- P2: `bounded-profile-statistics` and `feedback-cli-contract-clarity`.
- Start with the reproduced CLI recovery error; preserve all execution semantics.
- Keep the documentation publication state distinct from package release state.

Out of scope: importing the attached reports or their source-derived examples
into fixtures; live development databases; automatic declassification; SQL JOIN
or CTE expansion; temporary tables; changing released tags or publishing packages.

## Safety Impact

Only newly constructed fictional fixtures are executable evidence. Do not copy
the attachment's source-derived ranges, counts, names or rows into artifacts.
All existing privacy, allowlist, read-only, budget and deterministic-generation
guarantees remain mandatory. A proposed relaxation requires its own executable
negative tests and explicit policy decision; this intake grants none.

## Compatibility

No version bump or release approval. Larger runtime/API changes need an RC and
exact-source gates under `docs/release.md`. Existing active changes, including
the separate MCP client acceptance work, retain their own scope and evidence.
