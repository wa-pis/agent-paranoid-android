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
| `TEST_DATA_AGENT_MAX_INPUT_CELL_CHARS` | `1000000` | Maximum characters in one CSV cell |
| `TEST_DATA_AGENT_MAX_PARQUET_EXPANDED_BYTES` | `536870912` | Maximum estimated expanded Parquet bytes |
| `TEST_DATA_AGENT_MAX_YAML_ALIASES` | `50` | Maximum YAML aliases |
| `TEST_DATA_AGENT_MAX_YAML_DEPTH` | `100` | Maximum YAML nesting depth |
| `TEST_DATA_AGENT_MAX_BUSINESS_RULES_BYTES` | `1048576` | Maximum rule payload bytes |
| `TEST_DATA_AGENT_MAX_BUSINESS_RULE_EVALUATIONS` | `5000000` | Estimated row/rule work limit |
| `TEST_DATA_AGENT_MAX_OUTPUT_BYTES` | `536870912` | Maximum complete generated bundle size |
| `TEST_DATA_AGENT_MIN_FREE_DISK_BYTES` | `134217728` | Disk space kept in reserve |
| `TEST_DATA_AGENT_MAX_GENERATION_SECONDS` | `300` | Generation wall-clock limit |

Values must be positive integers, except
`TEST_DATA_AGENT_MAX_GENERATION_SECONDS`, which accepts a positive number.
Invalid environment values fail closed.

## Generator MCP

| Variable | Required | Purpose |
| --- | --- | --- |
| `TEST_DATA_AGENT_WORKSPACE_ROOT` | Recommended | Bounds every MCP input and output path |

When unset, the generator server uses the current working directory. For shared
or production-like use, always set a dedicated narrow workspace.

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

## Explicit Safety Overrides

| Variable | Default | Effect |
| --- | --- | --- |
| `TRINO_ALLOW_UNRESTRICTED` | `false` | Allows missing catalog/schema allowlists |
| `TRINO_ALLOW_INSECURE_HTTP` | `false` | Allows plain HTTP |

These accept `1`, `true`, `yes`, or `on` and their false equivalents.

Do not enable either override for production or production-adjacent Trino.
Plain HTTP is intended only for an isolated local integration environment.
