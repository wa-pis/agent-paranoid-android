# Change Proposal: controlled-relational-scenarios

## Status
Implementation candidate following relational-profile-utility R6. The isolated
candidate registers reviewed DatasetSpec declarations across generation and
mandatory validation/writers. Public delivery still requires full candidate
gates and green exact-head CI/merge. No package release is requested.

## Problem and current support
Valid FK assignment binds generated child rows to generated parent keys.
Existing mixed/negative business-rule generation can create synthetic missing
parent references, with seeded row selection and validation evidence. Its
invalid ratio is not an exact orphan count, targeted edge selector or fan-out
histogram. Ordinary assignment is round-robin; source fan-out remains unmeasured.

## Proposed scope
An explicit reviewed synthetic scenario would target one active declared FK by
its full parent/child field tuple. Optional exact orphan count applies only to
eligible non-null generated children and requires controlled-invalid mode.
A separate optional fan-out allocation specifies bounded generated child counts
per generated parent ordinal. Its sum must equal eligible non-null non-orphan
children. Neither setting changes nullable counts or silently expands datasets.

Both settings bind to the effective spec and resolved entity sizes. Generated
parent ordinals select synthetic keys only; no source key, row mapping or source
histogram is accepted. Duplicate targets, rejected/unknown edges, impossible
one-to-one allocations and conflicting rules reject before generation/publication.

## Safety and compatibility
Omitted settings retain seeded output and existing --count/ratio behavior.
Valid mode rejects requested orphans rather than weakening FK validation.
Controlled orphans produce expected invalid evidence, never a successful valid
report. Fan-out checks evaluate generated output and do not imply source fidelity.
All planning, allocation, mutation and evidence use existing row/byte/work/time
budgets and atomic publication. Schema/API/CLI design and RC evidence must precede
public activation. No database queries or source authorization changes are needed.
