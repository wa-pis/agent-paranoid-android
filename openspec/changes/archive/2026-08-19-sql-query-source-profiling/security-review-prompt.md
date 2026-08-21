# Independent review prompt: SQL query source boundary

Review the exact repository commit
`d3c2809b6f050c8443aa6b4920afd6aafefa2d10` as a Staff-level Python,
database-security, and privacy engineer. This is an AI-assisted independent
review, not a human approval.

Work read-only. Do not edit files, create commits, access live databases, make
paid/provider calls, or inspect credentials. You may run local no-network tests
that use synthetic fixtures.

## Scope

Focus on the PostgreSQL and Trino SQL-query profiling path and its adjacent
public boundaries, especially:

- `src/test_data_agent/adapters/database/sql_query_source.py`
- `src/test_data_agent/adapters/database/sql_query_profiling.py`
- `src/test_data_agent/adapters/database/sql_query_adapters.py`
- `src/test_data_agent/adapters/database/postgres_client.py`
- `src/test_data_agent/adapters/database/trino_client.py`
- `src/test_data_agent/adapters/config/postgres_config.py`
- `src/test_data_agent/adapters/config/trino_config.py`
- the CLI/Python wiring, tests, and OpenSpec for SQL query sources

Trace untrusted SQL text, literals, identifiers, backend errors, source values,
query rows, endpoints, and credentials from every source to every possible
profile, manifest, generated fixture, export, log, exception, provider, and MCP
sink.

## Required checks

1. Only the documented read-only SQL subset is accepted through parsed AST
   validation. Reject multi-statement SQL, comments used for statement
   smuggling, DDL/DML, CTE/subquery/UNION escapes, volatile or unsafe functions,
   and unsupported syntax fail closed.
2. Every physical source reference is schema/table/column allowlisted.
   Qualified wildcards expand only within those allowlists; there is no hidden
   arbitrary-SQL or unrestricted `SELECT *` path.
3. PostgreSQL and Trino execution remains read-only and resource-bounded across
   statement count, query bytes/complexity, tables, columns, aggregate work,
   response shape, timeouts, and returned metadata.
4. Profiling is metadata/aggregate-first. Source rows and query literals never
   enter generated output, profiles, manifests, logs/errors, providers, or
   default MCP responses.
5. Schema/type discovery, aliases, expressions, NULL handling, and unsupported
   backend types fail closed without exposing backend values or SQL text.
6. JDBC and component connection inputs do not weaken the same boundaries or
   expose credentials/endpoints in diagnostics.
7. Deterministic generation and validation consume only the source-free virtual
   entity profile; no source-row copy path exists.
8. Tests cover accepted PostgreSQL/Trino queries and adversarial bypasses at the
   real policy and adapter boundaries. Identify material missing regressions.

## Output contract

Start with findings ordered by severity. For every finding provide severity,
file and line, attack path, concrete impact, and the smallest safe fix. Do not
report style, governance, or speculative defense-in-depth suggestions as
release blockers.

Then provide:

- exact reviewed SHA;
- files and tests inspected;
- commands run and their results;
- limitations;
- an explicit final conclusion: `APPROVED` only if no unresolved Critical,
  High, or Medium defect exists, otherwise `BLOCKED`;
- a direct statement on arbitrary SQL, source-row return, allowlists, budgets,
  SQL/literal/credential egress, provider/MCP exposure, and fail-closed behavior.

Do not trust existing approval prose as evidence. Validate the code and tests
independently.
