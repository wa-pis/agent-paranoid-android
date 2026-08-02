# Tasks: 1-0-0-rc4-privacy-invocation-hardening

## P0 — Default MCP privacy boundary

- [x] Update the safe-MCP capability requirements for source-literal-free
  default responses.
- [x] Remove `sample_rows_masked` from the Trino MCP server, masking service,
  query builder, and public compatibility exports. Do not retain a row
  diagnostic in RC4; any future row-returning capability requires a separate
  OpenSpec change.
- [x] Update MCP golden contracts, docs, migration notes, and release notes.
- [x] Enumerate the production-registered default tool list from
  `trino_mcp_tools()` and test every Trino-accessing tool through both direct
  service and transport boundaries. Check success responses, validation and
  database errors, nested structures after JSON serialization, and metadata-
  only audit records for source literals.
  - [x] Freeze the exact default list and verify transport registration order
    plus audit wrapping for every production-registered tool.
  - [x] Exercise every tool through direct and transport success, validation,
    database-error, serialized nested-response, and audit paths.
    - [x] Invoke every production default wrapper through a direct-service
      success path and assert request sentinels are not echoed.
    - [x] Invoke every production default wrapper through a transport success
      path and assert request sentinels are not echoed.
    - [x] Cover validation failures through direct and transport paths without
      echoing request sentinels.
    - [x] Cover database failures through direct and transport paths without
      echoing request sentinels.
    - [x] Cover direct and transport nested serialization paths.
    - [x] Cover every default transport audit path with metadata-only success
      and failure records that omit arguments, results, and source literals.
- [x] Add source fixtures covering strings, integers, decimals, floats,
  booleans, dates, timestamps with timezone, UUID-like values, binary/base64-
  like values, Unicode, nested JSON, and null mixtures. Ensure sentinel values
  cannot be confused with aggregate counts.

## P1 — Invocation and release hardening

- [ ] Add a typed shared `QueryWorkBudget` with separate raw transport payload
  and canonical application-argument limits. Create it fresh per invocation,
  keep it concurrency-isolated and non-resettable, and enforce SQL/formula,
  AST, depth, columns, statements, and response limits before their respective
  resource-consuming operations.
  - [x] Define typed immutable limits, monotonic counters, immutable usage
    snapshots, and a bounded typed exhaustion error.
  - [x] Create one fresh budget per invocation and enforce separate raw
    transport and canonical application-argument limits.
    - [x] Create and concurrency-isolate a fresh application budget, then
      enforce canonical UTF-8 argument bytes before tool execution.
    - [x] Enforce raw transport payload bytes before MCP argument parsing.
  - [ ] Enforce SQL/formula, AST, depth, column, statement, and response limits
    at their resource-consuming boundaries.
    - [x] Enforce cumulative SQL/formula character work before Python/sqlglot
      parsing and before opening a Trino connection.
    - [x] Enforce AST node and depth work before query execution.
    - [x] Enforce projected-column work before query execution.
    - [x] Enforce statement work before opening a connection or cursor.
    - [ ] Consume response bytes incrementally before retaining complete
      oversized results.
- [ ] Thread one budget through nested table/column profiling and safe-query
  execution; consume response bytes incrementally, stop after exhaustion, and
  prove no connection/cursor or later statement is opened after preflight or
  nested-budget failure.
- [ ] Change prerelease installation examples to the exact
  `agent-paranoid-android==1.0.0rc4` command, update extras, and add a
  clean-environment README smoke check against that public wheel. Do not use
  floating `--pre` in the RC-specific instructions.
- [ ] Verify the base wheel and CSV/JSON quickstart without `trino`, `sqlglot`,
  or the MCP SDK; verify Trino separately through the `trino` extra and keep
  failures isolated to that optional capability.
- [ ] Publish `1.0.0rc4` from the exact verified merge commit and run public
  package, wheel, container, documentation, attestation, signature, and
  integration acceptance.

## P2/P3 — Contract clarity and durability decision

- [ ] Document the aggregate-only default toolset and the separate
  `run_safe_select` opt-in. Remove stale `sample_rows_masked` references and
  claims that row-returning output is source-free, PII-free, anonymous, or
  privacy-safe.
- [ ] Document atomic visibility, process-interruption recovery, and
  crash/power-loss durability separately; record whether fsync is deferred or
  release-blocking.
- [ ] Define stable promotion as the accepted RC4 production source tree plus
  a reviewed version/changelog/release-metadata-only diff, followed by all
  final release gates.

## Release gates

- [ ] Run `python3 -m ruff check src tests`.
- [ ] Run `python3 -m compileall -q src tests`.
- [ ] Run `python3 -m pytest --cov=test_data_agent --cov-report=term-missing --cov-fail-under=85`.
- [ ] Run `scripts/check_release.sh` and `mkdocs build --strict`.
- [ ] Confirm every remaining finding has an owner, disposition, and revisit
  trigger before stable promotion.
