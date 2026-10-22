# Current authentication verification

All production Trino DB-API connections converge in `TrinoClient._query_rows`.
Callers include SQL-query adapters, MCP construction and the existing gated
transformation streaming adapter. `TrinoConfig.from_env` supplies runtime auth
configuration. The client builds the auth object before connection, requires
verified HTTPS, and shares the existing query/result/deadline budgets.
OAuth2 additionally uses its bounded same-origin HTTPS session and requires an
explicit local redirect handler. No caller receives a new permission here.

`tests/test_trino_auth.py`, `test_trino_oauth_cli.py`, `test_trino_client.py`,
`test_trino_config.py`, `test_trino_query_builders.py`, `test_trino_work_budget.py`
and SQL query profiling were rerun together with CLI/parser/presenter regressions:
259 passed, one skipped because the isolated OAuth registration candidate is
unavailable. Fake drivers cover runtime secrets, TLS propagation, typed auth
failure detachment, resource closure, credential-free endpoint parsing, optional
integrated auth, nondelegation, value-free diagnostics and OAuth origin/deadlines.

The public Trino guide already links the existing authentication reference.
The reported external 401 still needs the actual installed version and sanitized
configuration evidence. These tests do not establish real server compatibility,
all possible 401/403 error categories, or complete transport/audit canary coverage.
Those checklist items remain open. No live server or secret was used.
