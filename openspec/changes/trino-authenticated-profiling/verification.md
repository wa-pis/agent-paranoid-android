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

The feedback follow-up runs 331 tests successfully, with one pre-existing
installed OAuth acceptance skip in the isolated environment. The new 31-test
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

The user tentatively identified installed version 1.6.0 and confirmed
username/password authentication on 2026-10-24. The supported `basic` mode uses
`TRINO_USER`, `TRINO_AUTH_METHOD=basic` and `TRINO_AUTH_SECRET_ENV` referencing
a separately supplied password variable over verified HTTPS. The historical
application settings and secret-reference presence remain unknown. A server
requiring a password does not prove that the application enabled this mode.
The historical external 401 remains unconfirmed; the
independent regression does not establish its cause or resolve server access.
Live authenticated acceptance remains pending: no live server or secret was
used. The public guide and credential-free environment example document the
existing authentication reference and safe failure handling. Full candidate CI
remains pending.

A second reproducer covers schema, row-count and column-summary failures in the
shared query profiler, for both SQL adapters. All six cases retained the raw
exception before the same detachment fix was applied there. This shared path
is exercised after Trino metadata discovery; fixing only the outer adapter
would leave those failures attached. PostgreSQL receives the same fixed error
on this shared path without changing its message or category.


## Merged candidate checkpoint

PR #640 passed full green CI and merged as
`b58eb02e46144a3d6d311ca81945dedcbad03cfb`. This supersedes the pending CI
statement above. A7 documentation and contract checks are complete. A3 historical
application-configuration evidence and live authenticated acceptance remain unavailable;
neither is inferred from fake-driver test success.


## Username/password clarification, 2026-10-24

After the user clarified the authentication requirement, the current
`test_trino_auth.py`, `test_trino_auth_feedback.py` and `test_trino_config.py`
suites passed all 91 cases offline against the candidate source. Coverage
includes Basic credential forwarding, verified HTTPS, missing/invalid secret
references and sanitized 401/403 failures. Both affected OpenSpec changes
validate strictly. No runtime change, live connection or credential collection
was needed; these checks do not reproduce the historical server rejection.
