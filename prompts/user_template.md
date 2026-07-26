Generate synthetic test data based on an existing Trino table.

Source:

* catalog: {catalog}
* schema: {schema}
* table: {table}

Requirements:

* row count: {count}
* output format: {csv/json/parquet}
* mode: {valid/mixed/negative/edge/load_test}
* invalid ratio: {invalid_ratio}
* seed: {seed}
* preserve approximate distributions: yes
* preserve referential integrity: {yes/no}
* include edge cases: yes
* copy production rows: no
* expose PII: no

Use the database only for schema, metadata, aggregate profiling, safe
distributions, and masked patterns. First create a reviewable DatasetSpec and
stop for my explicit approval. After approval, generate fully synthetic data
and validate it. Return artifact paths, manifest facts, and validation status;
do not return source or generated rows in chat.
