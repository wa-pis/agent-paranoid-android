Generate synthetic test data for related tables in a folder of CSV files.

* source folder: {input_folder_path}
* fresh agent workspace: {workspace_path}
* requested count: {count}
* output format: {csv/json/parquet}
* mode: {valid/mixed/negative}
* invalid ratio: {invalid_ratio}
* seed: {seed}
* business rules file, if any: {business_rules_path_or_none}

Use metadata and safe aggregates, never source rows as output. Review inferred
relationships, cardinality uncertainty and per-table counts. Do not infer links
solely because columns have similar names. First prepare a DatasetSpec, show
its assumptions and current fingerprint, and stop for my explicit human approval
of that exact specification. Then generate once and validate relationships and
business rules. Report artifact paths, manifest facts and validation status;
do not return source or generated rows in chat.
