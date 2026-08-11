# Profile Through Trino

Install the optional Trino client and, when using MCP, the MCP SDK:

```bash
pip install "agent-paranoid-android[trino]"
pip install "agent-paranoid-android[mcp,trino]"
```

Configure an explicit read-only scope:

```bash
export TRINO_HOST=trino.example.internal
export TRINO_PORT=8443
export TRINO_USER=test_data_agent
export TRINO_HTTP_SCHEME=https
export TRINO_ALLOWED_CATALOGS=warehouse
export TRINO_ALLOWED_SCHEMAS=analytics
export TRINO_DEPLOYMENT_PROFILE=shared-hardened
export TRINO_MAX_INVOCATION_ESTIMATED_SCAN_BYTES=1073741824
```

The default aggregate-only MCP tools list allowlisted metadata, describe
tables, and compute bounded aggregate profiles. They do not return source rows
or raw category literals. Table and column profiling share cumulative
statement, column, deadline, response, and optional scan budgets.

Start the Trino MCP server only after `doctor` reports valid configuration:

```bash
test-data-agent doctor --require-extra trino
test-data-agent-mcp-trino
```

The explicit opt-in `run_safe_select` surface is disabled by default. Enabling
it is a separate row-privacy contract: every string is recursively masked, but
allowed non-string source values may remain, so its output is not source-free,
anonymous, or a generated dataset.

Use the checked-in disposable example for a complete profile-to-generation
workflow over Trino's synthetic TPC-H `tiny` catalog:

```bash
examples/local_trino/run.sh /tmp/agent-paranoid-trino-example
```

The example removes its container on success or failure and leaves only the
safe profile, reviewed spec, generated rows, validation report, manifest, and a
bounded result summary. See [Configuration](../reference/configuration.md) and
[MCP Tools](../mcp_examples.md) for the full limits and tool contracts.
