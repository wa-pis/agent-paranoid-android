# Runnable Local Trino Example

> Stable `1.3.1` includes the baseline `run.sh` workflow plus `run-jdbc.sh`,
> `run-wildcard.sh`, and `run-query.sh`.

This launcher starts a pinned disposable Trino container with its built-in
synthetic TPC-H `tiny` catalog, profiles `tpch.tiny.nation` through bounded
read-only operations, writes a reviewable spec, and generates twelve fresh
synthetic JSON rows:

```bash
examples/local_trino/run.sh /tmp/agent-paranoid-trino-example
```

Run the identical workflow with endpoint/catalog/schema supplied in JDBC
syntax:

```bash
examples/local_trino/run-jdbc.sh /tmp/agent-paranoid-trino-jdbc-example
```

Run the same workflow with a `tpch.tiny.nation.*` profiling selector:

```bash
examples/local_trino/run-wildcard.sh /tmp/agent-paranoid-trino-wildcard-example
```

Run the checked-in reviewed `query.sql` through the aggregate-only query-source
pipeline:

```bash
examples/local_trino/run-query.sh /tmp/agent-paranoid-trino-query-example
```

The JDBC-style launcher still uses the Python Trino client and the same
allowlisted, bounded aggregate operations. It adds no Java runtime or JDBC
driver.
The wildcard is expanded from bounded `information_schema` metadata before
aggregate queries run. It does not authorize category literals, row return, or
SQL projection stars.
The query launcher requires the exact table-column allowlist, writes a query
fingerprint instead of SQL text, and never exports the derived result rows.

Docker and an installed `agent-paranoid-android[trino]` environment are
required. Set `TRINO_EXAMPLE_PORT` when port `18080` is unavailable. The
container is removed on success or failure.

The checked-in workflow never exports TPC-H rows. Trino returns schema and
aggregate profile metadata; the local generator creates new values from the
reviewable `DatasetSpec`. Inspect `profile.json`, `dataset_spec.yaml`,
`generated/validation_report.json`, and `generated/generation_manifest.json`.
