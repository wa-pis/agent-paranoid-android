# Tasks
- [x] Specify optional typed formula predicate, null/missing semantics and assign/check order.
- [x] Define eligible/evaluated/skipped/failed evidence and compatible omitted-predicate serialization.
- [x] Reuse existing predicate and DECIMAL/literal/privacy enforcement without widening the expression AST.
- [x] Implement deterministic conditional formulas with shared work/deadline budget and conflict preflight.
- [x] Add fictional EAV target-model examples with bounded vocabulary, duplicate/null policies and generated key domains.
- [x] Test false predicates, nullable values, sensitive literals, unsupported syntax, deterministic replay and publication rollback.
- [x] Update schemas, public contracts, docs and exact-source release-candidate evidence before activation.
- [x] Record source-row pivot/unpivot as deferred outside this synthetic change;
  require a separate explicitly authorized transformation/I/O proposal before
  implementation. See the scope disposition below and the roadmap.


Candidate checkpoint: implementation and focused acceptance are complete. The
final local release gate passed 4636 tests with 91.97% coverage, schema freshness,
resource/dependency budgets and synthetic quickstart. Strict MkDocs and OpenSpec
passed. The public-activation task remains open for exact-head provider CI and
merge; source-row pivot/unpivot remains a separate transformation/I/O proposal.


Merged checkpoint: #648 completed all 38 CI checks successfully on exact head
`4639aaf4634d88fbbaf639f1ce54b241fb4e9203`, then merged as
`25a221b70f95a0e9d11e8191a2301dedac9aa690`. The conditional-formula/EAV modeling
slice is complete. Source-row pivot/unpivot remains a separate explicitly
authorized transformation/I/O change; it is not part of synthetic generation.


## Final scope disposition — 2026-10-25

The implemented conditional-formula/source-free EAV requirements shipped in
1.7.0rc1 at `64b7c8c3bbb0174fd7e159c4dfb42312045a1716`; public package and
release verification are recorded in the candidate release evidence. The fresh
isolated installed-wheel follow-up also covers the conditional-formula matrix.
Earlier pending CI/merge/release paragraphs above are historical checkpoints.

The last unchecked line described a future scope restriction, not an unimplemented
requirement in this change's delta. Source-row pivot/unpivot changes row
cardinality, duplicate handling and provenance and cannot be enabled by the
source-free EAV model or the one-to-one transformation contract. Its disposition
is **deferred, not implemented**, retained explicitly in the roadmap. A future
proposal must define those contracts and obtain the required source-I/O authority;
archiving this completed synthetic slice grants none of it.
