# Tasks: database-source-documentation-reconciliation

- [x] Confirm JDBC URL, qualified wildcard, and SQL query source runtime
  contracts are implemented and their focused OpenSpecs are ready to baseline.
- [x] Reconcile `README.md`, `docs/index.md`, installation,
  choosing-an-approach, and MkDocs navigation with shipped behavior.
- [x] Reconcile PostgreSQL/Trino how-to pages and both local example READMEs;
  execute the component, JDBC, wildcard, and query-source launchers from an
  installed wheel against synthetic disposable sources.
  Evidence: PR #454 reconciled the public pages and PR #456 records the
  installed-wheel PostgreSQL and disposable Trino four-mode matrices.
- [x] Reconcile CLI help/reference, configuration, stability, support,
  compatibility, profile/spec, and public Python contracts.
- [x] Reconcile safety model, threat model, resource budgets, troubleshooting,
  agent guides, implementation map, and application-boundary ownership.
- [x] Reconcile roadmap, changelog, release notes, acceptance checklist, and
  active/canonical OpenSpec status without claiming an unpublished feature.
- [x] Remove stale or contradictory claims about JDBC runtime, URL credentials,
  wildcard SQL, arbitrary SQL, query rows, source-row copying, provider/MCP
  egress, and deterministic generation.
- [x] Add or update help, JSON, Python, artifact, documentation, and runnable
  example contract tests.
- [x] Run focused ruff, mypy, pytest, link checks, and `mkdocs build --strict`.
- [x] Run the full release gate and installed-wheel smoke matrix for the target
  release without live credentials or production services.
  Evidence: `scripts/check_release.sh` passed with 1230 tests, 10 gated live
  skips, and 90.27% coverage; PR #456 and the local disposable PostgreSQL run
  cover component, JDBC, wildcard, and query installed-wheel modes.
- [x] Baseline and archive all completed deltas only after public docs and
  examples match the exact shipped runtime.
  Evidence: canonical database-source configuration, allowlist, query-source,
  and public-documentation specifications were created before archival.
