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

The database role must already be read-only. The client also requests a
read-only transaction, TLS, statement and lock timeouts, and bounded aggregate
results. It accepts no arbitrary SQL and never profiles source rows.

Create a safe profile, review a generation specification, generate, and
validate:

```bash
test-data-agent profile-postgres --output out/postgres-profile.json
test-data-agent infer-spec out/postgres-profile.json --output out/dataset-spec.yaml
test-data-agent generate out/dataset-spec.yaml --seed 12345 --output out/generated
test-data-agent validate out/dataset-spec.yaml out/generated
test-data-agent export-postgres-sql out/dataset-spec.yaml --seed 12345 --output out/generated.sql
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
logs, or errors.

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
