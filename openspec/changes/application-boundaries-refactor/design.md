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

- The pre-refactor inventory is maintained in
  `docs/reference/application-boundaries.md` and checked against the golden
  Python, CLI, MCP, and artifact fixtures before code moves.
- Agent application services: planning, review, approval, recovery, advising,
  status, and workspace store.
- `agent_contracts.py` owns transport-neutral lifecycle models;
  `agent_planning.py` owns safe profile-to-plan orchestration. Existing imports
  continue through thin `agent.py` and `workspace_store.py` compatibility
  exports while later lifecycle services are extracted.
- `agent_review.py` owns metadata-only review reports and fingerprint refresh
  checks. It receives the workspace-status inspector as a typed callable so it
  does not import the compatibility composition module.
- `agent_approval.py` owns fingerprint-gated approval and completion
  publication. It receives workspace inspection and deterministic generation as
  typed callables so direct service use preserves the same safety gate.
- `agent_recovery.py` owns interrupted-publication recovery and recovery-state
  inspection. It receives completion-bundle validation as a typed callable and
  reuses the same approval publication boundary.
- `agent_advising.py` owns safe request/exchange creation and fingerprint-bound
  proposal persistence. It receives workspace inspection as a typed callable
  and remains metadata-only.
- `agent_status.py` owns read-only reconstruction of planned, recoverable, and
  completed lifecycle state from bounded workspace artifacts.
- CLI package: main composition root, dispatch, doctor, agent commands, dataset
  commands, and centralized optional dependency resolution.
- `cli_doctor.py` owns installation diagnostics and redacted capability smoke
  orchestration behind injected import and smoke callables.
- `cli_dependencies.py` owns the optional-extra module catalog, availability
  inspection, and normalized installation errors for CLI services.
- Trino package: config, pure SQL policy, non-executing query builders, client,
  profiling, and masking.
- Typed workspace transition and persistence interfaces with atomic commit and
  cleanup semantics.
- The filesystem workspace adapter stages a complete plan beside its final
  path and publishes it with one directory rename. Completion keeps
  `agent_result.json` as the last atomic state marker so interrupted runs stay
  recoverable from generated checkpoints.
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
