# Profile PostgreSQL

Install the optional driver:

```bash
pip install "agent-paranoid-android[postgres]"
```

Configure one explicit read-only scope. The password setting names another
environment variable; it is not the password itself.

```bash
export POSTGRES_SOURCE_ID=warehouse
export POSTGRES_HOST=db.example.internal
export POSTGRES_DATABASE=analytics
export POSTGRES_USER=test_data_agent
export POSTGRES_PASSWORD_ENV=WAREHOUSE_PASSWORD
export WAREHOUSE_PASSWORD='replace-in-your-shell'
export POSTGRES_ALLOWED_SCHEMAS=public
export POSTGRES_ALLOWED_TABLES=public.customers,public.orders
export POSTGRES_ALLOWED_COLUMNS=public.customers.customer_id,public.customers.status,public.orders.order_id,public.orders.customer_id,public.orders.state
```

For an intentionally table-wide aggregate profile, an entry may instead use
the exact `schema.table.*` form:

```bash
export POSTGRES_ALLOWED_COLUMNS='public.customers.*,public.orders.*'
```

The parent tables must still appear exactly in `POSTGRES_ALLOWED_TABLES`.
Before any aggregate runs, bounded PostgreSQL catalog metadata expands each
wildcard into a frozen, sorted explicit-column snapshot. Profiling queries
enumerate quoted column identifiers; they never execute `SELECT *`. Bare,
schema-wide, table-name, embedded, or over-budget wildcards fail closed.

If a platform portal supplies a JDBC endpoint, replace only the separate host,
port, database, and TLS settings with a credential-free JDBC-style URL:

```bash
export POSTGRES_JDBC_URL='jdbc:postgresql://db.example.internal:5432/analytics?sslmode=verify-full'
```

Keep `POSTGRES_USER`, `POSTGRES_PASSWORD_ENV`, every allowlist, and every budget
separate. Userinfo, passwords, unknown query properties, and session-changing
options in the URL fail before a connection is opened. This syntax is parsed
into the existing Psycopg adapter; Java and JDBC drivers are not used. If both
URL and component settings are present, explicitly supplied values must match.

The database role must already be read-only. The client also requests a
read-only transaction, TLS, statement and lock timeouts, and bounded aggregate
results. It accepts no arbitrary SQL and never profiles source rows.

Create a safe profile, review a generation specification, generate, and
validate. Output paths must not already exist unless the command explicitly
supports `--overwrite`:

```bash
test-data-agent profile-postgres --output out/postgres-profile.json
test-data-agent infer-spec out/postgres-profile.json --output out/dataset-spec.yaml
test-data-agent generate out/dataset-spec.yaml --seed 12345 --output out/generated
test-data-agent validate out/dataset-spec.yaml out/generated
test-data-agent export-postgres-sql out/dataset-spec.yaml --seed 12345 --output out/generated.sql
```

Run the SQL only in the intended local or disposable target database:

```bash
psql --set ON_ERROR_STOP=1 --dbname synthetic_target --file out/generated.sql
```

The SQL file contains one transaction, deterministic quoted `CREATE TABLE`,
foreign-key, and `INSERT` statements, PostgreSQL scalar literals, and `NULL`.
It is built from validated generated records, not profile query rows. Render or
validation failure leaves no partial output file. Repeating export with the
same reviewed spec, seed, package, and recorded environment produces the same
logical SQL; compare files directly when verifying one environment:

```bash
test-data-agent export-postgres-sql out/dataset-spec.yaml \
  --seed 12345 --output out/generated-second.sql
cmp out/generated.sql out/generated-second.sql
```

To profile a reviewed derived relation without creating a database view, put
one fully qualified single-table query in a local file:

```sql
SELECT o.order_id, o.state, o.amount * 2 AS doubled_amount
FROM public.orders AS o
WHERE o.order_id < 999999
```

Keep the same physical schema/table/column allowlists and run:

```bash
test-data-agent profile-query query.sql \
  --adapter postgres \
  --source-id warehouse \
  --entity orders_query \
  --output out/query-profile.json
test-data-agent infer-spec out/query-profile.json \
  --output out/query-spec.yaml
test-data-agent generate out/query-spec.yaml \
  --seed 12345 --output out/query-generated
test-data-agent validate out/query-spec.yaml out/query-generated
```

The query is parsed locally and must stay inside the documented scalar,
projection, and filter subset. A no-row schema probe and bounded aggregate
wrappers execute in the forced read-only session. The profile contains a query
fingerprint but not the SQL text, its literal, backend messages, or query rows.

The equivalent typed Python entry point keeps the query path and database
configuration explicit:

```python
from pathlib import Path

import psycopg

from test_data_agent import (
    SqlQueryAdapter,
    SqlQueryProfileRequest,
    profile_postgres_query_source,
)
from test_data_agent.postgres_config import PostgresConfig

request = SqlQueryProfileRequest(
    adapter=SqlQueryAdapter.POSTGRES,
    source_id="warehouse",
    entity="orders_query",
    query_file=Path("query.sql"),
)
profile = profile_postgres_query_source(
    request,
    config=PostgresConfig.from_env(),
    driver=psycopg,
)
```

Exact values remain disabled by default. A bounded, reviewed, non-sensitive
business enum can be kept locally with its source-qualified identity:

```bash
test-data-agent profile-postgres \
  --local-category warehouse.public.orders.state \
  --output out/postgres-profile.json
```

PII, secrets, identifiers, quasi-identifiers, free text, excessive cardinality,
and long values fail closed. Original literals are not sent to providers, MCP,
logs, or errors. A column wildcard is not a local-value policy: exact values
are considered only when the separate, fully qualified `--local-category`
selector is present and its content checks pass.

The selector authorizes only the bounded value domain and aggregate counts. It
does not retain source row order or a mapping that reconstructs source rows.
The generated SQL may contain approved values because its input is the
validated synthetic dataset.

The same profiling boundary is available from Python:

```python
import psycopg

from test_data_agent.postgres_client import PostgresClient
from test_data_agent.postgres_config import PostgresConfig
from test_data_agent import generate_dataset, infer_dataset_spec, validate_dataset
from test_data_agent.postgres_profiler import dataset_profile_from_postgres

config = PostgresConfig.from_env()
profile = dataset_profile_from_postgres(PostgresClient(config, psycopg))
spec = infer_dataset_spec(profile)
# Review or edit spec here before generation.
rows = generate_dataset(spec, seed=12345)
report = validate_dataset(rows, spec)
assert report.valid
```

Keep profile and generated artifacts local unless their destination policy
explicitly permits otherwise.

For a complete synthetic end-to-end check against a temporary local
PostgreSQL cluster, run the
[`examples/local_postgres`](https://github.com/wa-pis/agent-paranoid-android/tree/main/examples/local_postgres)
example. It creates a SELECT-only role, proves that writes are denied, profiles
two related tables, validates deterministic generation, executes the exported
SQL in an empty target database, and removes the cluster. Run
`examples/local_postgres/run-jdbc.sh OUTPUT` for the same workflow configured by
a placeholder JDBC-style URL, or `examples/local_postgres/run-wildcard.sh
OUTPUT` for bounded table-qualified wildcard expansion. Run
`examples/local_postgres/run-query.sh OUTPUT` for the reviewed query-file path.
