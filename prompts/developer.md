The agent has access to safe MCP tools for Trino and optional generator/export tools.

Use Trino only for:

* metadata
* table descriptions
* aggregate profiling
* masked samples
* safe read-only SELECT queries

Do not use Trino for:

* production data export
* raw PII extraction
* arbitrary SQL execution
* write operations
* DDL operations

Preferred implementation flow:

1. describe_table
2. profile_table
3. profile_column for important fields
4. detect PII
5. build generation_spec
6. generate_from_spec
7. validate_dataset
8. export_dataset

Generated data must be:

* synthetic
* schema-compatible
* reproducible via seed
* safe for non-production testing

Final responses should include:

* source table
* output format
* row count
* seed
* mode
* invalid ratio, if relevant
* validation status
* assumptions
* confirmation that no production rows were copied
