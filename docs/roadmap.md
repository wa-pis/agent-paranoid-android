# Roadmap

English · [Русский](ru/roadmap.md)

These are directions, not committed dates. Priorities follow user feedback and
confirmed defects. Stable `1.6.0` is already published and publicly verified;
completed work belongs in [release history](history.md), not this list.

## Now

- Follow up on the remaining external `1.6.0` evidence gaps through the
  [OpenSpec work plan](https://github.com/wa-pis/agent-paranoid-android/tree/main/openspec/changes/external-feedback-1-6):
  historical Trino application authentication settings and external profile
  provenance. The numeric profiling, relational planning/utility, bounded
  statistics and CLI fixes shipped in the published
  [1.7.0rc1 candidate](feedback-acceptance-1.7.0rc1.md); its finite installed
  checks do not reproduce missing private inputs or the historical 401.
- Complete remaining transformation evidence: target-size coverage of the final
  public/configured routes and the separately tracked trust-boundary amendment
  review. Prior approvals and private scale runs retain their original scope.
- Improve onboarding from pilot feedback. Versioned guides and four downloadable
  formats are already published; see [documentation versions](versions.md).
- Run product-validation pilots on development and analytics workflows.
- Address confirmed client defects, migration feedback and dependency maintenance.
- Monitor source/output consistency, portable business rules and MCP permissions.

## Next

- Implement Read the Docs migration while preserving verified editions, bilingual
  guides, four download formats, old links and rollback; see the
  [OpenSpec](https://github.com/wa-pis/agent-paranoid-android/tree/main/openspec/changes/migrate-documentation-to-readthedocs).
  The parallel edition builder and retained-manifest verification are prepared;
  hosted acceptance, version mapping,
  preview integration and rollback remain open. GitHub Pages remains the current
  host until parallel acceptance and switch.
- Design batch-based validation of CSV, JSON and Parquet so complete datasets
  need not remain in memory. Bound cross-table key and uniqueness checks,
  preserve deterministic results and measure memory on synthetic fixtures.
  A separate OpenSpec change is required before implementation.
- Simplify CSV and database workflows using pilot feedback.
- Publish runnable examples and short case studies using synthetic fixtures.
- Improve diagnostics where users repeatedly need help.

## Later

- Source-row EAV pivot/unpivot remains deferred. Conditional formulas and
  source-free EAV modeling shipped in the 1.7.0rc1 candidate; transforming existing
  EAV rows requires a separate proposal for row cardinality, duplicate/null
  semantics, typed values, provenance and explicitly authorized source I/O.
  Neither source-free generation nor one-to-one transformation authorizes it.
- Consider monthly-date category inference and a separately reviewed configurable
  local-category ceiling. Neither is implemented; source-preservation defaults
  remain 20 non-sensitive values of at most 64 characters, with content checks.
- Add integrations only after demonstrated demand.
- Consider reporting and validation adapters for concrete workflows.
- Evolve public contracts through the compatibility and deprecation policy.

The finite fictional transformation/session campaign for stable `1.6.0`
completed with [explicit coverage limits](release-evidence-1.6.0.md).
That grants no dataset permission. Changed public activation still requires
matching specifications, executable evidence and independent exact-source review.
