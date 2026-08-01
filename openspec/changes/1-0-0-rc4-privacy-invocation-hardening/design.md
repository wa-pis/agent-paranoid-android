# Design: 1-0-0-rc4-privacy-invocation-hardening

## Approach

Implement the hardening in four bounded stages:

1. Make the default Trino MCP registration aggregate/metadata-only. Add a
   source-literal regression harness that uses distinct values in all columns,
   including non-PII-looking values. If a row diagnostic remains necessary,
   register it only through an explicit operator configuration and record its
   invocation in the existing metadata-only audit boundary.
2. Create a typed `QueryWorkBudget` owned by the Trino application boundary.
   Pass one budget object through profiling and query helpers, decrementing
   shared request, statement, column, AST, and response allowances. Check each
   limit before the operation that could consume it and fail closed with a
   bounded typed error.
3. Update prerelease installation examples, MCP safety language, contract
   fixtures, and release documentation. The clean-environment check must use
   the exact command shown to users and assert the installed RC version.
4. Publish RC4 only after the direct API, integration, artifact, documentation,
   and security gates pass on the exact verified commit. Stable promotion then
   reuses that accepted commit and does not reopen feature scope.

## Data And Contracts

- `src/test_data_agent/mcp_trino_server.py`: default tool registration and any
  explicit opt-in row capability.
- `src/test_data_agent/trino_masking.py`: no heuristic masking path may be
  presented as a guarantee that arbitrary source literals are absent.
- `src/test_data_agent/trino_client.py`, `trino_profiling.py`, and
  `trino_config.py`: typed shared invocation budget and enforcement points.
- `tests/fixtures/contracts/mcp-trino-tools.json` and Trino tests: updated
  default tool contract plus adversarial no-literal assertions.
- `openspec/specs/safe-mcp-workflow/spec.md` and MCP documentation: explicit
  aggregate-only/default versus opt-in/row-returning semantics.
- `README.md`, `docs/getting-started/installation.md`, and release checks:
  exact prerelease installation and clean public-artifact quickstart.
- Release metadata, changelog, attestations, container tags, and public
  acceptance evidence: all identify the exact `1.0.0rc4` commit/artifact.

The budget should be represented as a typed model rather than an unstructured
dictionary. It must cover at least maximum request bytes, SQL/formula
characters, AST nodes and depth, projected columns, statements, and response
bytes. Nested profiling receives the same budget instance, not a fresh budget
per column or query.

## Failure Modes

- An unsafe or over-budget request fails before opening a Trino connection or
  cursor whenever the required information is available at validation time.
- A budget exhausted during nested profiling stops the invocation and returns a
  bounded typed error; it must not continue with later columns or statements.
- A source-literal regression fails if any distinct test fixture value appears
  in the default MCP response, error, or audit payload.
- A row-returning capability is unavailable unless its explicit configuration,
  operator review, and audit requirements are satisfied.
- A public RC4 install or README smoke failure blocks stable promotion; no local
  checkout-only success is sufficient.
- Atomic publication continues to protect visibility and process-interruption
  recovery. Crash/power-loss durability remains an explicit documented
  decision, not an accidental guarantee.

## Alternatives

- Keep heuristic `sample_rows_masked` in the default surface: rejected because
  unknown literals can pass through unchanged.
- Add more per-query limits only: rejected because fan-out profiling can still
  exceed a safe invocation budget.
- Publish stable directly from the merged RC3 refactor: rejected until the P0
  privacy and P1 release-budget findings are closed.
- Promise fsync durability in this RC: deferred unless product requirements
  explicitly include crash/power-loss durability; otherwise document the
  current guarantee precisely.
