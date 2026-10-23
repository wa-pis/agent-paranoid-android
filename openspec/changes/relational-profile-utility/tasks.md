# Tasks
- [x] R1: Verify repeated-key pool coverage across adapters and exact/unknown/censored count cases with synthetic profiles.
- [x] R2: Verify metadata PK names not ending in id; explicitly support or reject composite PKs without selecting a component silently.
- [x] R3: Specify additive per-entity sizing and total row budgets; retain --count compatibility and reject oversized plans before allocation.
- [x] R4: Reuse metadata-only relationship discovery as reviewable candidates; test ambiguous names, absent parents, different domains and unauthorized tables.
- [x] R5: Add utility/coverage evidence for declared checks, unmodeled relationships, key-domain size and temporal evidence; distinguish unknown from measured zero.
- [x] R6: Specify optional controlled orphan/fan-out scenarios independently from valid FK generation; never infer source row mappings.
- [x] R7: Evaluate EAV conditional-formula/pivot requests and record support or an explicit separate proposal.
- [x] R8: Exercise unequal parent/child sizes, nullable keys, empty relations and deterministic replay through CLI and direct services.
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

## R3 implementation evidence

- Additive per-entity sizing is available on direct inference, its artifact
  service and `infer-spec`; global `--count` semantics and omitted-count defaults
  are retained. Specific overrides take precedence; ambiguity rejects.
- An explicit optional total-row planning ceiling rejects before field inference
  or spec publication. It is not persisted; later count/load changes require
  renewed review, with runtime row/byte/work budgets still enforced as before.
- Synthetic tests cover precedence, defaults, strict counts, unknown/duplicate
  names, no profile mutation, unchanged existing output on ceiling rejection,
  spec serialization and deterministic unequal parent/child generation with
  nullable foreign keys and validation. R8 remains open for its broader CLI and
  empty-relation acceptance matrix.

## R4 implementation evidence

- Reuse deterministic discovery in a saved-profile-only `discover-relationships`
  CLI and typed fingerprint-bound report. No database/provider call or table
  authorization expansion is added. Source distribution literals are excluded.
- Hypotheses retain explicit untrusted/review-required status and no generation
  authority. Ambiguous parents stay separate; names/types/counts cannot certify
  source overlap or domain identity. Accepted review does not mutate a spec.
- Share bounded local inference work/deadline across foreign-key and temporal
  discovery, cap candidates at 1,000 and bound profile/report payload bytes.
  Failures leave existing reports unchanged or publish no new artifact.
- Synthetic tests cover absent parents, independent domains, incompatible types,
  ambiguous names, lower-bound/unknown evidence, deterministic offline export,
  no source values, unchanged generation and work/candidate/report limits.
- Report kind rejects DatasetSpec parsing and CLI generation; an expired
  deadline at atomic publication rolls back instead of replacing an existing report.

## R5 implementation evidence

- Add optional typed hash-bound utility evidence to validation reports, retaining
  old report parsing and all existing validity/section semantics.
- Active declared check counts and executed/not-declared/not-run statuses account
  for rejected declarations, disabled sections and fail-fast. Existing generated
  relationship metrics expose key-domain counts and zero-versus-unknown ratios.
- Temporal observation/failure counts collect inside the existing budgeted scan;
  no source values, second row scan or generation change is introduced.
- Source orphan/fan-out/temporal fidelity and unmodeled relationship counts are
  explicitly unmeasured. Synthetic tests cover empty data, actual zero resolution,
  temporal failures, disabled/skipped/rejected declarations, legacy parsing,
  canonical hash agreement, changed-spec mismatch and deterministic CLI replay.
- Update generated report/MCP contract fixtures and relational guidance. Complete
  release-candidate gates remain tracked in R9 and the umbrella change.

## R8 acceptance evidence

- A synthetic direct/CLI matrix covers both larger-child and larger-parent
  tables with zero/all-null child keys, independent identifier domains, exact
  declared sizes, no spec mutation and deterministic replay with one seed.
- Header-only CSV tables and empty direct rows retain identical relationship
  metrics: no checked references gives no ratio; a real orphan fails. Schema
  validation still rejects row-count mismatch with positive declarations, so
  an empty dataset cannot be misrepresented as a fully valid generated bundle.
- Validation leaves input files unchanged. This adds acceptance coverage, not
  zero-row generation support or relaxed schema/relationship enforcement.

## R6/R7 reviewed dispositions

- Existing mixed/negative business rules already produce synthetic missing-parent
  cases; they do not promise targeted exact orphan counts or a source fan-out
  histogram. The proposed `controlled-relational-scenarios` follow-up specifies
  explicit edge/size binding, nullable eligibility, exact generated allocations,
  conflict rejection, controlled-invalid evidence and shared budgets. Runtime
  implementation and RC gates remain unchecked in that separate change.
- Formula rules have assign/check without a predicate; strict payloads reject
  unknown keys and the expression AST excludes Python conditional expressions.
  Conditional-required/allowed-values rules already use typed predicates.
  Scenario weights do not substitute for predicates, and EAV pivot is absent.
- The proposed `reviewed-eav-expressions` follow-up specifies typed conditional
  formula evaluation, skipped evidence, null/ordering/conflict semantics and
  source-free target modeling. Source-row pivot/unpivot requires a separate
  authorized transformation/I/O change. Neither proposal activates a feature.
- R9 and umbrella candidate/release gates remain open. These are explicit
  feasibility dispositions, not claims that the follow-up implementations shipped.
