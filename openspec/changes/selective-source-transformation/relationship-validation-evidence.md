# Relationship and final-validation evidence audit

## Updated closed candidate checkpoint — 2026-10-02 UTC

The audit below records the earlier accepted-main boundary, not the current
dirty candidate's complete coverage. Closed `io/transformation_batch.py` now
binds ordered per-input snapshots, exact saved-profile/validation bytes and
concrete shared domain mappings. It validates final scalar relationships and
explicit complete non-null ordered composite tuples before temporary atomic
bundle publication. Composite parent uniqueness, child membership and declared
one-to-one cardinality are checked as tuples, not independent components.
Common preservation uses a real controlling-TTY receipt bound to exact snapshot
and displayed review; individual receipts cannot authorize a batch.

Installed isolated development wheel SHA256
`075c5225f4fe22a0d470b0c8960e7f02d3806a795df4a5b7929b6acbcde9921d`:
batch suite55passed3.59s. Subsequent four focused saved-profile inline/CSV null
tests passed against that unchanged installed product in0.50s: empty input is
distinct from explicit null; output null uses its configured marker; optional
report flags do not disable final non-nullable schema rejection. The tests use
nullable independent string fields, not new nullable composite semantics.

This supersedes the earlier assertion that no cross-input execution evidence
exists. It does NOT close public multi-input interface/route parity, nullable
composite semantics, complete multi-domain/scale coverage, independent exact-SHA
safety/RC review or full RC acceptance. Public single-input contracts remain
unchanged; the batch adapter is unregistered and temporary fictional-only.

## Historical accepted-main audit

Checkpoint: 2026-10-02 UTC, accepted implementation main
`8670e562f50980cfd62678c6f0f51d4887cb8961`. Read-only code/test inspection;
no successful checks repeated and no new runtime or safety-policy change.

## Established coverage

- `tests/test_transformation_approval.py::test_composite_domain_binds_ordered_fields_in_both_entities`
  checks ordered inline/CSV domain components across entities, including type and
  partial-identity rejection. This is approval preflight, not cross-input execution.
- `test_composite_domain_rejects_missing_or_ambiguous_field_positions` rejects
  incomplete/ambiguous component declarations. Decimal domain shape compatibility
  is checked by `test_decimal_domain_requires_same_shape_across_entities`.
- `tests/test_transformation_execute.py::test_composite_domain_matches_whole_original_tuple`
  checks one-input composite inline/CSV execution for string/integer/float/date
  tuples, including missing-tuple rejection and original column order. It does
  not prove independent parent/child dataset referential integrity.
- `test_closed_synthesis_uses_bound_spec_seed_and_source_row_count` covers final
  schema/uniqueness rejection despite disabled optional validation flags, valid
  mode restrictions, nullable failures and bound generation references.
- Existing nullable/typed-mapping tests and installed route/finance evidence
  cover specific accepted types and readback. Formula-rounding tests belong to
  the private derive engine: do not count them as SQL aggregate recomputation.

## Claims deliberately not closed

The policy contract's Shared Domains And Relationships section explicitly says
ordered field binding is implemented while relationship execution/full composite
key validation remain pending. Its execution section explicitly excludes
cross-input relationships. Therefore neither domain preflight nor single-input
readback closes the tasks to implement consistent linked-key execution and validate
every declared cross-row relationship before publication. No full multi-domain,
cross-input, infeasible-relationship or final-RC acceptance claim is made.

Next trace the declared relationship boundary and approved full-scope plan before
choosing the smallest implementation; keep unsupported shapes fail-closed and
do not activate private derive or infer new relationship semantics.

## Executable boundary trace

`io/transformation_receipt.py::_canonical_request` explicitly requires exactly
one source and revalidates evidence against that source. `replace_csv_snapshot`
also rejects decisions for another entity. The current public signatures accept
one source path and one policy; a multi-input wrapper cannot safely concatenate
requests or reuse an individual receipt as approval of a combined dataset.

`validation/reconciliation.py::assert_generated_dataset_valid` enforces final
schema, relationships and constraints independently of optional report flags,
but also performs source-free generated-row privacy checks. It must not be used
unchanged to reject owner-approved explicit mapped values under ADR-0029.
Reuse the separate schema/relationship/constraint validators at the future
transformation boundary, retaining existing cell-origin privacy guards.

Implementation must bind all sources, shared concrete domain/mapping bytes and
the declared validation specification before execution; check final parent/child
tuples and uniqueness before one atomic bundle publication. Existing single-input
receipt/snapshot/rollback contracts remain unchanged until that candidate is
complete. No partial per-entity publication or inferred relationship declarations.
