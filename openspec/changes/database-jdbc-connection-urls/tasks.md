# Tasks: database-jdbc-connection-urls

- [ ] Add typed PostgreSQL and Trino JDBC URL parsers at the existing
  configuration boundaries.
- [ ] Add additive CLI/environment inputs and deterministic conflict handling.
- [ ] Reject credentials, unsafe properties, ambiguous URLs, and unverified TLS
  before network access.
- [ ] Add `examples/local_postgres/run-jdbc.sh` and
  `examples/local_trino/run-jdbc.sh` using the existing disposable synthetic
  services, installed-wheel entry points, placeholder URLs, and fixed seeds.
- [ ] Add no-network unit, CLI/configuration, and example contract tests with
  placeholder URLs; keep live disposable runs explicitly gated.
- [ ] Prove URLs and component values cannot enter profiles, logs, errors, MCP,
  provider payloads, or artifacts.
- [ ] Prove both JDBC examples complete profile, infer, generate, and validate,
  report `source_rows_copied: false`, and clean up on success or failure.
- [ ] Update README, PostgreSQL/Trino how-to pages, configuration reference,
  changelog, roadmap, and public contract tests.
- [ ] Run focused ruff, mypy, pytest, documentation contracts, and strict
  MkDocs checks.
- [ ] Run the full release gate before assigning the implementation to a
  release candidate.
