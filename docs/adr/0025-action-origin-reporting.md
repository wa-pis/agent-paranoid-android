# ADR-0025: Report executed cell origins rather than value equality

- Status: Accepted — owner decision 2026-09-28; private manifest v2.
- Recorded: 2026-09-29. This is the recording date, not an invented original approval date.
- Authority and implementation boundaries: see Evidence below and the [register conventions](index.md#status-and-authority).

## Context

Equality cannot tell whether a value was preserved, replaced by an equal value or independently generated.

## Decision

Track the actual branch for each output cell: replacement, synthetic or original. Mapping/literal replacement and explicit type/format transformation are replacement even if values coincide. Generated values remain synthetic after formatting. Unmatched rules use the origin of their actual fallback; preserved null is original.

Report aggregate counts/shares only. Dropped cells are separate and excluded from the output-cell denominator; empty output shares are null. Physical encoding/quoting alone does not change origin. Private manifest v2 uses provenance rather than legacy retention.

## Alternatives and consequences

The earlier equality-based user report is superseded. Equality-based safety checks are not removed: reporting never authorizes preservation, copying or anonymity claims. Independently rounded percentages may not sum to exactly 100; do not falsify counts to hide rounding.

## Evidence

Sources: [owner provenance decision](https://github.com/wa-pis/agent-paranoid-android/blob/637065966c12584e11c9b437c1e8b8f8d708c0df/openspec/changes/selective-source-transformation/policy-contract.md), [report implementation](https://github.com/wa-pis/agent-paranoid-android/blob/637065966c12584e11c9b437c1e8b8f8d708c0df/src/test_data_agent/core/transformation_report.py).
Executable anchors: [report tests](https://github.com/wa-pis/agent-paranoid-android/blob/637065966c12584e11c9b437c1e8b8f8d708c0df/tests/test_transformation_report.py), [execution provenance](https://github.com/wa-pis/agent-paranoid-android/blob/637065966c12584e11c9b437c1e8b8f8d708c0df/tests/test_transformation_execute.py).
Supersedes the earlier unchanged-percentage narrative, not a previous numbered ADR.

## Revisit when

Any new action needs a defined origin classification and execution tracking before it appears in the user report.

