# Design: application-boundaries-refactor

## Approach

Refactor incrementally from the current composition roots. First extract pure
policies and typed ports, then move one lifecycle or transport responsibility at
a time behind those interfaces. Keep compatibility wrappers thin and delete
them only after the documented migration window.

The dependency direction is:

```text
CLI/MCP transport → application services → policy/core → ports
                                      ↘ filesystem/database adapters
```

Transport adapters may translate arguments and render results, but they may
not be the only place where safety checks happen.

## Data And Contracts

- Agent application services: planning, review, approval, recovery, advising,
  status, and workspace store.
- CLI package: main composition root, dispatch, doctor, agent commands, dataset
  commands, and centralized optional dependency resolution.
- Trino package: config, pure SQL policy, non-executing query builders, client,
  profiling, and masking.
- Typed workspace transition and persistence interfaces with atomic commit and
  cleanup semantics.
- Architecture test rules for forbidden imports and direct unsafe boundaries.

## Failure Modes

- A dependency cycle blocks the change and must be resolved before merging.
- A moved public import or changed CLI/MCP result is a compatibility failure,
  not an incidental refactor detail.
- A filesystem or database failure must retain current cleanup, timeout, and
  audit behavior.
- Direct application calls that bypass CLI/MCP must still reject unsafe specs,
  SQL, paths, and provider payloads.

## Alternatives

### Keep the god modules and add more tests

Rejected as the long-term plan. Tests catch regressions but do not provide
clear ownership or prevent accidental dependency direction.

### Rewrite all orchestration at once

Rejected. A staged extraction makes compatibility and safety evidence reviewable
per change.

### Put policy in each transport

Rejected. It duplicates security logic and recreates the bypass risk this
refactor is intended to remove.
