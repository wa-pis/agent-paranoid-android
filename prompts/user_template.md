Generate synthetic test data based on an existing Trino table.

Source:

* catalog: {catalog}
* schema: {schema}
* table: {table}

Requirements:

* fresh agent workspace: {workspace_path}
* row count: {count}
* output format: {csv/json/parquet}
* mode: {valid}
* invalid ratio: 0
* seed: {seed}
* preserve approximate distributions: yes
* preserve referential integrity: {yes/no}
* include edge cases: yes
* copy production rows: no
* expose PII: no

Use the database only for schema, metadata, aggregate profiling, safe
distributions, and masked patterns. First create a reviewable DatasetSpec,
show its current fingerprint, and stop for my explicit human approval
of that exact specification. After approval, generate fully synthetic data
and validate it. Return artifact paths, manifest facts, and validation status;
do not return source or generated rows in chat.

The MCP Trino planner starts in valid mode and has no mode/invalid-ratio
arguments. For other modes, edit the pending spec before my human review;
do not invent planner parameters.
