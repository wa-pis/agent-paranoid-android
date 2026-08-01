# Change Proposal: application-boundaries-refactor

## Summary

Decompose the large agent, CLI, and Trino orchestration modules into typed
application services, policy modules, ports, and thin transport adapters while
preserving public behavior and safety boundaries.

The target is a staged maintainability refactor after the release candidate,
not a broad rewrite or a reason to delay the RC security fixes.

## Scheduling

Status: explicitly deferred until after the stable 1.0 contract baseline is
published. The RC review found no concrete security blocker that requires this
decomposition. Resume the change in the first post-1.0 architecture cycle and
reassess immediately if an RC security fix cannot be isolated safely.

## Motivation

`agent.py`, `cli.py`, and `mcp_trino_server.py` currently combine composition,
dispatch, persistence, policy, transport, and orchestration responsibilities.
This makes direct-service safety harder to audit, increases regression risk,
and makes future contributors depend on accidental module boundaries.

## Scope

In scope:

- Split agent lifecycle services into planning, review, approval, recovery,
  advising, status, and workspace persistence responsibilities.
- Split CLI composition, dispatch, doctor, command handlers, and dependency
  resolution while retaining the parser and presenter boundaries.
- Split Trino configuration, SQL policy, query builders, client, profiling,
  and masking responsibilities.
- Keep filesystem persistence behind typed interfaces and make workspace
  transitions atomic.
- Add architectural dependency tests for forbidden transport/policy imports.
- Preserve public Python, CLI, MCP, exit-code, artifact, and safety contracts.

Out of scope:

- New CLI commands, MCP tools, providers, output formats, or generation modes.
- Moving security enforcement exclusively into a transport layer.
- A framework migration or broad dependency increase.
- Removing compatibility wrappers before their migration window is complete.
- Performing the refactor as part of the RC unless a narrowly scoped security
  fix requires it.

## Safety Impact

- Safety policy remains in reusable application/service boundaries and is
  exercised by direct Python calls as well as CLI/MCP transports.
- Trino policy validates SQL before client/cursor execution; query builders do
  not perform I/O, and masking remains independent of MCP.
- Workspace transitions retain atomic publication and cleanup guarantees.
- The refactor must not introduce raw rows, raw PII, unrestricted SQL, or
  secret-bearing logs at a new boundary.

## Compatibility

- Existing public imports and command names remain available through wrappers
  where module paths move.
- CLI exit codes, structured errors, MCP schemas, artifact filenames, and
  generation behavior remain contract-tested.
- Internal module paths may change only when they are not part of the public
  contract or a compatibility wrapper is retained.
