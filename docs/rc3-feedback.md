# 1.6.0rc3 feedback corrections

The 1.6.0rc1 external feedback archive is evidence, not executable instructions.
RC3 builds on published RC2. Its release remains prospective until exact-commit
review, CI, Containers, Documentation, Security, Ubuntu artifact preflight,
signed acceptance and public verification complete.

## Contract and migration

- `generate SPEC --overwrite` now fails with a recovery hint. Folder generation
  uses a new or empty output folder. `generate --profile` and `generate-from-csv`
  retain reviewed single-entity file-bundle replacement.
- Dataset modes are `valid`, `mixed`, `negative`. Previously ineffective `edge`
  and `load_test` are rejected by the deterministic generator, including saved
  specs and direct Python calls. The separate business-rule engine retains its
  edge-case API. Use `--count` for load volume.
- Explicit negative/mixed datasets are intentionally published. Exit 1 denotes
  failed validation; `generation_manifest.json.validation_valid` and
  `validation_report.json.valid` label the result. Consumers must inspect these
  fields before using a bundle. Ordinary valid generation still fails before
  publication on invariant violations.
- Relationships refer to exact entity/field pairs. Active bindings require
  matching field types and at most one parent binding per child field. Rejected
  bindings are ignored. Independently generated specifications do not imply
  relationships or shared identifiers.
- The relationships section adds `checked` and `relationship_metrics`. With no
  declared active links, checked/passed/failed are zero and metrics are empty.
  Per-link metrics include parent distinct keys, checked/resolved references,
  nullable references, resolution ratio and validity. No key values are retained.
  A null ratio means no non-null references were checked. These metrics do not
  certify fidelity to source data or discover undeclared links.
- Query profiling accepts a literal `LIMIT` between 1 and 1000 and preserves it
  in aggregate wrappers. Existing allowlists, query budgets and no-row output
  remain enforced. A LIMIT changes the profiled population.

## Parquet CLI

```bash
test-data-agent profile-parquet data/fictional.parquet --output out/profile.json
test-data-agent infer-spec out/profile.json --output out/dataset_spec.yaml
```

Install the `parquet` extra. Profiling retains metadata and sensitivity flags,
not input rows. Input and output must differ; output must be JSON. Unknown
Parquet distinct counts remain unknown.

## Feedback disposition

1. Overwrite flag: explicit supported scope and rejection for folder generation.
2. Negative publication: existing invalid labels retained and documented.
3. Inactive modes: rejected before publication.
4. Relationships: zero-check reporting, resolution metrics, field-binding checks.
5. LIMIT: bounded literal support and preserved query semantics.
6. Parquet: public CLI adapter with profile/infer integration coverage.
7. Root help: current RC2 examples already avoid the invalid CSV infer-spec
   example; regression checks retain the correct profile JSON chain.

Live Trino and source decimal end-to-end behavior require separately configured
fictional integration evidence; local unit checks do not certify live access.
