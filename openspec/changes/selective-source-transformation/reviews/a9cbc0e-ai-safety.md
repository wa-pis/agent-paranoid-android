# SQL adapter independent AI review

Reviewer Boyle / CSV-Gate-1, agent `01a0dfa0-7f22-75d3-9b19-d181e11f187d`.
Date: 2026-09-27, Europe/Samara. SHA `a9cbc0e0d1172bfdeb54210bac7ea5926a019cf3`,
base `902a5f639a9198d27c1135031bc0e9ffb379ff48`.
Scope: new SQL adapter, output binding, normalization, equality/privacy,
budgets and temporary publication. Evidence submission
`01a0e2fd-208c-7550-8392-4c161c429777`,
[reviewer](codex://threads/01a0dfa0-7f22-75d3-9b19-d181e11f187d).

## Findings

1. High: failed source parsing under output format disabled final row equality.
   Fictional ISO source -> DMY replacement -> DATE restored source while source
   comparison failed. Fix: compare cells independently; only a proven differing
   cell establishes row change. Unresolved comparisons alone reject.
2. High: normalized FLOAT could introduce a sensitive-looking final value after
   intermediate checks (fictional 1.234567e6 -> 1234567.0). Fix: apply existing
   privacy detector to normalized values before accepting output.

Author added regression tests and fixed both. Independent re-review by the same
reviewer on 2026-09-27 verified SHA
`ff6790c496c8ad3fa6cdd3df37a256c2f7dfe127` against the initial reviewed SHA.
Both High findings resolved; no additional changed-scope issue identified.
Re-review submission: `01a0e302-17fd-7731-83df-e8ba84962a23`.
Reviewer inspected the static diff, surrounding control flow and regression
assertions; tests were not independently rerun. The progress-only edit was
excluded. No edits, network, database access, receipts or publication occurred.
31 SQL-focused tests passed; changed Ruff/mypy and diff checks passed.
These conservative guards do not establish complete cross-format acceptance.

Reviewer inspected immutable diff and ran fictional in-memory probes only.
No writes, receipt issuance, publication, network, database or real data.
Author's 380 checks were not independently rerun; PostgreSQL execution and
filesystem fault behavior were not exercised. AI review is not human approval,
public activation or release authorization.
