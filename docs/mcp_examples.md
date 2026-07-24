# MCP Examples

These examples show the intended safe shape of MCP workflows. Tool responses
return summaries, paths, row counts, validation status, and manifest context,
not source rows or generated rows.

## Local CSV Folder To Synthetic Dataset

1. Start the generator server with a narrow workspace root:

```bash
TEST_DATA_AGENT_WORKSPACE_ROOT=/path/to/workspace \
  python3 -m test_data_agent.mcp_generator_server
```

2. Ask the MCP client to call `profile_csv` for individual CSV files, or use
   local CLI folder profiling when starting from a folder.
3. Call `infer_dataset_spec` with a safe `profile_path` or safe inline
   `profile_payload`.
4. Review the written `DatasetSpec`.
5. Optionally provide reviewed business rules through one
   `business_rules_path` or structured `business_rules_payload`.
6. Call `generate_dataset` with an explicit seed and output folder.
7. Call `validate_dataset` for the generated bundle.

Expected final report:

```text
rows: customers=25, orders=25
seed: 12345
validation: passed
synthetic: true
source rows copied: false
```

For a rule-driven run, the response also includes a compact
`business_validation` object and `business_validation_report_path`. The
manifest stores the same summary and the SHA-256 fingerprint of the normalized
rule contract.

Example inline payload:

```json
{
  "field_rules": [
    {
      "table": "customers",
      "field": "status",
      "required": true,
      "allowed_values": ["active", "paused"]
    }
  ]
}
```

Inline and file inputs are size-bounded. Unknown keys, missing entities or
fields, unsupported formula syntax, and concrete PII or secret values are
rejected before an output folder is created.

## Trino Profile To Synthetic Output

1. Start the Trino MCP server with allowlisted catalogs and schemas:

```bash
TRINO_ALLOWED_CATALOGS=hive,iceberg \
TRINO_ALLOWED_SCHEMAS=dev,test,staging \
TRINO_QUERY_MAX_EXECUTION_TIME=30s \
TRINO_QUERY_MAX_RUN_TIME=45s \
TRINO_QUERY_MAX_SCAN_PHYSICAL_BYTES=1GB \
  python3 -m test_data_agent.mcp_trino_server
```

2. Use metadata and profiling tools such as `describe_table`,
   `profile_table_safe`, `profile_column`, and rule-profiling tools.
3. Pass the `profile_table_safe` response to the generator MCP server's
   `plan_trino_dataset` tool with a new workspace, count, seed, and output
   format.
4. Review `dataset_spec.yaml` in that workspace.
5. Call `approve_dataset_plan` to generate and validate fresh synthetic data.

The Trino server must remain read-only and bounded. Unsafe SQL, DDL, DML,
unrestricted `SELECT *`, joins, CTEs, subqueries, and likely PII aliases are
rejected before execution.
Both allowlists are mandatory unless `TRINO_ALLOW_UNRESTRICTED=true` is set
explicitly. HTTPS is the default; plain HTTP additionally requires
`TRINO_ALLOW_INSECURE_HTTP=true` and is intended only for isolated local use.
The `TRINO_QUERY_MAX_*` values are sent as Trino session properties so a query
is terminated by the server when it exceeds its time or scan budget.
The generic `run_safe_select` tool is excluded from the default MCP surface.
Set `TRINO_ENABLE_SAFE_SELECT=true` only for a trusted client that needs it;
the planning workflow does not use raw SQL.

## Guardrails For AI Clients

- Never request production rows for export.
- Never ask MCP tools to return raw PII or generated datasets inline.
- Always use explicit seeds.
- Always review the `DatasetSpec` before generation for new data domains.
- Always review structured business rules; do not place production values,
  identifiers, PII, credentials, or tokens in rule literals.
- Always inspect `generation_manifest.json` and `validation_report.json` before
  reporting success.
