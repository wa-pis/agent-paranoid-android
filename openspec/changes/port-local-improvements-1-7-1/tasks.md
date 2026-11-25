# Port Tasks

- [x] Snapshot the original changes and create a separate branch/worktree at 1.7.1.
- [x] Merge privacy, semantic counters and source policy without dropping release gates.
- [x] Merge exact CSV distinct tracking and private DuckDB spill; retain released Parquet inspection.
- [x] Adapt tiled CSV, generation and validation optimizations to the released models and budgets.
- [x] Retain historical measurements and classify superseded documentation/implementations.
- [x] Complete combined regression, seeded release parity, package/contract, coverage and static checks.
- [x] Finish documentation/OpenSpec, independent review and final source-preservation audit.
- [x] Complete the automation's final review, address reproduced regressions and record fresh gates.

Historical local completion evidence: [final review](final-review.md) and
[machine-readable checks](final-review-checks.json), bound to `1a40ad08`.

## Current PR qualification

- [x] Record the completed CI checks and fixes at exact implementation `0529fb43`.
- [x] Repeat ordinary/streaming public CSV measurements at 100,000/750,000 rows
  and 25 fields, with four alternating repeats, full checks and source identity.
- [x] Prepare a source-grouped guide and checklist for human review.
- [ ] Obtain a human review decision against an explicit SHA. Reviewer assignment
  awaits an operator-specified reviewer's GitHub login; automated reviews do not
  close this step.

Current evidence: [CI follow-up](ci-followup.md),
[CSV benchmark](public-csv-current.md) and [human review guide](review-guide.md).

## Release candidate safety follow-up

- [x] Restore polymorphic request-deadline checks before native work; reproduce
  both captured budget subclasses and PostgreSQL/Trino pre-spawn refusals.
- [x] Remove unused unbounded distinct-digest retention from native
  transformation profiling; retain unknown distinctness and privacy evidence.
- [x] Qualify the replacement candidate with fresh exact-source release gates,
  review and installed Ubuntu-artifact acceptance before tagging/publication;
  see [1.8.0rc1 release evidence](../../../docs/release-evidence-1.8.0rc1.md).

The `204a3240` candidate is not releasable. See the release follow-up in
[verification](verification.md#release-candidate-safety-follow-up).
