# Independent AI safety review — numeric zero

- Reviewer: Boyle / CSV-Gate-1, agent 01a0dfa0-7f22-75d3-9b19-d181e11f187d.
- Date: 2026-09-28.
- SHA: 1c5c905066c2ca573f878252289983f8dc716402.
- Base: ebfab030fe081149d5394d91fb8159bf9545e01d.
- Scope: numeric-zero synthesis allowance, complete-row guard and tests only.
- Checks: verified SHA, static diff/contract/call-path inspection; fictional
  in-memory evaluation of changed predicate. No full executor or receipt test
  independently performed; author tests not rerun by reviewer.

## High: mixed formatted preservation and generated zero

Generated -0.00 -> 0.0 combined with preserved/formatted DATE retained every
field's information, but escaped both spelling comparison and the all-preserved
set check. Newly introduced interaction with zero allowance. Other scoped checks
found no additional discrepancy in type/shape binding, nonzero/text/bool rejection,
null handling or shared fallback routing.

Disposition: author reproduced with two full private-publication regressions,
direct synthesis and replace-text fallback, using fictional data and the existing
test-only TTY receipt fixture. Both failed before correction. Guard now checks
the union of preserved and coincident-zero fields. Executor suite: 237 passed;
Ruff passed. Independent verification of corrected exact SHA remains pending.

AI review, not human approval or public activation/release authorization.
