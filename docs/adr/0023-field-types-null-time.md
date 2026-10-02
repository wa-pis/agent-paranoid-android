# ADR-0023: Make matching, nulls and temporal conversion explicit per field

- Status: Accepted — owner decisions 2026-09-27; implementation coverage varies.
- Recorded: 2026-09-29. This is the recording date, not an invented original approval date.
- Authority and implementation boundaries: see Evidence below and the [register conventions](index.md#status-and-authority).

## Context

CSV spelling, native numeric values, null and timezones cannot be equated safely by implicit coercion.

## Decision

Choose literal or typed matching per field, independent of input/output format. Literal text preserves spelling; typed values compare under the selected type. Native numbers/dates require explicit formatting for text matching, never automatic str(). Output formatting is a separate choice.

Empty CSV cells are empty strings. Null uses an optional explicit nonempty marker, with separate source/output/mapping settings bound to policy bytes. A literal colliding with the output marker rejects; quoting is not an escape. Native null remains distinct from empty text.

Temporal format describes input and output_format describes rendering. DATE needs no timezone. Explicit DATETIME conversion uses source_timezone/target_timezone when needed, never guessed UTC. Unconditional replace_text emits its literal unchanged, even if it resembles a date.

## Alternatives and consequences

Automatic date/null detection or native stringification is convenient but changes keys and values invisibly. Formats and zones are restricted/validated by the supported implementation; choosing metadata alone does not authorize preservation.

Implicit same-instant DATETIME key equivalence and formula-null semantics are not settled by this decision; see the open-question register. Private code behavior is not authority to extend it.

## Evidence

Sources: [dated owner decisions](https://github.com/wa-pis/agent-paranoid-android/blob/637065966c12584e11c9b437c1e8b8f8d708c0df/openspec/changes/selective-source-transformation/policy-contract.md), [transformation delta](https://github.com/wa-pis/agent-paranoid-android/blob/637065966c12584e11c9b437c1e8b8f8d708c0df/openspec/changes/selective-source-transformation/specs/selective-source-transformation/spec.md).
Executable anchors: [policy](https://github.com/wa-pis/agent-paranoid-android/blob/637065966c12584e11c9b437c1e8b8f8d708c0df/tests/test_transformation_policy.py), [CSV](https://github.com/wa-pis/agent-paranoid-android/blob/637065966c12584e11c9b437c1e8b8f8d708c0df/tests/test_transformation_csv.py), [execution](https://github.com/wa-pis/agent-paranoid-android/blob/637065966c12584e11c9b437c1e8b8f8d708c0df/tests/test_transformation_execute.py).

## Revisit when

A new coercion, marker escape or temporal-key equality rule requires explicit agreement and cross-format tests.

