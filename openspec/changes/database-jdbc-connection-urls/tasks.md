# Tasks: database-jdbc-connection-urls

- [ ] Add typed PostgreSQL and Trino JDBC URL parsers at the existing
  configuration boundaries.
- [ ] Add additive CLI/environment inputs and deterministic conflict handling.
- [ ] Reject credentials, unsafe properties, ambiguous URLs, and unverified TLS
  before network access.
- [ ] Add no-network unit and CLI/configuration tests with placeholder URLs.
- [ ] Prove URLs and component values cannot enter profiles, logs, errors, MCP,
  provider payloads, or artifacts.
- [ ] Update README, PostgreSQL/Trino how-to pages, configuration reference,
  changelog, roadmap, and public contract tests.
- [ ] Run focused ruff, mypy, pytest, documentation contracts, and strict
  MkDocs checks.
- [ ] Run the full release gate before assigning the implementation to a
  release candidate.
