Generate synthetic test data based on an existing Trino table.

Source:

* catalog: {catalog}
* schema: {schema}
* table: {table}

Requirements:

* row count: {count}
* output format: {csv/json/parquet/sql}
* mode: {valid/mixed/negative/edge/load_test}
* invalid ratio: {invalid_ratio}
* seed: {seed}
* preserve approximate distributions: yes
* preserve referential integrity: {yes/no}
* include edge cases: yes
* copy production rows: no
* expose PII: no

Use the database only for schema, metadata, aggregate profiling, safe distributions, and masked patterns. Generate fully synthetic data. Validate the output and return the generation specification plus validation report.
