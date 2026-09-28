# Independent AI corrective review — SQL aggregate policy

- Reviewer: Boyle / CSV-Gate-1, independent AI subagent
  `01a0dfa0-7f22-75d3-9b19-d181e11f187d`; not implementation author.
- Date: 2026-09-28.
- Exact SHA: `16eece3c9da8a92656fc423b8049a140045a5586`.
- Compared against: `f14dc5c8111be8897779af029fbcf1a6892edac3`.
- PR: https://github.com/wa-pis/agent-paranoid-android/pull/590
- Prior findings: [initial review](4876fcb-ai-safety.md).

## Disposition

Both findings closed; no additional issue identified in the corrective scope.

High physical-column remapping: shared inspection rejects table column-alias
lists before authorization (sql_query_source.py lines 237–239 at reviewed SHA).
Grouped, MIN and ordinary SELECT reproducers reject for both adapters; ordinary
table aliases remain accepted.

Low decorated COUNT-star: modifiers on every Star node reject (lines 240–241).
COUNT-star REPLACE/EXCEPT and projection-star REPLACE probes reject; bare
COUNT(*) and authorized wildcard expansion remain accepted.

## Independent checks and limitations

Verified exact HEAD and inspected runtime/tests/guidance/persisted evidence and
example assertion corrections. Independently ran 20 fictional in-memory cases
with SQLGlot 30.13.0, all passed; only query-file reading was substituted.
Runtime, tests and examples matched HEAD; unrelated progress.md edits excluded.
No suite reruns, writes, network, live database or publication. Author checks
and CI were not independently verified. Read-only changed-scope review only.

AI evidence, not human GitHub approval or independent merge/activation authority.
