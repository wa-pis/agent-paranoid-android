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
- [ ] Split CLI composition/dispatch, doctor, command handlers, and centralized
  optional dependency resolution without changing parser/presenter contracts.
  - [x] Extract installation diagnostics and capability smoke orchestration.
  - [ ] Extract composition and command dispatch.
  - [x] Extract agent command handlers.
  - [x] Extract dataset and utility command handlers.
  - [x] Centralize optional dependency resolution.
- [ ] Split Trino config, SQL policy, query builders, client, profiling, and
  masking; keep policy pure and builders non-executing.
- [ ] Preserve compatibility wrappers and add golden contract coverage for
  public Python, CLI, MCP, errors, artifacts, and safety behavior.
- [ ] Add architecture tests preventing transport-only enforcement, policy
  duplication, CLI/MCP imports from core services, and cyclic dependencies.
- [ ] Add direct-service adversarial tests for unsafe specs, paths, SQL, and
  provider payloads after each extraction.
- [ ] Document migration notes for any intentionally moved internal boundary.
- [ ] Run the full typing, lint, compile, test, package, documentation, and
  security gates.
- [ ] Merge applicable OpenSpec deltas into the canonical baseline and archive
  this change after every task is complete.
