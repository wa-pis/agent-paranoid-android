# Design: agent-json-contract

Successful agent commands serialize the existing typed `AgentResult` or
`AgentWorkspaceStatus` models with `schema_version: "1.0"`.

Known failures serialize `CliErrorResponse`, containing a stable error code,
concise message, command, exit code, retryability, and optional help command.
JSON goes to stdout and leaves stderr empty so callers can parse one stream.

Human output remains the default. Parser errors become structured only when
the invocation contains `--json`.
