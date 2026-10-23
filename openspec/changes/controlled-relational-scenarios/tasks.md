# Tasks
- [x] Specify typed scenario contract, full edge identity, count precedence and spec/size hash binding.
- [ ] Add preflight for null eligibility, exact totals, conflicting rules, key-pool/one-to-one constraints and bounded allocation.
- [ ] Implement synthetic-only exact orphan mutation behind explicit controlled-invalid mode.
- [ ] Implement bounded fan-out assignment using generated parent ordinals only.
- [ ] Record requested/observed violations and fan-out evidence without source values or fidelity claims.
- [ ] Test omitted-option compatibility, zero/all-null/empty/impossible plans, deterministic replay and no partial publication.
- [ ] Update public contracts, documentation, OpenSpec baselines and run exact-source candidate gates before activation.


## Private preflight foundation

- [x] Add immutable full-edge declarations with strict bounded counts.
- [x] Bind internal preparation to effective-spec, resolved-size and declaration hashes plus explicit seed.
- [x] Reject statically impossible eligibility/capacity, ambiguous edges, conflicting key writers and ratio/mode combinations using the shared budget.
- [x] Validate the actual frozen generated parent keys/null mask and every target before private mutation.

The foundation is not a registered execution option. The original allocation,
evidence, compatibility and release-candidate tasks remain open; static checks
are not evidence that requested scenarios were generated.

## Private atomic execution

- [x] Allocate exact orphan and fan-out counts on a bounded generated-key preview.
- [x] Preserve dependency order, generated null masks and independent seeded replay.
- [x] Reconcile all active relationships before committing; rollback expired commits.
- [x] Return count-only requested/observed evidence with expected-invalid status.
- [ ] Register reviewed declarations, mandatory writer reconciliation and public evidence.

Private execution has 14 synthetic cases; 150 focused tests pass including
legacy relationship solving, validation, conditional formulas and budgets.
This does not activate a public generation option or close publication gates.
