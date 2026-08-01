# Tasks: application-boundaries-refactor

Target: required before the stable 1.0 release and delivered as small,
contract-preserving increments.

- [x] Inventory public imports, CLI commands, MCP tools, artifact contracts,
  and current dependency direction before moving code.
- [x] Extract typed workspace persistence and atomic transition interfaces.
- [x] Split agent lifecycle services into planning, review, approval, recovery,
  advising, status, and workspace-store modules.
  - [x] Extract neutral agent contracts and the planning lifecycle service.
  - [x] Extract the metadata-only review lifecycle service.
  - [x] Extract the approval lifecycle service.
  - [x] Extract the recovery lifecycle service.
  - [x] Extract the metadata-only advising lifecycle service.
  - [x] Extract the status lifecycle service.
- [x] Split CLI composition/dispatch, doctor, command handlers, and centralized
  optional dependency resolution without changing parser/presenter contracts.
  - [x] Extract installation diagnostics and capability smoke orchestration.
  - [x] Extract composition and command dispatch.
  - [x] Extract agent command handlers.
  - [x] Extract dataset and utility command handlers.
  - [x] Centralize optional dependency resolution.
- [x] Split Trino config, SQL policy, query builders, client, profiling, and
  masking; keep policy pure and builders non-executing.
  - [x] Extract validated connection and resource-budget configuration.
  - [x] Extract pure SQL and allowlist policy.
  - [x] Extract non-executing metadata and profiling query builders.
  - [x] Extract the bounded Trino client boundary.
  - [x] Extract profiling orchestration.
  - [x] Extract masking and safe category summaries.
- [ ] Preserve compatibility wrappers and add golden contract coverage for
  public Python, CLI, MCP, errors, artifacts, and safety behavior.
- [x] Add architecture tests preventing transport-only enforcement, policy
  duplication, CLI/MCP imports from core services, and cyclic dependencies.
- [x] Add direct-service adversarial tests for unsafe specs, paths, SQL, and
  provider payloads after each extraction.
  - [x] Reject symlinked workspace targets at the persistence boundary before
    plan staging.
  - [x] Reject unsafe specs at the approval service before injected generation.
  - [x] Reject unsafe SQL at the masking service before injected Trino access.
  - [x] Reject unsafe provider payloads before advisor review persistence.
- [ ] Document migration notes for any intentionally moved internal boundary.
- [ ] Run the full typing, lint, compile, test, package, documentation, and
  security gates.
- [ ] Merge applicable OpenSpec deltas into the canonical baseline and archive
  this change after every task is complete.
