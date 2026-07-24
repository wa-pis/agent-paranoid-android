# Connect An MCP Client

The project exposes two MCP servers with separate trust boundaries:

- the generator server reads and writes only inside one workspace;
- the Trino server provides allowlisted, read-only metadata and profiling.

Start with the generator server. Add Trino only when database profiling is
required.

## Prepare A Workspace

```bash
mkdir -p /path/to/synthetic-workspace
```

Inputs, safe profiles, reviewed specs, rules, and outputs used through generator
MCP tools must remain below this directory.

## MCP Client Configuration

Use the installed console commands:

```json
{
  "mcpServers": {
    "test-data-agent-generator": {
      "command": "test-data-agent-mcp-generator",
      "env": {
        "TEST_DATA_AGENT_WORKSPACE_ROOT": "/path/to/synthetic-workspace"
      }
    },
    "test-data-agent-trino": {
      "command": "test-data-agent-mcp-trino",
      "env": {
        "TRINO_HOST": "trino.example.internal",
        "TRINO_PORT": "443",
        "TRINO_USER": "synthetic_data_reader",
        "TRINO_HTTP_SCHEME": "https",
        "TRINO_ALLOWED_CATALOGS": "hive,iceberg",
        "TRINO_ALLOWED_SCHEMAS": "test_data,staging",
        "TRINO_QUERY_MAX_EXECUTION_TIME": "30s",
        "TRINO_QUERY_MAX_RUN_TIME": "45s",
        "TRINO_QUERY_MAX_SCAN_PHYSICAL_BYTES": "1GB"
      }
    }
  }
}
```

Do not place a password or token directly in a committed MCP configuration.
Use the client's secret mechanism or an environment injected by the runtime.

## Safe Generator Sequence

1. Call `profile_csv` with a CSV path and a new profile path.
2. Call `infer_dataset_spec` with that safe profile.
3. Stop and review the written `DatasetSpec`.
4. Call `generate_dataset` with an explicit seed.
5. Call `validate_dataset`.
6. Report summaries and artifact paths, not generated rows.

For business rules, provide exactly one of `business_rules_path` or a bounded
structured `business_rules_payload`.

## Safe Trino Sequence

1. Call `list_catalogs`, `list_schemas`, and `list_tables`.
2. Call `describe_table`.
3. Use `profile_table_safe`, `profile_column`, and aggregate rule-profiling
   tools.
4. Pass the safe profile payload to generator `infer_dataset_spec`.
5. Do not export or relay source rows.

Both catalog and schema allowlists are mandatory by default. HTTPS is the
default. Plain HTTP requires an explicit override and is intended only for an
isolated local Trino instance.

## Expected Result

MCP responses contain compact metadata:

```text
rows: customers=25, orders=25
seed: 12345
validation: passed
synthetic: true
source rows copied: false
```

Generated files stay in the workspace. Dataset rows are not returned through
MCP responses.

## Failure Conditions

The server rejects:

- paths outside the workspace, including existing symlink escapes;
- existing output files and non-empty output directories;
- unrestricted SQL, DDL, DML, joins, CTEs, and subqueries;
- likely PII projections and raw sensitive rule literals;
- missing Trino allowlists;
- requests exceeding configured input, output, query, or execution limits.

See [MCP Tools](../mcp_examples.md) and
[Configuration](../reference/configuration.md) for details.
