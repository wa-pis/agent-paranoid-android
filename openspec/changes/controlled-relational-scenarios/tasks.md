# Tasks
- [x] Specify typed scenario contract, full edge identity, count precedence and spec/size hash binding.
- [x] Add preflight for null eligibility, exact totals, conflicting rules, key-pool/one-to-one constraints and bounded allocation.
- [x] Implement synthetic-only exact orphan mutation behind explicit controlled-invalid mode.
- [x] Implement bounded fan-out assignment using generated parent ordinals only.
- [x] Record requested/observed violations and fan-out evidence without source values or fidelity claims.
- [x] Test omitted-option compatibility, zero/all-null/empty/impossible plans, deterministic replay and no partial publication.
- [ ] Update public contracts, documentation, OpenSpec baselines and run exact-source candidate gates before activation.


## Private preflight foundation

- [x] Add immutable full-edge declarations with strict bounded counts.
- [x] Bind internal preparation to effective-spec, resolved-size and declaration hashes plus explicit seed.
- [x] Reject statically impossible eligibility/capacity, ambiguous edges, conflicting key writers and ratio/mode combinations using the shared budget.
- [x] Validate the actual frozen generated parent keys/null mask and every target before private mutation.

Historical foundation: this checkpoint had no registered execution option.
Static checks alone did not prove generated scenarios; the candidate below adds
execution and interface acceptance.

## Private atomic execution

- [x] Allocate exact orphan and fan-out counts on a bounded generated-key preview.
- [x] Preserve dependency order, generated null masks and independent seeded replay.
- [x] Reconcile all active relationships before committing; rollback expired commits.
- [x] Return count-only requested/observed evidence with expected-invalid status.
- [x] Register reviewed declarations, mandatory writer reconciliation and public evidence.

Private execution has 14 synthetic cases; 150 focused tests pass including
legacy relationship solving, validation, conditional formulas and budgets.
This does not activate a public generation option or close publication gates.

## Public contract candidate

- [x] Register the optional reviewed DatasetSpec field, omitting empty values for legacy identity compatibility.
- [x] Keep preparation in deterministic rules and count-only observation in validation.
- [x] Run preparation before row allocation and resolve controlled relationships before native/business solving.
- [x] Reconcile mandatory schema/privacy/native/business/scenario invariants in generation and both writer entry points.
- [x] Keep expected orphan datasets invalid in reports/manifests, including disabled optional validation settings.
- [x] Exercise Python, CLI and row-free MCP plus JSON/CSV/Parquet publication and SQL rejection.
- [x] Update schemas, advisor contract fixture, EN/RU documentation, example, changelog and baseline specs.
- [x] Complete the full local release gate and record exact-source evidence.
- [ ] Complete all exact-head provider CI checks and merge the candidate.

The candidate has 32 preflight, 14 private atomic-execution and 16 public-interface
synthetic test cases. No live database, source rows, release tag or package
publication is part of this change. Full release/CI results remain pending.

Local release gate: 4698 passed, 23 skipped, 92.03% coverage, with dependency,
resource, schema and quickstart checks successful. Exact-head provider CI and
merge remain open. The source/schema digest is recorded in verification.md.
