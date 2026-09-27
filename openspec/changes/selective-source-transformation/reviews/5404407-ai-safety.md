# Nullable CSV — independent AI review

- Reviewer: Boyle / CSV-Gate-1, agent `01a0dfa0-7f22-75d3-9b19-d181e11f187d`.
- Date: 2026-09-27, Europe/Samara.
- Reviewed SHA: `540440742e907e41b5e798577d269537f6a45a19`.
- Base: `84659f98af90ad00ad7dfd2f716edff764ac9e6c`.
- Scope: nullable CSV diff, profiling, receipts, mappings, synthesis,
  preservation and formula boundary; prior temporal findings excluded.
- Evidence: reviewer submission `01a0e2ae-d133-7e20-a95a-cabc95ff9778`,
  [reviewer task](codex://threads/01a0dfa0-7f22-75d3-9b19-d181e11f187d).

## Finding and disposition

High: skipping source null markers also skipped positive content-sensitivity
evidence. An email-shaped fictional marker could change a sensitive field into
a preservation-eligible field. Receipt remained mandatory; no raw-email output
was demonstrated. Fix: observe sensitivity independently before excluding a
marker from null/type statistics. Regression covers exact and whitespace-padded
fictional email markers, requiring sensitive classification and preserve denial.
Author reproduced failure before fixing; independent re-review pending.

Reviewer also noted malformed rows reach review but are rejected by executor;
this inherited preflight gap was not a new execution bypass. No other changed-
scope receipt, whole-row or output-sensitivity regression found.

## Checks and limits

Reviewer inspected immutable diff and tests and ran fictional in-memory
profiling/canonicalization and malformed-row probes. No receipt issuance,
publication, edits, network or real data. Author's 323 tests/Ruff/mypy/OpenSpec
were not independently rerun. Author fix checks: 41 source/profiler tests,
Ruff/mypy passed; then both exact/padded marker regression cases passed.

This is AI conformance review, not human/GitHub approval, public activation,
or release authorization.
