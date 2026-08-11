# Runnable Output-Format Example

This example generates the same fictional dataset as CSV, JSON, generic SQL,
and Parquet from one reviewed spec and seed. It also exports one executable
PostgreSQL DDL+INSERT file:

```bash
examples/output_formats/run.sh /tmp/agent-paranoid-output-formats
```

Run it from an installed environment with the `parquet` extra. Every format
folder contains freshly generated synthetic rows, a validation report, and a
generation manifest. The generic `sql` folder contains quoted `INSERT`
statements only. `postgres.sql` is the separate deterministic PostgreSQL
transaction with `CREATE TABLE` and `INSERT` statements. Both are generated
from validated synthetic records and never convert or export source rows.
