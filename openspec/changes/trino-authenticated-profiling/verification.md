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

The feedback follow-up runs 293 tests successfully, with one pre-existing
installed OAuth acceptance skip in the isolated environment. The new 25-test
matrix covers HTTP 401/403 and TLS failures at connect, execute and fetch;
missing, empty, multiline and oversized Basic/JWT secrets; all authenticated
modes rejecting HTTP overrides; URL credentials and missing certificate files.
Fictional canaries are absent from public exception repr/tracebacks, cause and
context, CLI JSON, captured logs and signed MCP audit records. Failed CLI
profiling preserves an existing output artifact. No failed profile is published.

The untyped-driver test first reproduced a retained `__context__` in SQL-query
profiling, then passed after raising the same fixed error outside the handler.
The existing MCP boundary already detached it. No auth mode, TLS policy,
allowlist, budget, public error category or default changed.

The user tentatively identified installed version 1.6.0 but cannot supply the
authentication method. The historical external 401 remains unconfirmed; the
independent regression does not establish its cause or resolve server access.
Live authenticated acceptance remains pending: no live server or secret was
used. The public guide and credential-free environment example document the
existing authentication reference and safe failure handling. Full candidate CI
remains pending.
