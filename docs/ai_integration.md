# AI Integration

This project can be used by an AI agent in two practical modes:

1. As a local CLI tool.
2. As an MCP server that exposes safe Trino inspection and profiling tools.

## CLI Mode

An AI agent with shell access can call the local command-line interface:

```bash
test-data-agent profile-example ...
test-data-agent infer-spec ...
test-data-agent generate ...
test-data-agent validate ...
```

In this mode, the AI plans the workflow, builds or edits a `DatasetSpec`, runs
deterministic generation, validates the output, and reports the result.

Install the package locally first:

```bash
python3 -m pip install -e ".[dev]"
```

## MCP Mode

The repository already includes a Trino MCP server:

```bash
python3 -m test_data_agent.mcp_trino_server
```

It exposes safe tools for Trino metadata and profiling:

- `list_catalogs`
- `list_schemas`
- `list_tables`
- `describe_table`
- `profile_table`
- `profile_table_safe`
- `profile_column`
- `profile_foreign_key`
- `profile_temporal_ordering`
- `profile_formula_rule`
- `profile_conditional_required`
- `profile_conditional_allowed_values`
- `profile_aggregate_mapping`
- `sample_rows_masked`
- `run_safe_select`

Example MCP client configuration:

```json
{
  "mcpServers": {
    "test-data-agent-trino": {
      "command": "python3",
      "args": ["-m", "test_data_agent.mcp_trino_server"],
      "cwd": "/Users/agrudin/dev/my/agent-paranoid-android",
      "env": {
        "TRINO_HOST": "trino.example.internal",
        "TRINO_PORT": "443",
        "TRINO_USER": "your_user",
        "TRINO_HTTP_SCHEME": "https",
        "TRINO_ALLOWED_CATALOGS": "hive,iceberg",
        "TRINO_ALLOWED_SCHEMAS": "dev,test,staging"
      }
    }
  }
}
```

## Recommended AI Workflow

Use the MCP server for safe source inspection, then use the CLI or Python API
for generation and validation:

1. Inspect schemas through MCP.
2. Profile tables safely through MCP.
3. Build a `DatasetSpec`.
4. Generate synthetic data with the CLI.
5. Validate generated data with the CLI.
6. Return a concise report with row count, seed, format, validation status, and
   confirmation that no production rows were copied.

## Current Limitation

The current MCP server focuses on safe Trino access: schema metadata, aggregate
profiling, masked samples, safe bounded selects, and rule profiling.

Generation, export, and validation are implemented today as CLI and Python APIs,
not as MCP tools.

## Next Integration Step

A useful next step is to add a second MCP server, for example
`test_data_agent.mcp_generator_server`, with tools such as:

- `profile_csv`
- `infer_dataset_spec`
- `generate_dataset`
- `validate_dataset`
- `export_dataset`

That would let an AI client run the full synthetic data pipeline through MCP
without shell commands.
