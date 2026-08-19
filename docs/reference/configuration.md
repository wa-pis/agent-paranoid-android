# Configuration

Defaults are conservative. Raise limits only after reviewing expected data
volume, available resources, and the trust level of the input.

All byte values are integer bytes unless stated otherwise.

CLI flags override the corresponding command defaults. Environment variables
configure resource, database, provider, and transport boundaries only where
listed below; they do not silently activate an optional provider or overwrite
an explicit CLI value. Use `COMMAND --help` to inspect CLI defaults and
`doctor --json` for installed/local capability states. `doctor` deliberately
does not read provider credentials or test remote reachability.

## Input And Generation Limits

| Variable | Default | Purpose |
| --- | ---: | --- |
| `TEST_DATA_AGENT_MAX_GENERATION_COUNT` | `100000` | Maximum rows per entity |
| `TEST_DATA_AGENT_MAX_INPUT_FILE_BYTES` | `134217728` | Maximum bytes per input file |
| `TEST_DATA_AGENT_MAX_TOTAL_INPUT_BYTES` | `536870912` | Maximum total input bytes |
| `TEST_DATA_AGENT_MAX_INPUT_ROWS` | `1000000` | Maximum input rows |
| `TEST_DATA_AGENT_MAX_INPUT_COLUMNS` | `1000` | Maximum columns |
| `TEST_DATA_AGENT_MAX_INPUT_CELLS` | `10000000` | Maximum row/column cells |
| `TEST_DATA_AGENT_MAX_INPUT_FILES` | `100` | Maximum files in a source folder |
| `TEST_DATA_AGENT_MAX_INPUT_CELL_CHARS` | `1000000` | Maximum characters in one CSV cell or JSON string value |
| `TEST_DATA_AGENT_MAX_PARQUET_EXPANDED_BYTES` | `536870912` | Maximum estimated expanded Parquet bytes |
| `TEST_DATA_AGENT_MAX_YAML_ALIASES` | `50` | Maximum YAML aliases |
| `TEST_DATA_AGENT_MAX_YAML_DEPTH` | `100` | Maximum YAML nesting depth |
| `TEST_DATA_AGENT_MAX_JSON_DEPTH` | `100` | Maximum structural depth for JSON datasets, profile/spec imports, and profile caches before parsing |
| `TEST_DATA_AGENT_MAX_BUSINESS_RULES_BYTES` | `1048576` | Maximum rule payload bytes |
| `TEST_DATA_AGENT_MAX_BUSINESS_RULE_EVALUATIONS` | `5000000` | Estimated row/rule work limit |
| `TEST_DATA_AGENT_MAX_OUTPUT_BYTES` | `536870912` | Maximum complete generated bundle size |
| `TEST_DATA_AGENT_MIN_FREE_DISK_BYTES` | `134217728` | Disk space kept in reserve |
| `TEST_DATA_AGENT_MAX_GENERATION_SECONDS` | `300` | Generation wall-clock limit |
| `TEST_DATA_AGENT_MAX_LOCAL_PROFILE_SECONDS` | `120` | Wall-clock limit for one local CSV-folder profile |
| `TEST_DATA_AGENT_MAX_LOCAL_PROFILE_SAMPLE_ROWS` | `1000000` | Cumulative relationship/rule sample-row ceiling per folder profile |

Values must be positive integers, except the two `*_SECONDS` values, which
accept positive finite numbers. Invalid environment values fail closed.

## Local CSV-Folder Profile Limits

Each fresh local folder profile receives one typed monotonic budget. Its
defaults are 120 seconds, at most 1,000,000 retained sample rows, 536,870,912
input bytes, and 10,000,000 streamed cells. The byte and cell caps reuse
`TEST_DATA_AGENT_MAX_TOTAL_INPUT_BYTES` and
`TEST_DATA_AGENT_MAX_INPUT_CELLS`; the normal CLI sample is smaller at 50,000
rows via `--rule-sample-rows`.

The Python API can pass narrower `LocalProfileLimits` through a fresh
`LocalProfileBudget`. Deadline, sample, byte, or cell exhaustion raises a
structured `LocalProfileLimitError`. A failed profile is not written to the
metadata-only cache.

## PostgreSQL Profiling

`profile-postgres` requires `POSTGRES_ALLOWED_SCHEMAS`,
`POSTGRES_ALLOWED_TABLES`, and `POSTGRES_ALLOWED_COLUMNS`. Connection settings
use `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DATABASE`, `POSTGRES_USER`, and
`POSTGRES_SSLMODE`. As an alternative to the host, port, database, and TLS
components, `POSTGRES_JDBC_URL` accepts the credential-free
`jdbc:postgresql://host:port/database?sslmode=verify-full` shape. This is URL
syntax parsed into the existing Psycopg configuration, not a Java/JDBC runtime.
Set `POSTGRES_PASSWORD_ENV` to the name of the environment variable containing
the password; never put a user or password in the URL.

