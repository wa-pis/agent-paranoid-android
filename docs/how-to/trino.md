# Profile Through Trino

English · [Русский](../ru/how-to/trino.md)

Database profiling is available in stable `1.6.0` and requires explicit
read-only configuration, allowlists and resource budgets.

Install the optional Trino client and, when using MCP, the MCP SDK:

```bash
pip install "agent-paranoid-android[trino]"
pip install "agent-paranoid-android[mcp,trino]"
```

Stable `1.6.0` supports Basic, JWT, Kerberos, GSSAPI, OAuth2 and client
certificates are documented in the
[configuration reference](../reference/configuration.md#trino-connection). Follow its
runtime secret-indirection, HTTPS verification and local OAuth opt-in rules.
Local contract tests do not establish remote authentication compatibility.

Configure an explicit read-only scope:

```bash
export TRINO_HOST=trino.example.internal
export TRINO_PORT=8443
export TRINO_USER=test_data_agent
export TRINO_HTTP_SCHEME=https
export TRINO_ALLOWED_CATALOGS=warehouse
export TRINO_ALLOWED_SCHEMAS=analytics
export TRINO_ALLOWED_TABLE_COLUMNS='warehouse.analytics.orders.*'
export TRINO_DEPLOYMENT_PROFILE=shared-hardened
export TRINO_MAX_INVOCATION_ESTIMATED_SCAN_BYTES=1073741824
```

`TRINO_ALLOWED_TABLE_COLUMNS` is optional for compatibility. When set, an
entry is either one exact `catalog.schema.table.column` or the exact
`catalog.schema.table.*` form. Wildcards require restricted mode and catalog
and schema membership in the mandatory allowlists. Bounded
`information_schema` metadata is validated and sorted before the first table
aggregate; the complete column budget is charged in preflight. Executed
profiling SQL still quotes explicit columns and never projects `*`.

The same endpoint and optional request defaults can come from a credential-free
JDBC-style URL:

```bash
export TRINO_JDBC_URL='jdbc:trino://trino.example.internal:8443/warehouse/analytics?SSL=true'
export TRINO_USER=test_data_agent
export TRINO_ALLOWED_CATALOGS=warehouse
export TRINO_ALLOWED_SCHEMAS=analytics
```

The catalog and schema path must match the allowlists. Credentials, tokens,
roles, session properties, proxies, headers, unknown properties, and
`SSL=false` fail before client construction. This is parsed into the Python
Trino client; it does not install or invoke Java or a JDBC driver. Explicit
component settings may coexist only when their values agree.

The default aggregate-only MCP tools list allowlisted metadata, describe
tables, and compute bounded aggregate profiles. They do not return source rows
or raw category literals. Table and column profiling share cumulative
statement, column, deadline, response, and optional scan budgets.

A wildcard authorizes aggregate profiling scope only. It does not authorize
category literals, preserve-as-is, caller SQL stars, row-returning tools,
provider payloads, default MCP literals, logs, or errors. Exact table-column
entries retain their existing bounded category-summary policy.

Check that the Trino capability is installed, then start the MCP server:

```bash
test-data-agent doctor --require-extra trino
test-data-agent-mcp-trino
```

`doctor` checks the installed driver, safe-SQL support and configured deployment
budget profile using a local smoke check. It does not validate the selected
endpoint, authentication or catalog/schema allowlists, or contact Trino.
Server startup and tool calls enforce their respective configuration and access
checks; a successful local doctor check does not prove database access.

The explicit opt-in `run_safe_select` surface is disabled by default. Enabling
it is a separate row-privacy contract: every string is recursively masked, but
allowed non-string source values may remain, so its output is not source-free,
anonymous, or a generated dataset.

Use the checked-in disposable example for a complete profile-to-generation
workflow over Trino's synthetic TPC-H `tiny` catalog:

```bash
examples/local_trino/run.sh /tmp/agent-paranoid-trino-example
```

Use `examples/local_trino/run-jdbc.sh OUTPUT` to run the identical disposable
workflow with its endpoint and `tpch/tiny` defaults supplied in JDBC syntax.
Use `examples/local_trino/run-wildcard.sh OUTPUT` to exercise bounded
`tpch.tiny.nation.*` expansion and deterministic field ordering.
Use `examples/local_trino/run-query.sh OUTPUT` to profile one reviewed local
`SELECT` as a virtual entity. Query-source mode additionally requires exact
`TRINO_ALLOWED_TABLE_COLUMNS` entries or a table-qualified wildcard and rejects
unrestricted mode. It stores a fingerprint, not query text, literals, backend
messages, endpoints, or result rows.

The typed Python entry point uses the same environment configuration and
policy boundary:

```python
from pathlib import Path

import trino

from test_data_agent import (
    SqlQueryAdapter,
    SqlQueryProfileRequest,
    profile_trino_query_source,
)
from test_data_agent.trino_config import TrinoConfig

request = SqlQueryProfileRequest(
    adapter=SqlQueryAdapter.TRINO,
    source_id="warehouse",
    entity="nation_query",
    query_file=Path("query.sql"),
)
profile = profile_trino_query_source(
    request,
    config=TrinoConfig.from_env(),
    driver=trino,
)
```

The example removes its container on success or failure and leaves only the
safe profile, reviewed spec, generated rows, validation report, manifest, and a
bounded result summary. See [Configuration](../reference/configuration.md) and
[MCP Tools](../mcp_examples.md) for the full limits and tool contracts.

## MCP with a username and password

Select `TRINO_AUTH_METHOD=basic` explicitly for username/password login.
The default is `none`: setting `TRINO_USER` alone does not send a password.
`TRINO_AUTH_SECRET_ENV` holds the **name of the password environment variable**,
not the password. Basic requires verified HTTPS, including local deployments.

### 1. Prepare the environment and access

```bash
python3 -m venv /ABSOLUTE/PATH/trino-env
/ABSOLUTE/PATH/trino-env/bin/python -m pip install 'agent-paranoid-android[mcp,trino]'
/ABSOLUTE/PATH/trino-env/bin/test-data-agent --version
/ABSOLUTE/PATH/trino-env/bin/test-data-agent doctor --require-extra trino
```

Replace `/ABSOLUTE/PATH` with your absolute path. Doctor checks local installation,
not server login. Obtain the HTTPS host/port, login, approved catalog/schema/table/
column scope and read-only metadata/aggregate grants from your Trino administrator.
The MCP process needs network access, any required VPN and a trusted certificate
chain. A corporate CA must be trusted by the Python/runtime environment; keep
certificate verification enabled.

### 2. Supply the password to the process

If your MCP client supports protected secret injection into child-process
environment variables, configure `MY_TRINO_PASSWORD` there. Keep the password out
of JSON, repositories, command arguments and chat. A graphical application may
not inherit terminal variables, and a `.env` file is not loaded automatically.
Restart the MCP server after changing its environment.

A complete **macOS** option: use Keychain Access to create a password item named
`agent-paranoid-android-trino`, with its account matching `TRINO_USER` and your
password. Save this script as `/ABSOLUTE/PATH/start-trino-mcp.sh`, replacing the
path to the installed server:

```bash
#!/bin/bash
# Resolve the password locally; reserve stdout for the MCP protocol.
if ! MY_TRINO_PASSWORD=$(/usr/bin/security find-generic-password \
    -s agent-paranoid-android-trino -a "$TRINO_USER" -w 2>/dev/null); then
  printf '%s\n' 'Trino password is unavailable in Keychain' >&2
  exit 1
fi
export MY_TRINO_PASSWORD
exec /ABSOLUTE/PATH/trino-env/bin/test-data-agent-mcp-trino
```

Run `chmod 700 /ABSOLUTE/PATH/start-trino-mcp.sh`. Allow local access to that
item if macOS prompts. Do not enable `set -x` or print the password. This launcher
resolves the secret at startup without relying on a GUI application's inherited
environment. On other operating systems use the client's protected storage or a
local secret mechanism.

### 3. Register the server in your MCP client

This is the common `mcpServers` shape; the settings location depends on the client.
Replace all fictional endpoints, usernames and data names locally. This example
uses the Keychain launcher from the previous step:

```json
{
  "mcpServers": {
    "trino": {
      "command": "/ABSOLUTE/PATH/start-trino-mcp.sh",
      "env": {
        "TRINO_HOST": "trino.example.internal",
        "TRINO_PORT": "443",
        "TRINO_HTTP_SCHEME": "https",
        "TRINO_USER": "your_login",
        "TRINO_AUTH_METHOD": "basic",
        "TRINO_AUTH_SECRET_ENV": "MY_TRINO_PASSWORD",
        "TRINO_ALLOWED_CATALOGS": "warehouse",
        "TRINO_ALLOWED_SCHEMAS": "analytics",
        "TRINO_ALLOWED_TABLE_COLUMNS": "warehouse.analytics.orders.*",
        "TRINO_DEPLOYMENT_PROFILE": "shared-hardened",
        "TRINO_MAX_INVOCATION_ESTIMATED_SCAN_BYTES": "1073741824"
      }
    }
  }
}
```

When the client securely supplies `MY_TRINO_PASSWORD` instead of using Keychain,
set `command` directly to
`/ABSOLUTE/PATH/trino-env/bin/test-data-agent-mcp-trino`.
Secret substitution is client-specific: `${MY_TRINO_PASSWORD}` in JSON is not a
universal substitution mechanism.

`TRINO_HOST` is a host name without a URL scheme or path; use the actual HTTPS
port. Catalog/schema allowlists are mandatory comma-separated sets. Column scope
is optional for ordinary table profiling, but required for `profile-query`.
You may replace `warehouse.analytics.orders.*` with comma-separated exact columns.
The wildcard permits bounded aggregate profiling only, grants no source-row
access and does not replace Trino grants.

The cumulative scan limit shown is 1 GiB per invocation. Existing defaults also
bound request timeout to 30 seconds, execution time to 30 seconds, run time to
45 seconds and scanning to 1 GiB per query. `TRINO_CATALOG` and `TRINO_SCHEMA`
are optional defaults within the allowlists. See the
[configuration reference](../reference/configuration.md#trino-connection) for all settings.

### 4. Verify startup and diagnose failures

Restart the server in your MCP client and check that Trino tools appear. Start
with an allowed metadata tool such as `list_catalogs`, then `describe_table` for
an approved table. Process startup and Doctor success do not prove authentication.
These instructions are checked locally against configuration contracts, not
against your remote server.

For a 401, check `basic`, the variable referenced by `TRINO_AUTH_SECRET_ENV`,
the login and process restart locally. For a 403, check server grants and access
policy; a status alone does not establish the exact cause. For TLS failures,
check the endpoint and certificate trust.

For support share the package version, launch method, `TRINO_AUTH_METHOD`,
`TRINO_HTTP_SCHEME`, whether a login and secret reference are set, whether the
password variable reaches the process, and whether another client can log in.
Do not share login/password values, complete `.env` files, connection URLs,
source rows or raw driver responses.

## Authentication failures

For a failed connection, record the installed package version and selected
`TRINO_AUTH_METHOD` locally. Share only those details when investigating a failure;
do not share passwords, tokens, connection URLs or raw driver responses.
A reported HTTP 401 alone does not identify a configuration or compatibility issue.

SQL-query profiling converts untyped HTTP 401/403 and TLS failures into the fixed
`SQL query source profiling failed` error, without retaining the original
exception cause or context. The CLI keeps its `external_service` category and
leaves an existing output artifact unchanged. MCP returns its fixed Trino error
and records value-free audit diagnostics. These boundaries do not establish
successful authentication against a particular server.
