# Tasks: 1-0-0-rc4-privacy-invocation-hardening

## P0 — Default MCP privacy boundary

- [x] Update the safe-MCP capability requirements for source-literal-free
  default responses.
- [x] Remove `sample_rows_masked` from the default Trino MCP registration, or
  implement the explicit opt-in/review/audit boundary for any retained row
  diagnostic.
- [ ] Update MCP golden contracts, docs, migration notes, and release notes.
- [ ] Add direct-service and transport tests with distinct literals in every
  source column; assert none appear in default responses, errors, or audit
  records.

## P1 — Invocation and release hardening

- [ ] Add a typed shared `QueryWorkBudget` and enforce request, SQL/formula,
  AST, depth, columns, statements, and response limits before their respective
  resource-consuming operations.
- [ ] Thread one budget through nested table/column profiling and safe-query
  execution; add tests proving exhaustion is shared across the invocation and
  no connection/cursor is opened for preflight failures.
- [ ] Change prerelease installation examples to select RC4 intentionally,
  update extras, and add a clean-environment README smoke check against the
  public wheel.
- [ ] Verify the base wheel and CSV/JSON quickstart without `trino`, `sqlglot`,
  or the MCP SDK; verify Trino separately through the `trino` extra and keep
  failures isolated to that optional capability.
- [ ] Publish `1.0.0rc4` from the exact verified merge commit and run public
  package, wheel, container, documentation, attestation, signature, and
  integration acceptance.

## P2/P3 — Contract clarity and durability decision

- [ ] Document aggregate-only tools versus explicitly opt-in row-returning
  tools and remove ambiguous privacy claims.
- [ ] Document atomic visibility, process-interruption recovery, and
  crash/power-loss durability separately; record whether fsync is deferred or
  release-blocking.

## Release gates

- [ ] Run `python3 -m ruff check src tests`.
- [ ] Run `python3 -m compileall -q src tests`.
- [ ] Run `python3 -m pytest --cov=test_data_agent --cov-report=term-missing --cov-fail-under=85`.
- [ ] Run `scripts/check_release.sh` and `mkdocs build --strict`.
- [ ] Confirm every remaining finding has an owner, disposition, and revisit
  trigger before stable promotion.