Each `POSTGRES_ALLOWED_COLUMNS` item is either an exact
`schema.table.column` or a table-qualified `schema.table.*`. Wildcards are
expanded from bounded metadata into explicit columns before aggregate queries;
they never become SQL projection stars or local-value permissions.

The `POSTGRES_MAX_TABLES`, `POSTGRES_MAX_COLUMNS`, `POSTGRES_MAX_STATEMENTS`,
`POSTGRES_MAX_RESULT_ROWS`, `POSTGRES_MAX_RESULT_CELLS`, and
`POSTGRES_MAX_SECONDS` limits bound one profile. Statement and lock timeouts use
`POSTGRES_STATEMENT_TIMEOUT_MS` and `POSTGRES_LOCK_TIMEOUT_MS`. See the
[PostgreSQL workflow](../how-to/postgresql.md) for a complete example.

| Variable | Default | Purpose |
| --- | --- | --- |
| `POSTGRES_SOURCE_ID` | `postgres` | Stable non-secret source identity used in qualified entity names |
| `POSTGRES_JDBC_URL` | unset | Credential-free JDBC-style endpoint; conflicts with unequal explicit host, port, database, or TLS components |
| `POSTGRES_HOST` | `localhost` | PostgreSQL host; never serialized into profile identity |
| `POSTGRES_PORT` | `5432` | PostgreSQL port |
| `POSTGRES_DATABASE` | `postgres` | Database name |
| `POSTGRES_USER` | `test_data_agent` | Existing read-only database role |
| `POSTGRES_PASSWORD_ENV` | unset | Name of the environment variable containing the password |
| `POSTGRES_SSLMODE` | `require` | `require`, `verify-ca`, `verify-full`, or explicitly approved local `disable` |
| `POSTGRES_ALLOW_INSECURE` | `false` | Required with `POSTGRES_SSLMODE=disable`; local isolated testing only |
| `POSTGRES_ALLOWED_SCHEMAS` | required | Comma-separated schema allowlist |
| `POSTGRES_ALLOWED_TABLES` | required | Comma-separated `schema.table` allowlist |
| `POSTGRES_ALLOWED_COLUMNS` | required | Comma-separated exact `schema.table.column` or table-qualified `schema.table.*` profiling selectors |
| `POSTGRES_STATEMENT_TIMEOUT_MS` | `30000` | Per-statement timeout requested on the read-only session |
| `POSTGRES_LOCK_TIMEOUT_MS` | `5000` | Lock wait timeout requested on the read-only session |
| `POSTGRES_MAX_TABLES` | `100` | Maximum profiled tables |
| `POSTGRES_MAX_COLUMNS` | `1000` | Maximum profiled columns |
| `POSTGRES_MAX_STATEMENTS` | `1500` | Cumulative statement limit |
| `POSTGRES_MAX_RESULT_ROWS` | `10000` | Cumulative aggregate/metadata result rows |
| `POSTGRES_MAX_RESULT_CELLS` | `100000` | Cumulative aggregate/metadata result cells |
| `POSTGRES_MAX_SECONDS` | `120` | Shared monotonic profile deadline |

The database role must independently lack write privileges. The client also
requests `default_transaction_read_only=on`, but that setting is defense in
depth rather than a replacement for role permissions. No arbitrary SQL or
source-row profiling option exists.

## SQL Query Source Limits

`profile-query` uses the selected adapter's existing connection, physical
table/column allowlists, statement/result/time/scan budgets, and read-only
enforcement. Trino query sources require `TRINO_ALLOWED_TABLE_COLUMNS`; an
unrestricted Trino configuration is rejected for this command.

| Variable | Default | Purpose |
| --- | ---: | --- |
| `SQL_QUERY_MAX_BYTES` | `65536` | Maximum UTF-8 bytes in the local query file |
| `SQL_QUERY_MAX_AST_NODES` | `500` | Maximum parsed SQL nodes |
| `SQL_QUERY_MAX_AST_DEPTH` | `32` | Maximum parsed SQL nesting depth |
| `SQL_QUERY_MAX_PROJECTED_COLUMNS` | `100` | Maximum explicit fields after wildcard expansion |

Values must be positive integers and remain below the built-in absolute caps.
The file is read once with descriptor metadata revalidation. SQL text and
literals are not accepted through environment variables or CLI options and are
not written to profiles, manifests, errors, providers, or MCP responses.

