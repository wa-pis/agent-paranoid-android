# Independent AI safety review — SQL aggregate policy

- Reviewer: Boyle / CSV-Gate-1, independent AI subagent
  `01a0dfa0-7f22-75d3-9b19-d181e11f187d`; not implementation author.
- Date: 2026-09-28.
- Runtime SHA: `4876fcbd4916499d38bd1fa874292dbe46e344db`.
- Base: `440101eb54d30fd300c189d27d6d1025c6bb501b`.
- Final head inspected: `f14dc5c8111be8897779af029fbcf1a6892edac3`.
- PR: https://github.com/wa-pis/agent-paranoid-android/pull/590
- Scope: shared SQL authorization diff, aggregate shapes, column/sensitivity
  identity, COUNT-star, unchanged adapter/profile/budget consumers and tests/docs.

## Findings and disposition

High, open: table column-alias lists can remap a permitted reference onto an
unauthorized sensitive physical column. With fictional physical column order
`(private_token, status)`, `AS o(status, unused)` makes `o.status` refer to the
first physical column. Both grouped COUNT and MIN variants passed PostgreSQL
and Trino local authorization. Existing alias handling predates this patch but
the new aggregate path inherits the bypass. Reject column-alias lists or resolve
physical lineage before authorization. Blocks clean safety disposition.

Low, open: `COUNT(* REPLACE (amount AS status))` passed the bare-star exception.
Unsupported decorated star reaches the adapter boundary. No execution/disclosure
demonstrated; require an undecorated star.

Author disposition: correcting both via shared pre-authorization rejection,
with regressions for both adapters and both aggregate/non-aggregate paths.
Independent corrective review still required; findings are not yet closed here.

## Reviewer checks and limitations

Verified runtime Git blobs identical between runtime SHA and final head.
Inspected changed runtime/tests/docs/specs and relevant consumers. Ran 60
fictional in-memory parser/authorization cases plus four alias-list probes with
SQLGlot 30.13.0; only query-file reading was substituted. No suite rerun, writes,
network, DB/provider access or activation. Author checks are not independent
evidence. Used read-only fallback because persisted security-scan artifacts
conflicted with the no-writes scope. No formal scan artifacts generated.

AI review only; not human GitHub approval or public activation authority.
