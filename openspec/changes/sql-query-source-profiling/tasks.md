# Tasks: sql-query-source-profiling

- [x] Finalize the typed query-profile request and public CLI/Python contract
  after JDBC URL and qualified wildcard reviews.
- [x] Add bounded query-file loading, dialect parsing, strict AST validation,
  and physical source allowlist enforcement.
- [x] Add trusted PostgreSQL and Trino no-row schema and aggregate query
  builders for the initial SQL subset.
- [x] Produce one source-free virtual-entity profile with query fingerprint,
  safe metadata, aggregates, and bounded warnings.
- [x] Connect the profile to existing infer, review, deterministic generation,
  validation, and export without introducing a row-copy path.
- [x] Add checked-in safe `query.sql` files and `run-query.sh` launchers under
  both `examples/local_postgres` and `examples/local_trino`, reusing their
  disposable synthetic services.
- [x] Add fake DB-API/Trino tests for accepted queries and adversarial SQL,
  unauthorized references, volatile functions, wildcard gating, schema drift,
  response shape, cleanup, and every resource budget.
- [x] Add installed-wheel example smoke tests for profile, query fingerprint,
  infer, deterministic generation, validation, non-copying, redaction, and
  cleanup; keep live database runs explicitly gated.
- [x] Prove SQL text, SQL literals, backend errors, endpoints, source values,
  and query rows cannot enter logs, errors, MCP, providers, profiles, manifests,
  or generated fixtures.
- [x] Document all query-source launchers and expected artifacts in their
  example READMEs plus README, CLI, Python, configuration, privacy, roadmap,
  changelog, and OpenSpec updates.
- [x] Run full ruff, mypy, pytest, release checks, strict MkDocs, package build,
  and isolated-wheel smoke before release assignment.
- [ ] Obtain focused independent review of the SQL policy and source-to-sink
  privacy boundary before publishing a candidate.
- [ ] Hand the shipped CLI/Python/query/example facts to the separate
  `database-source-documentation-reconciliation` cross-feature audit.
