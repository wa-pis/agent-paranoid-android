# Tasks

- [x] Select MCP 2.2.0 and update dependency policy and lockfile.
- [x] Adapt server creation, union models and request context in the shared adapter.
- [x] Preserve budget enforcement and redact unexpected SDK 2 failures.
- [x] Exercise real subprocess stdio and unchanged golden tool schemas.
- [x] Add real stdio regression to the minimum MCP CI profile.
- [ ] Pass the final release gate and supported Python/minimum dependency CI matrix.

Local evidence: transport regressions and real stdio pass with MCP 2.2.0 and
MCP 1.28.1. Tests use synthetic tool arguments and no external services.
The corrected minimum profile (Python 3.11, MCP 1.28.1, Pydantic 2.11.0)
passes all 61 transport and stdio tests without skips. MCP 1.0.0 is unsupported:
it lacks server and metadata APIs required by the bounded transport.
The 2026-09-23 Python 3.13 release gate passed: 1290 tests, 10 skipped,
90.29% coverage; lint, types, licenses, budgets, schema and quickstart passed.
