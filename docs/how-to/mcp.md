# Connect An MCP Client

The project exposes two MCP servers with separate trust boundaries:

- the generator server reads and writes only inside one workspace;
- the Trino server's default aggregate-only tools provide allowlisted,
  read-only metadata and profiling.

Start with the generator server. Add Trino only when database profiling is
required.

For process and dependency isolation, use the separate hardened images in
[Container Deployment](../operations/containers.md). The generator example has
no network, while the Trino worker receives no generator workspace mount.

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

1. Put a CSV file, CSV folder, or safe profile below the workspace root.
2. Call `plan_dataset` with that source, a new agent workspace, count, seed,
   and output format.
3. Stop and review the written `dataset_spec.yaml`.
4. Call `inspect_dataset_plan` and record
   `review.current_spec_sha256`.
5. Call `approve_dataset_plan` with that exact fingerprint only after review.
6. Report summaries and artifact paths, not generated rows.

Use `profile_csv`, `infer_dataset_spec`, `generate_dataset`, and
`validate_dataset` separately when an advanced client needs control over each
pipeline stage.

For business rules, provide exactly one of `business_rules_path` or a bounded
structured `business_rules_payload`.

## Safe Trino Sequence

The default aggregate-only tools are source-literal-free and contain only
metadata and aggregate profiling operations:

- `list_catalogs`, `list_schemas`, `list_tables`, `describe_table`;
- `profile_table`, `profile_table_safe`, `profile_column`;
- `profile_foreign_key`, `profile_temporal_ordering`, `profile_formula_rule`;
- `profile_conditional_required`, `profile_conditional_allowed_values`;
- `profile_aggregate_mapping`.

This default aggregate-only surface has no row-returning diagnostic. Its
successful responses, validation and database errors, and metadata-only audit
records do not contain source-cell literals.

1. Call `list_catalogs`, `list_schemas`, and `list_tables`.
2. Call `describe_table`.
3. Call `profile_table_safe` for an allowlisted table.
4. Pass that response to generator `plan_trino_dataset` with a new workspace,
   explicit count, seed, and output format.
5. Stop and review the written `dataset_spec.yaml`.
6. Call `inspect_dataset_plan` and record `review.current_spec_sha256`.
7. Call `approve_dataset_plan` with that value as `reviewed_spec_sha256` only
   after the human reviewed that exact spec fingerprint.
8. Do not export or relay source rows.

Both catalog and schema allowlists are mandatory by default. HTTPS is the
default. Plain HTTP requires an explicit override and is intended only for an
isolated local Trino instance.

The explicit opt-in row-returning tool `run_safe_select` is not exposed by
default. Trusted clients that need it must set `TRINO_ENABLE_SAFE_SELECT=true`.
The review-first planning sequence above does not require it. Its bounded
row-shaped result may contain allowed source values, including values not
recognized as sensitive by heuristic masking.
Enabling it does not make returned rows source-free, PII-free, anonymous, or
privacy-safe; use a separately trusted client and do not relay its results to
an LLM or generated output.

## Expected Result

The default generator and default aggregate-only Trino tools return compact
metadata:

```text
rows: customers=25, orders=25
seed: 12345
validation: passed
synthetic: true
source rows copied: false
```

Generated files stay in the workspace. These default tools do not return
dataset or source rows; explicit opt-in row-returning tools are outside this
expected result.

## Failure Conditions

The server rejects:

- paths outside the workspace, including existing symlink escapes;
- existing output files and non-empty output directories;
- unrestricted SQL, DDL, DML, joins, CTEs, and subqueries;
- likely PII projections and raw sensitive rule literals;
- non-Trino or oversized inline planning profiles;
- DatasetSpec input passed to `plan_dataset` instead of `generate_dataset`;
- missing Trino allowlists;
- requests exceeding configured input, output, query, or execution limits.

See [MCP Tools](../mcp_examples.md) and
[Configuration](../reference/configuration.md) for details.
