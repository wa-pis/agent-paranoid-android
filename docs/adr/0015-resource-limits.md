# ADR-0015: Make budgets explicit, separate and actionable

- Status: Accepted — baseline plus owner capacity decision on 2026-09-28.
- Recorded: 2026-09-29. This is the recording date, not an invented original approval date.
- Authority and implementation boundaries: see Evidence below and the [register conventions](index.md#status-and-authority).

## Context

Hard-coded helper ceilings and borrowed profiling limits cannot establish end-to-end transformation capacity. Raising disclosure budgets to fit a large dataset would weaken a different boundary.

## Decision

Bound bytes, rows, columns, cells, scalar width, parsing complexity, expansion and cumulative work/time at their owning stages. Distinguish input/result/output/transport budgets and source-free profiling from transformation capacity. Fail closed without silent truncation or automatic limit increases.

Transformation target: 1,000,000 rows × 100 columns; required fictional acceptance: 300,000 × 50. Arbitrary-width values still must fit byte/time limits. Support session/run and saved behavior-profile settings. Errors distinguish requested_above_limit from actual limit_exceeded and include safe dimension, amount, threshold, units, origin and supported recovery settings. Invalid configuration is separate.

## Alternatives and consequences

Removing caps or increasing only one constant does not meet the decision. Adding unapproved hard-RSS/exact-wire guarantees is also not selected. Decoded payload measurements and cooperative deadlines must not be described as stronger guarantees.

The private installed CSV replacement route has 300k×50 evidence; SQL throughput, all routes and public activation are not thereby accepted. Local query-worker changes remain implementation work, not a released contract.

## Evidence

Sources: [configuration](../reference/configuration.md), [operational budgets](../operations/resource-budgets.md), [owner capacity contract](https://github.com/wa-pis/agent-paranoid-android/blob/637065966c12584e11c9b437c1e8b8f8d708c0df/openspec/changes/selective-source-transformation/policy-contract.md).
Evidence: [CSV scale acceptance](https://github.com/wa-pis/agent-paranoid-android/blob/637065966c12584e11c9b437c1e8b8f8d708c0df/openspec/changes/selective-source-transformation/csv-scale-acceptance.md); [limit tests](https://github.com/wa-pis/agent-paranoid-android/blob/637065966c12584e11c9b437c1e8b8f8d708c0df/tests/test_transformation_input_limits.py).

## Revisit when

Any capacity change needs end-to-end evidence and separate disclosure review; defaults, supported capacity and measured capacity must stay distinguishable.