## GigaChat Advisor

GigaChat is explicit and off unless `agent-advise --provider gigachat` is
selected. Configure exactly one runtime authentication value:

| Variable | Default | Purpose |
| --- | --- | --- |
| `GIGACHAT_CREDENTIALS` | unset | Authorization key used by the official SDK to obtain an access token |
| `GIGACHAT_ACCESS_TOKEN` | unset | Pre-obtained short-lived access token; mutually exclusive with `GIGACHAT_CREDENTIALS` |
| `GIGACHAT_SCOPE` | `GIGACHAT_API_PERS` | `GIGACHAT_API_PERS`, `GIGACHAT_API_B2B`, or `GIGACHAT_API_CORP` |
| `GIGACHAT_CA_BUNDLE_FILE` | system trust store | Absolute or relative path to a reviewed readable CA bundle |

Credentials are never accepted as CLI arguments or written to settings,
workspaces, logs, or errors. The API and authorization endpoints are fixed to
the official HTTPS services. TLS verification cannot be disabled; endpoint,
client-certificate, SSL-context, or token-expiry overrides fail locally.

The CLI exposes only the optional `--model` override. Applications that use
the Python adapter can provide frozen `GigaChatAdvisorSettings` to narrow the
default 4 MiB request, 1 MiB response, 4,096 output-token, 15-second timeout,
and zero-retry budgets. See [Use The GigaChat Advisor](../how-to/gigachat.md).

## Generator MCP

| Variable | Required | Purpose |
| --- | --- | --- |
| `TEST_DATA_AGENT_WORKSPACE_ROOT` | Recommended | Bounds every MCP input and output path |
| `TEST_DATA_AGENT_MAX_PROFILE_PAYLOAD_BYTES` | Optional | Maximum inline safe profile size; defaults to 4 MiB |
| `TEST_DATA_AGENT_AUDIT_LOG` | Optional | Enables a shared HMAC-authenticated JSONL audit log |
| `TEST_DATA_AGENT_AUDIT_HMAC_KEY` | Required with audit log | Base64 key containing at least 32 random bytes |
| `TEST_DATA_AGENT_AUDIT_HMAC_KEY_FILE` | Alternative to key value | Path to a bounded base64 secret file |
| `TEST_DATA_AGENT_AUDIT_ACTOR` | Optional | Stable non-sensitive worker or deployment label |
| `TEST_DATA_AGENT_AUDIT_MAX_BYTES` | Optional | Audit log size limit; defaults to 64 MiB |

When unset, the generator server uses the current working directory. For shared
or production-like use, always set a dedicated narrow workspace.

Configure exactly one of `TEST_DATA_AGENT_AUDIT_HMAC_KEY` and
`TEST_DATA_AGENT_AUDIT_HMAC_KEY_FILE`. Secret files must be regular,
non-linked, at most 4096 bytes, and not group- or world-writable.

## Trino MCP

The default aggregate-only tools are source-literal-free. The explicit opt-in
row-returning tools are configured separately:

| Variable | Default | Purpose |
| --- | --- | --- |
| `TRINO_ENABLE_SAFE_SELECT` | `false` | Enables `run_safe_select`; every returned string is recursively masked in bounded composite values, but other non-string source values may remain outside the source-literal-free guarantee |

## Trino Connection

Use `TRINO_JDBC_URL` as an alternative to separate host and port settings. Its
supported form is `jdbc:trino://host:port/catalog/schema?SSL=true`. Catalog and
schema are optional request defaults and are accepted only when each is in the
mandatory allowlist. Authentication remains in `TRINO_USER` and existing
runtime secret mechanisms; URL credentials, tokens, roles, session properties,
headers, proxies, unknown properties, and `SSL=false` are rejected. The URL is
parsed into the existing Python Trino client and does not load Java or a JDBC
driver.

