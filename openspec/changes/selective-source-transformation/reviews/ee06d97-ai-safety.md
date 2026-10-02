# Independent AI re-review — numeric zero correction

- Reviewer: Boyle / CSV-Gate-1, agent 01a0dfa0-7f22-75d3-9b19-d181e11f187d.
- Date: 2026-09-28.
- Verified SHA: ee06d97d76ebd7d1434a81dad520efa91bef7ad1.
- Compared against: 1c5c905066c2ca573f878252289983f8dc716402.
- Scope: corrective union guard and direct/fallback regression variants only.

Disposition: High finding closed. Union of preserved and coincident-zero fields
rejects whole rows retaining source information through formatted preservation
and numeric-zero synthesis. No additional issue identified in corrective diff.

Checks: verified HEAD and runtime/test files against HEAD; static tracing of both
regressions; in-memory predicate check showing mixed full coverage rejects while
partial coverage alone does not. No suite, receipt or publication execution;
author's 237 tests and Ruff not independently rerun. Signature not independently
verified. Unrelated progress edits excluded. No writes or live data access.

Reviewer reported the prior evidence file absent. Author verified its full
repository path via git ls-tree at HEAD; this document records that discrepancy
without attributing an evidence-file inspection to the reviewer.

AI review only, not human approval or publication/activation authorization.
