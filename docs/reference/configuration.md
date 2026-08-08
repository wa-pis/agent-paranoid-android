# Configuration

Defaults are conservative. Raise limits only after reviewing expected data
volume, available resources, and the trust level of the input.

All byte values are integer bytes unless stated otherwise.

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
| `TEST_DATA_AGENT_MAX_JSON_DEPTH` | `100` | Maximum nesting depth for JSON dataset values |
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
| `TRINO_ENABLE_SAFE_SELECT` | `false` | Enables `run_safe_select`; its bounded, masked rows may contain allowed source values and are outside the source-literal-free guarantee |

## Trino Connection

| Variable | Default | Purpose |
| --- | --- | --- |
| `TRINO_HOST` | `localhost` | Trino host name |
| `TRINO_PORT` | `8080` | Trino port |
| `TRINO_USER` | `test_data_agent` | Trino user |
| `TRINO_HTTP_SCHEME` | `https` | `https` or explicitly allowed `http` |
| `TRINO_ALLOWED_CATALOGS` | required | Comma-separated catalog allowlist |
| `TRINO_ALLOWED_SCHEMAS` | required | Comma-separated schema allowlist |
| `TRINO_REQUEST_TIMEOUT_SECONDS` | `30` | Client request timeout, `0.1` to `300` |
| `TRINO_MAX_RESULT_ROWS` | `10000` | Client result cap, maximum `100000` |
| `TRINO_QUERY_MAX_EXECUTION_TIME` | `30s` | Trino execution-time session budget |
| `TRINO_QUERY_MAX_RUN_TIME` | `45s` | Trino total run-time session budget |
| `TRINO_QUERY_MAX_SCAN_PHYSICAL_BYTES` | `1GB` | Trino physical scan budget |

Duration values use `ms`, `s`, `m`, or `h`. Data-size values use `B`, `kB`,
`MB`, or `GB`.

`TRINO_QUERY_MAX_RUN_TIME` must be greater than or equal to
`TRINO_QUERY_MAX_EXECUTION_TIME`.

## Trino Invocation Limits

These limits apply to one MCP tool invocation, including nested table and
column profiling. Every invocation receives a fresh monotonic budget.

| Variable | Default | Unit | Scope | Failure behavior |
| --- | ---: | --- | --- | --- |
| `TRINO_MAX_INVOCATION_PROFILED_COLUMNS` | `100` | columns | Per invocation | Rejects before profiling the next column |
| `TRINO_MAX_INVOCATION_STATEMENTS` | `150` | statements | Per invocation | Rejects before opening the next Trino connection |
| `TRINO_MAX_INVOCATION_SECONDS` | `120` | seconds | Per invocation | Clamps HTTP and Trino query timeouts; closes active query resources on expiry |
| `TRINO_MAX_INVOCATION_ESTIMATED_SCAN_BYTES` | unset | bytes | Per invocation, optional | Rejects before a statement whose conservative estimate would exceed the limit |

All configured values must be finite and positive. Column, statement, and scan
limits accept integers; invocation seconds accepts a number. Invalid values
fail server startup. Budget exhaustion raises a bounded query-work error and
does not restore work already consumed by nested helpers.

`TRINO_QUERY_MAX_EXECUTION_TIME`, `TRINO_QUERY_MAX_RUN_TIME`, and
`TRINO_QUERY_MAX_SCAN_PHYSICAL_BYTES` remain per-query limits. The invocation
deadline clamps the two per-query time limits and `TRINO_REQUEST_TIMEOUT_SECONDS`
to the remaining invocation time. When the optional cumulative scan limit is
set, each statement conservatively consumes the configured per-query
`TRINO_QUERY_MAX_SCAN_PHYSICAL_BYTES` cap; leaving it unset disables that
cumulative cap while retaining the per-query Trino limit.

## Explicit Safety Overrides

| Variable | Default | Effect |
| --- | --- | --- |
| `TRINO_ALLOW_UNRESTRICTED` | `false` | Allows missing catalog/schema allowlists |
| `TRINO_ALLOW_INSECURE_HTTP` | `false` | Allows plain HTTP |

These accept `1`, `true`, `yes`, or `on` and their false equivalents.

Do not enable either override for production or production-adjacent Trino.
Plain HTTP is intended only for an isolated local integration environment.
