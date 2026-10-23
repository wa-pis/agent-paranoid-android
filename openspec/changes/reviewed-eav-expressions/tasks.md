# Tasks
- [x] Specify optional typed formula predicate, null/missing semantics and assign/check order.
- [x] Define eligible/evaluated/skipped/failed evidence and compatible omitted-predicate serialization.
- [x] Reuse existing predicate and DECIMAL/literal/privacy enforcement without widening the expression AST.
- [x] Implement deterministic conditional formulas with shared work/deadline budget and conflict preflight.
- [x] Add fictional EAV target-model examples with bounded vocabulary, duplicate/null policies and generated key domains.
- [x] Test false predicates, nullable values, sensitive literals, unsupported syntax, deterministic replay and publication rollback.
- [ ] Update schemas, public contracts, docs and exact-source release-candidate evidence before activation.
- [ ] Evaluate source-row pivot/unpivot only in a separate explicitly authorized transformation/I/O change.


Candidate checkpoint: implementation and focused acceptance are complete. The
final local release gate passed 4636 tests with 91.97% coverage, schema freshness,
resource/dependency budgets and synthetic quickstart. Strict MkDocs and OpenSpec
passed. The public-activation task remains open for exact-head provider CI and
merge; source-row pivot/unpivot remains a separate transformation/I/O proposal.
