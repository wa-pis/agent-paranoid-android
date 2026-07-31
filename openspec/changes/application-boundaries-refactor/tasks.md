# Tasks: application-boundaries-refactor

- [ ] Inventory public imports, CLI commands, MCP tools, artifact contracts,
  and current dependency direction before moving code.
- [ ] Extract typed workspace persistence and atomic transition interfaces.
- [ ] Split agent lifecycle services into planning, review, approval, recovery,
  advising, status, and workspace-store modules.
- [ ] Split CLI composition/dispatch, doctor, command handlers, and centralized
  optional dependency resolution without changing parser/presenter contracts.
- [ ] Split Trino config, SQL policy, query builders, client, profiling, and
  masking; keep policy pure and builders non-executing.
- [ ] Preserve compatibility wrappers and add golden contract coverage for
  public Python, CLI, MCP, errors, artifacts, and safety behavior.
- [ ] Add architecture tests preventing transport-only enforcement, policy
  duplication, CLI/MCP imports from core services, and cyclic dependencies.
- [ ] Add direct-service adversarial tests for unsafe specs, paths, SQL, and
  provider payloads after each extraction.
- [ ] Document migration notes for any intentionally moved internal boundary.
- [ ] Run the full typing, lint, compile, test, package, and security gates.
