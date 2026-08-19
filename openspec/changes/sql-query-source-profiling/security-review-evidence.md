# SQL query source security review evidence

## Review identity

- Reviewer stable pseudonym: **opencode-nemotron-3-ultra-free-sql-query-1-3**
- Runtime: **OpenCode 1.18.15 using Nemotron 3 Ultra Free**
- Reviewed commit: **`d3c2809b6f050c8443aa6b4920afd6aafefa2d10`**
- Review date: **2026-08-19 UTC**
- Review mode: read-only inspection in a disposable clone, local synthetic and
  no-network tests only
- Prompt: [security-review-prompt.md](security-review-prompt.md)
- Public review record: [GitHub issue #461](https://github.com/wa-pis/agent-paranoid-android/issues/461)

This is an AI-assisted independent review, not a human-review claim or a
waiver. The external model received the bounded repository source needed to
review this boundary after the repository owner explicitly approved that
destination. No credentials, tokens, production data, live database, or paid
provider call was used.

The prompt initially named three modules under an assumed
`adapters/database/` package. The reviewer found and inspected their actual
locations at `src/test_data_agent/sql_query_source.py`,
`sql_query_profiling.py`, and `sql_query_adapters.py`; the raw review records
that correction rather than hiding it.

## Scope and conclusion

The review traced SQL text, SQL literals, source identifiers, backend errors,
source values, result rows, endpoints, and credentials across the PostgreSQL
and Trino query-source policy, configuration, clients, trusted query builders,
CLI/Python wiring, profile output, generation, provider, and MCP boundaries.

**OpenCode conclusion: APPROVED.** It found no unresolved Critical, High, or
Medium defect. It concluded that arbitrary SQL and source-row return paths are
blocked; table and column allowlists and resource budgets are enforced; query
profiling is metadata/aggregate-first; generated data consumes a source-free
virtual profile; and SQL, literals, credentials, backend values, and source
rows do not reach providers, default MCP, profiles, manifests, generated
fixtures, logs, or user-facing errors.

## Commands and results

The reviewer ran the following checks against the disposable exact-commit
clone:

```text
focused query source/profile/adapter tests: 33 passed
query/config/policy/client/budget tests:     158 passed
Trino direct SQL policy tests:                14 passed
PostgreSQL and Trino client tests:            30 passed
full tests excluding integration:           1226 passed, 4 failed
```

The four full-suite failures were example-launcher environment failures: the
disposable source clone did not have the package's installed console scripts
on its runtime path. They did not exercise or fail the SQL policy boundary.
The separately completed installed-wheel acceptance matrix covers PostgreSQL
component, JDBC, qualified wildcard, and query modes locally, while CI covers
the same four Trino modes against a disposable synthetic service.

The disposable review clone had no tracked or untracked changes after the
review.

## Reviewer observations and maintainer dispositions

### Low: parser comment attachment

The reviewer noted that comment rejection currently relies on comments being
attached to nodes by the pinned `sqlglot` parser. Current adversarial tests
prove comments are rejected, and the AST policy accepts only one parsed
statement and a closed node/function subset. A separate lexical comment check
could add defense in depth if parser behavior or the pin changes. This is a
non-blocking Low observation, not a demonstrated bypass.

### Informational: shared Trino unrestricted mode

`TrinoConfig` retains the pre-existing explicit unrestricted mode for other
surfaces. Query-source profiling rejects that mode before client execution and
requires exact table-column selectors. No query-source bypass exists; no
change is required for this OpenSpec.

### False positive: PostgreSQL wildcard column overflow

The reviewer initially suggested that the discovery probe's
`LIMIT max_columns + 1` could silently truncate a table with too many columns.
The source-to-sink follow-up found the downstream enforcement it had missed:
`with_resolved_postgres_columns()` validates the resolved snapshot through
`PostgresConfig.validate()`, and `_validate_resolved_columns()` rejects any
snapshot larger than `max_columns`. The extra row is an overflow sentinel and
the path fails closed. No finding remains.

### Informational: quoted Trino metadata relation

The reviewer confirmed that catalog interpolation in the Trino
`information_schema.columns` relation uses `quote_identifier()`, which first
applies the strict identifier policy, while schema and table remain bound
parameters. It found no injection path and recommended no change.

## Limitations

- The OpenCode run did not start live PostgreSQL or Trino. Disposable live
  acceptance is recorded separately in the implementation PR/CI evidence.
- Driver enforcement of PostgreSQL transaction read-only and Trino session
  limits was inspected through client code and fake-driver tests; the model did
  not independently instrument either driver.
- The review was focused on the query-source boundary. The separately opt-in
  Trino row-returning MCP tool was checked only for separation from this path,
  not re-audited as a full independent surface.

## Final disposition

**APPROVED.** Commit `d3c2809b6f050c8443aa6b4920afd6aafefa2d10`
has no unresolved Critical, High, or Medium defect in the SQL query-source
policy or source-to-sink privacy boundary. The accepted Low observation does
not provide an exploit path under the pinned parser and tested policy. Stable
release approval remains a separate exact-candidate decision.
