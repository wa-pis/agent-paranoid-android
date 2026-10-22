# Tasks
- [x] R1: Verify repeated-key pool coverage across adapters and exact/unknown/censored count cases with synthetic profiles.
- [x] R2: Verify metadata PK names not ending in id; explicitly support or reject composite PKs without selecting a component silently.
- [ ] R3: Specify additive per-entity sizing and total row budgets; retain --count compatibility and reject oversized plans before allocation.
- [ ] R4: Reuse metadata-only relationship discovery as reviewable candidates; test ambiguous names, absent parents, different domains and unauthorized tables.
- [ ] R5: Add utility/coverage evidence for declared checks, unmodeled relationships, key-domain size and temporal evidence; distinguish unknown from measured zero.
- [ ] R6: Specify optional controlled orphan/fan-out scenarios independently from valid FK generation; never infer source row mappings.
- [ ] R7: Evaluate EAV conditional-formula/pivot requests and record support or an explicit separate proposal.
- [ ] R8: Exercise unequal parent/child sizes, nullable keys, empty relations and deterministic replay through CLI and direct services.
- [ ] R9: Update synthetic-generation/dataset-validation baselines, docs, contracts and candidate migration evidence.

## R2 implementation evidence

- Catalog key arity is returned alongside authorized column metadata; no raw keys
  or unauthorized component names are fetched. Composite keys reject before
  aggregate scans, even for a partial allowlist.
- Single-column INTEGER/STRING keys become synthetic identifiers independently
  of their name, retaining sensitivity. Other key types require a reviewed spec.
- Synthetic tests cover integer/text/sensitive names through inference,
  deterministic generation and validation, full/partial composite metadata,
  malformed arity and unsupported key types. R9 remains open for the broader
  relational work and candidate migration evidence.

## R1 verification evidence

- Extended the output-size matrix through public Trino aggregate and JSON
  adapters, in addition to CSV file, folder and shared aggregate profiles.
- PostgreSQL table and both SQL-query adapters retain repeated synthetic pools
  through inference, larger generation, deterministic replay and validation.
  Their tests provide aggregates only, with no source key values.
- Parquet with and without row-group statistics retains unknown distinctness;
  neither pools nor primary keys are invented. Unknown nulls reject inference.
- Unknown/zero distinct counts, CSV fingerprint censoring and CSV-folder
  tracker overflow do not manufacture pool sizes or primary-key evidence.
- Existing native pool validation, sensitive identifiers, nullable output,
  independent domains and undersized primary-key rejection tests are retained.
- This verification changes no runtime behavior, schema or seeded output.
  Parquet cardinality collection remains separate bounded-statistics work.
