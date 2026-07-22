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
5. Call `generate_dataset` with an explicit seed and output folder.
6. Call `validate_dataset` for the generated bundle.

Expected final report:

```text
rows: customers=25, orders=25
seed: 12345
validation: passed
synthetic: true
source rows copied: false
```

## Trino Profile To Synthetic Output

1. Start the Trino MCP server with allowlisted catalogs and schemas:

```bash
TRINO_ALLOWED_CATALOGS=hive,iceberg \
TRINO_ALLOWED_SCHEMAS=dev,test,staging \
  python3 -m test_data_agent.mcp_trino_server
```

2. Use metadata and profiling tools such as `describe_table`,
   `profile_table_safe`, `profile_column`, and rule-profiling tools.
3. Pass the safe profile payload to the generator MCP server's
   `infer_dataset_spec` tool.
4. Generate or export fresh synthetic data from the resulting `DatasetSpec`.

The Trino server must remain read-only and bounded. Unsafe SQL, DDL, DML,
unrestricted `SELECT *`, joins, CTEs, subqueries, and likely PII aliases are
rejected before execution.
Both allowlists are mandatory unless `TRINO_ALLOW_UNRESTRICTED=true` is set
explicitly. HTTPS is the default; plain HTTP additionally requires
`TRINO_ALLOW_INSECURE_HTTP=true` and is intended only for isolated local use.

## Guardrails For AI Clients

- Never request production rows for export.
- Never ask MCP tools to return raw PII or generated datasets inline.
- Always use explicit seeds.
- Always review the `DatasetSpec` before generation for new data domains.
- Always inspect `generation_manifest.json` and `validation_report.json` before
  reporting success.
