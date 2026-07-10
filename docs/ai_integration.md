# AI Integration

This project can be used by an AI agent in two practical modes:

1. As a local CLI tool.
2. Through two MCP servers that cover safe Trino profiling and synthetic data
   generation.

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

The Trino server is read-only and exposes safe metadata, aggregate profiling,
masked sampling, and bounded query tools:

```bash
python3 -m test_data_agent.mcp_trino_server
```

Its tools are:

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

The generator server exposes the local synthetic pipeline:

```bash
python3 -m test_data_agent.mcp_generator_server
```

Its tools are:

- `profile_csv`
- `infer_dataset_spec`
- `generate_dataset`
- `validate_dataset`
- `export_dataset`

`export_dataset` generates fresh data from a spec in the requested format. It
does not accept or convert arbitrary row files.

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
    },
    "test-data-agent-generator": {
      "command": "python3",
      "args": ["-m", "test_data_agent.mcp_generator_server"],
      "cwd": "/Users/agrudin/dev/my/agent-paranoid-android",
      "env": {
        "TEST_DATA_AGENT_WORKSPACE_ROOT": "/Users/agrudin/dev/my/agent-paranoid-android"
      }
    }
  }
}
```

Use a narrower workspace root in production-like environments. Every generator
tool path must remain below that root. Absolute or relative paths that escape it
are rejected, including escapes through existing symlinks. Output files must be
new, and generation folders must be new or empty.

## Recommended AI Workflow

An MCP-compatible AI client can run the complete workflow:

1. Inspect schemas through MCP.
2. Profile tables safely through MCP.
3. Pass the safe profile result directly as `profile_payload` to
   `infer_dataset_spec`, or save it as safe profile JSON inside the workspace.
4. Review the versioned `DatasetSpec` written by `infer_dataset_spec`.
5. Call `generate_dataset` or `export_dataset` with an explicit seed.
6. Call `validate_dataset` on the generated bundle.
7. Return a concise report with row count, seed, format, validation status, and
   confirmation that no production rows were copied.

The generator MCP responses return summaries and validation reports, not data
rows. Generated files stay in the configured workspace. Each bundle includes a
`generation_manifest.json` with its spec fingerprint, package version, schema
version, seed, format, row counts, validation status, and synthetic provenance.

The reasons for the two-server boundary, path restrictions, manifest checks,
and artifact ownership are documented in
[Generator MCP Design Rationale](mcp_generator_design.md).

## Local Demo

The included demo starts from a checked-in safe Trino profile and executes spec
inference, deterministic CSV generation, validation, and manifest creation:

```bash
python3 scripts/run_ai_demo.py \
  --profile examples/trino_safe_profile.json \
  --output out/ai_demo \
  --count 100 \
  --seed 12345
```
