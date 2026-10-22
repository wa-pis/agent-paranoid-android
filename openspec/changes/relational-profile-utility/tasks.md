# Tasks
- [ ] R1: Verify repeated-key pool coverage across adapters and exact/unknown/censored count cases with synthetic profiles.
- [ ] R2: Verify metadata PK names not ending in id; explicitly support or reject composite PKs without selecting a component silently.
- [ ] R3: Specify additive per-entity sizing and total row budgets; retain --count compatibility and reject oversized plans before allocation.
- [ ] R4: Reuse metadata-only relationship discovery as reviewable candidates; test ambiguous names, absent parents, different domains and unauthorized tables.
- [ ] R5: Add utility/coverage evidence for declared checks, unmodeled relationships, key-domain size and temporal evidence; distinguish unknown from measured zero.
- [ ] R6: Specify optional controlled orphan/fan-out scenarios independently from valid FK generation; never infer source row mappings.
- [ ] R7: Evaluate EAV conditional-formula/pivot requests and record support or an explicit separate proposal.
- [ ] R8: Exercise unequal parent/child sizes, nullable keys, empty relations and deterministic replay through CLI and direct services.
- [ ] R9: Update synthetic-generation/dataset-validation baselines, docs, contracts and candidate migration evidence.
