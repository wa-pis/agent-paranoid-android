# Runnable Local PostgreSQL Example

> Stable `1.3.1` includes the baseline `run.sh` workflow plus `run-jdbc.sh`,
> `run-wildcard.sh`, and `run-query.sh`.

This example creates a disposable local PostgreSQL cluster with two related
synthetic tables, a SELECT-only profiling role, and an empty target database.
It then runs the complete workflow:

```text
profile-postgres -> infer-spec -> generate -> validate
                 -> export-postgres-sql -> psql target
```

Run it from an installed `agent-paranoid-android[postgres]` environment:

```bash
examples/local_postgres/run.sh /tmp/agent-paranoid-postgres-example
```

Run the same workflow with a credential-free JDBC-style endpoint:

```bash
examples/local_postgres/run-jdbc.sh /tmp/agent-paranoid-postgres-jdbc-example
```

Run it with table-qualified column wildcards that are expanded through bounded
metadata into explicit columns before aggregate profiling:

```bash
examples/local_postgres/run-wildcard.sh /tmp/agent-paranoid-postgres-wildcard-example
```

Run the checked-in reviewed `query.sql` as one virtual aggregate-only source:

```bash
examples/local_postgres/run-query.sh /tmp/agent-paranoid-postgres-query-example
```

The second launcher changes only endpoint configuration. It still uses the
Python Psycopg adapter, mandatory exact allowlists, the same fixed seed, and the
same disposable synthetic databases; no Java or JDBC driver is involved.
The wildcard launcher changes only the column authorization syntax. Executed
profiling SQL still enumerates quoted columns and never uses a projection star.
The query launcher records only a SHA-256 query fingerprint and policy version
in its profile. It never writes query text, query literals, backend messages,
endpoints, or result rows to artifacts.

Requirements are `initdb`, `pg_ctl`, `psql`, and either the installed
`test-data-agent` command or `TDA_PYTHON=/path/to/python`. Set
`POSTGRES_EXAMPLE_PORT` when port `55432` is unavailable.

The script uses trust authentication only inside the temporary localhost-only
cluster. It proves that the profiling role cannot insert, applies mandatory
schema/table/column allowlists and narrow resource budgets, and enables exact
values only for the reviewed synthetic `orders.state` enum. The customer
status field remains synthetic.

On success, the output directory contains the safe profile, reviewed spec,
generated JSON bundle, and two byte-identical PostgreSQL SQL files. The script
also executes one file in the empty target database and verifies row counts,
foreign-key coverage, the approved enum domain, and replacement of the
non-allowlisted category. The temporary cluster and all database files are
removed on success or failure.
