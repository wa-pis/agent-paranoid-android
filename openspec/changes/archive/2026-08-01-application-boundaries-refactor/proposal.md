# Change Proposal: application-boundaries-refactor

## Summary

Decompose the large agent, CLI, and Trino orchestration modules into typed
application services, policy modules, ports, and thin transport adapters while
preserving public behavior and safety boundaries.

The target is a staged maintainability refactor after public RC2 acceptance
and before the stable 1.0 release. It is not a broad rewrite or permission to
change the frozen public contracts.

## Scheduling

Status: required before the stable 1.0 contract baseline is published. Deliver
the change through small, contract-preserving pull requests after RC2 public
acceptance. Complete every task and the full release gates before publishing a
new candidate that contains the refactor.

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
- Bundling the extraction into one pull request or relaxing the stable-release
  gates because the intended behavior is unchanged.

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
