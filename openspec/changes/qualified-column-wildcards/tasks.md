# Tasks: qualified-column-wildcards

- [ ] Add typed exact-column and table-qualified wildcard selectors for
  PostgreSQL and Trino configuration.
- [ ] Expand wildcard selectors through bounded metadata into one immutable
  explicit-column snapshot.
- [ ] Keep trusted query builders explicit and prove they never emit projection
  stars.
- [ ] Add fake DB-API/Trino tests for allow, deny, deterministic ordering,
  schema drift, malformed metadata, and every relevant budget.
- [ ] Prove wildcard authorization cannot enable row return, preserve-as-is,
  provider/MCP disclosure, or sensitive-value egress.
- [ ] Update README, PostgreSQL/Trino how-to pages, configuration reference,
  changelog, roadmap, and public contract tests.
- [ ] Run focused ruff, mypy, pytest, documentation contracts, and strict
  MkDocs checks.
- [ ] Run the full release gate before assigning the implementation to a
  release candidate.
