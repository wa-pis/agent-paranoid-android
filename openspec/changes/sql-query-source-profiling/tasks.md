# Tasks: sql-query-source-profiling

- [ ] Finalize the typed query-profile request and public CLI/Python contract
  after JDBC URL and qualified wildcard reviews.
- [ ] Add bounded query-file loading, dialect parsing, strict AST validation,
  and physical source allowlist enforcement.
- [ ] Add trusted PostgreSQL and Trino no-row schema and aggregate query
  builders for the initial SQL subset.
- [ ] Produce one source-free virtual-entity profile with query fingerprint,
  safe metadata, aggregates, and bounded warnings.
- [ ] Connect the profile to existing infer, review, deterministic generation,
  validation, and export without introducing a row-copy path.
- [ ] Add fake DB-API/Trino tests for accepted queries and adversarial SQL,
  unauthorized references, volatile functions, wildcard gating, schema drift,
  response shape, cleanup, and every resource budget.
- [ ] Prove SQL text, SQL literals, backend errors, endpoints, source values,
  and query rows cannot enter logs, errors, MCP, providers, profiles, manifests,
  or generated fixtures.
- [ ] Add runnable synthetic PostgreSQL and Trino examples plus README, CLI,
  Python, configuration, privacy, roadmap, changelog, and OpenSpec updates.
- [ ] Run full ruff, mypy, pytest, release checks, strict MkDocs, package build,
  and isolated-wheel smoke before release assignment.
- [ ] Obtain focused independent review of the SQL policy and source-to-sink
  privacy boundary before publishing a candidate.
