# Design: post-mvp-hardening

## Packaging Boundary

Faker, Pydantic, and PyYAML remain core. PyArrow, MCP, SQLGlot, and Trino move
to extras. Imports at optional boundaries fail with installation guidance, and
CI continues exercising the complete dependency set.

## Compatibility Boundary

All serialized DatasetSpec adapters use one version check before Pydantic
validation. Supported and deprecated versions are explicit registries.
Unknown versions fail closed rather than relying on ignored fields.

## Audit Boundary

MCP registration wraps tools with metadata-only audit events. Each invocation
writes `started` before execution and `succeeded` or `failed` afterward. Records
chain the previous HMAC-SHA256 value. Arguments, SQL, payloads, results, rows,
and exception messages are excluded. POSIX no-follow open, file locking,
regular-file checks, link checks, permissions, record size, and total size
limits protect the sink.

HMAC detects changes by principals without the key. External retention of the
verified final MAC is required to detect valid tail truncation or a malicious
administrator that also holds the key.

## Trino Planning Boundary

`profile_table_safe` remains in the credential-bearing Trino server and
enforces catalog/schema allowlists. The generator server receives only its
bounded profile payload, writes review artifacts, and stops.
`approve_dataset_plan` is a separate tool call. `run_safe_select` is absent
from the default Trino MCP surface and requires explicit operator opt-in.
