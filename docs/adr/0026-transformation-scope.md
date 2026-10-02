# ADR-0026: Keep internal formula recomputation out of the 1.6 RC scope

- Status: Accepted — owner scope correction 2026-09-28.
- Recorded: 2026-09-29. This is the recording date, not an invented original approval date.
- Authority and implementation boundaries: see Evidence below and the [register conventions](index.md#status-and-authority).

## Context

Earlier implementation/planning expanded SQL aggregate requirements into an internal financial formula engine, creating unrelated blockers.

## Decision

For this RC, aggregates belong to authorized SQL queries and their result columns are ordinary transformation inputs. Do not require SQL-to-formula translation, financial total/balance recomputation or formula-null decisions to complete 1.6.

Keep existing private derive code/tests, but do not activate them publicly or use them to infer new scope. Existing source-free generation/rule capabilities are unaffected. Key mappings, one-to-one semantics, exact types, privacy and authorized SQL budgets remain required. Reconcile original client findings 18/23 separately.

## Alternatives and consequences

Deleting existing code is not required. Treating every prototype or suggested feedback item as an accepted feature caused the expansion. Old plan/design/safety text about recomputed totals is historical where it conflicts with this explicit correction.

This is scope correction, not a relaxation of validation for any feature that actually executes.

## Evidence

Sources: [owner scope correction](https://github.com/wa-pis/agent-paranoid-android/blob/637065966c12584e11c9b437c1e8b8f8d708c0df/openspec/changes/selective-source-transformation/policy-contract.md), [resumption plan](https://github.com/wa-pis/agent-paranoid-android/blob/637065966c12584e11c9b437c1e8b8f8d708c0df/openspec/changes/selective-source-transformation/resumption-plan.md), [client acceptance](https://github.com/wa-pis/agent-paranoid-android/blob/637065966c12584e11c9b437c1e8b8f8d708c0df/openspec/changes/selective-source-transformation/client-acceptance.md).
Existing private coverage: [exact formulas](https://github.com/wa-pis/agent-paranoid-android/blob/637065966c12584e11c9b437c1e8b8f8d708c0df/tests/test_transformation_exact_formula.py), [rounding](https://github.com/wa-pis/agent-paranoid-android/blob/637065966c12584e11c9b437c1e8b8f8d708c0df/tests/test_transformation_decimal_rounding.py).
Supersedes the earlier assistant-added formula release requirement, not source-free rule support.

## Revisit when

Only an explicit later feature decision can bring internal formula execution into the public transformation scope.