| Variable | Default | Purpose |
| --- | --- | --- |
| `TRINO_JDBC_URL` | unset | Credential-free JDBC-style endpoint; conflicts with unequal explicit endpoint/default components |
| `TRINO_HOST` | `localhost` | Trino host name |
| `TRINO_PORT` | `8080` | Trino port |
| `TRINO_USER` | `test_data_agent` | Trino user |
| `TRINO_HTTP_SCHEME` | `https` | `https` or explicitly allowed `http` |
| `TRINO_CATALOG` | unset | Optional request default; must be in `TRINO_ALLOWED_CATALOGS` |
| `TRINO_SCHEMA` | unset | Optional request default; requires `TRINO_CATALOG` and membership in `TRINO_ALLOWED_SCHEMAS` |
| `TRINO_ALLOWED_CATALOGS` | required | Comma-separated catalog allowlist |
| `TRINO_ALLOWED_SCHEMAS` | required | Comma-separated schema allowlist |
| `TRINO_ALLOWED_TABLE_COLUMNS` | unset | Optional exact `catalog.schema.table.column` or restricted table-qualified `catalog.schema.table.*` profile selectors; wildcard does not authorize category literals |
| `TRINO_REQUEST_TIMEOUT_SECONDS` | `30` | Client request timeout, `0.1` to `300` |
| `TRINO_MAX_RESULT_ROWS` | `10000` | Client result cap, maximum `100000` |
| `TRINO_QUERY_MAX_EXECUTION_TIME` | `30s` | Trino execution-time session budget |
| `TRINO_QUERY_MAX_RUN_TIME` | `45s` | Trino total run-time session budget |
| `TRINO_QUERY_MAX_SCAN_PHYSICAL_BYTES` | `1GB` | Trino physical scan budget |
| `TRINO_DEPLOYMENT_PROFILE` | `trusted-local` | `trusted-local` permits an unset cumulative scan ceiling; `shared-hardened` requires a finite `TRINO_MAX_INVOCATION_ESTIMATED_SCAN_BYTES` |

Duration values use `ms`, `s`, `m`, or `h`. Data-size values use `B`, `kB`,
`MB`, or `GB`.

`TRINO_QUERY_MAX_RUN_TIME` must be greater than or equal to
`TRINO_QUERY_MAX_EXECUTION_TIME`.

When `TRINO_ALLOWED_TABLE_COLUMNS` is set, table profiling uses only its exact
selectors plus metadata-expanded columns from a matching table wildcard. The
request fails before aggregate work when metadata is empty, malformed,
duplicated, inconsistent, or over the invocation column budget.

## Trino Invocation Limits

These limits apply to one MCP tool invocation, including nested table and
column profiling. Every invocation receives a fresh monotonic budget.

| Variable | Default | Unit | Scope | Failure behavior |
| --- | ---: | --- | --- | --- |
| `TRINO_MAX_INVOCATION_PROFILED_COLUMNS` | `100` | columns | Per invocation | Rejects before profiling the next column |
| `TRINO_MAX_INVOCATION_STATEMENTS` | `150` | statements | Per invocation | Rejects before opening the next Trino connection |
| `TRINO_MAX_INVOCATION_SECONDS` | `120` | seconds | Per invocation | Clamps HTTP and Trino query timeouts; closes active query resources on expiry |
| `TRINO_MAX_INVOCATION_ESTIMATED_SCAN_BYTES` | unset | bytes | Per invocation; required for `shared-hardened` | Rejects before a statement whose conservative estimate would exceed the limit |

All configured values must be finite and positive. Column, statement, and scan
limits accept integers; invocation seconds accepts a number. Invalid values
fail server startup. The `shared-hardened` profile fails closed when the
cumulative scan ceiling is unset. Budget exhaustion raises a bounded query-work error and
does not restore work already consumed by nested helpers.

The typed budget also keeps `database_result_bytes` and
`transport_response_bytes` separate; each defaults to `4 MiB` in the Trino MCP
work limits. The transport limit is measured in UTF-8 bytes after final MCP
JSON serialization and framing, at the production writer boundary. Its
minimum is `350` bytes: that fixed amount is reserved for the bounded terminal
error response, so normal responses can use at most the configured total minus
the reserve. A related notification and its final response share the same
per-invocation budget.

`TRINO_QUERY_MAX_EXECUTION_TIME`, `TRINO_QUERY_MAX_RUN_TIME`, and
`TRINO_QUERY_MAX_SCAN_PHYSICAL_BYTES` remain per-query limits. The invocation
deadline clamps the two per-query time limits and `TRINO_REQUEST_TIMEOUT_SECONDS`
to the remaining invocation time. When the optional cumulative scan limit is
set, each statement conservatively consumes the configured per-query
`TRINO_QUERY_MAX_SCAN_PHYSICAL_BYTES` cap. Leaving the cumulative cap unset is
allowed only for the explicitly named `trusted-local` profile; the
`shared-hardened` profile requires a finite cap before startup.

## Explicit Safety Overrides

| Variable | Default | Effect |
| --- | --- | --- |
| `TRINO_ALLOW_UNRESTRICTED` | `false` | Allows missing catalog/schema allowlists |
| `TRINO_ALLOW_INSECURE_HTTP` | `false` | Allows plain HTTP |

These accept `1`, `true`, `yes`, or `on` and their false equivalents.

Do not enable either override for production or production-adjacent Trino.
Plain HTTP is intended only for an isolated local integration environment.
