# Runnable Local PostgreSQL Example

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
