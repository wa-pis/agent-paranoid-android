# Tasks: database-source-documentation-reconciliation

- [ ] Confirm JDBC URL, qualified wildcard, and SQL query source runtime
  contracts are implemented and their focused OpenSpecs are ready to baseline.
- [ ] Reconcile `README.md`, `docs/index.md`, installation,
  choosing-an-approach, and MkDocs navigation with shipped behavior.
- [ ] Reconcile PostgreSQL/Trino how-to pages and both local example READMEs;
  execute the component, JDBC, wildcard, and query-source launchers from an
  installed wheel against synthetic disposable sources.
- [ ] Reconcile CLI help/reference, configuration, stability, support,
  compatibility, profile/spec, and public Python contracts.
- [ ] Reconcile safety model, threat model, resource budgets, troubleshooting,
  agent guides, implementation map, and application-boundary ownership.
- [ ] Reconcile roadmap, changelog, release notes, acceptance checklist, and
  active/canonical OpenSpec status without claiming an unpublished feature.
- [ ] Remove stale or contradictory claims about JDBC runtime, URL credentials,
  wildcard SQL, arbitrary SQL, query rows, source-row copying, provider/MCP
  egress, and deterministic generation.
- [ ] Add or update help, JSON, Python, artifact, documentation, and runnable
  example contract tests.
- [ ] Run focused ruff, mypy, pytest, link checks, and `mkdocs build --strict`.
- [ ] Run the full release gate and installed-wheel smoke matrix for the target
  release without live credentials or production services.
- [ ] Baseline and archive all completed deltas only after public docs and
  examples match the exact shipped runtime.
