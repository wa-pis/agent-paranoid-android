# Tasks: database-jdbc-connection-urls

- [x] Add typed PostgreSQL and Trino JDBC URL parsers at the existing
  configuration boundaries.
- [x] Add additive CLI/environment inputs and deterministic conflict handling.
- [x] Reject credentials, unsafe properties, ambiguous URLs, and unverified TLS
  before network access.
- [x] Bound URL bytes and parsed host/database/catalog/schema components before
  client construction, with fixed non-reflective errors and no-network tests.
- [x] Add `examples/local_postgres/run-jdbc.sh` and
  `examples/local_trino/run-jdbc.sh` using the existing disposable synthetic
  services, installed-wheel entry points, placeholder URLs, and fixed seeds.
- [x] Add no-network unit, CLI/configuration, and example contract tests with
  placeholder URLs; keep live disposable runs explicitly gated.
- [x] Prove URLs and component values cannot enter profiles, logs, errors, MCP,
  provider payloads, or artifacts.
- [x] Prove both JDBC examples complete profile, infer, generate, and validate,
  report `source_rows_copied: false`, and clean up on success or failure.
  Evidence: the installed-wheel PostgreSQL acceptance matrix passed component,
  JDBC, wildcard, and query launchers locally; PR #456 passed the equivalent
  disposable Trino CI matrix, including cleanup assertions.
- [x] Update README, PostgreSQL/Trino how-to pages, configuration reference,
  changelog, roadmap, and public contract tests.
- [x] Run focused ruff, mypy, pytest, documentation contracts, and strict
  MkDocs checks.
- [x] Run the full release gate before assigning the implementation to a
  release candidate.
- [x] Hand the shipped CLI/configuration/example facts to the separate
  `database-source-documentation-reconciliation` cross-feature audit.
