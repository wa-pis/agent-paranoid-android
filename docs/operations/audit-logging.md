# MCP Audit Logging

Shared MCP deployments can enable an append-only, HMAC-SHA256 authenticated
JSONL audit log. Logging is disabled unless both the path and key are set.

Each tool invocation writes a `started` record before the operation and a
`succeeded` or `failed` record afterward. Records include service, operation,
time, invocation ID, status, sequence, and the previous record MAC. Tool
arguments, SQL text, profile payloads, generated rows, return values, and error
messages are never recorded.

## Configure

Create a private directory and a base64-encoded key containing at least 32
random bytes:

```bash
install -d -m 700 /var/lib/test-data-agent/audit
export TEST_DATA_AGENT_AUDIT_LOG=/var/lib/test-data-agent/audit/mcp.jsonl
export TEST_DATA_AGENT_AUDIT_HMAC_KEY="$(
  python3 -c 'import base64, secrets; print(base64.b64encode(secrets.token_bytes(32)).decode())'
)"
export TEST_DATA_AGENT_AUDIT_ACTOR=shared-worker-1
```

Provide the key through the deployment secret manager. Do not commit it, put it
in MCP client configuration, or print it in CI logs. The log parent directory
must already exist. Symbolic links, hard-linked files, and group- or
world-writable log files are rejected.

When audit configuration is present but invalid, MCP operations fail closed.
The default maximum log size is 64 MiB. Override it with
`TEST_DATA_AGENT_AUDIT_MAX_BYTES`, up to 1 GiB.

## Verify

With the same key present in the environment:

```bash
test-data-agent audit-verify /var/lib/test-data-agent/audit/mcp.jsonl
```

Verification checks every sequence number, previous-record link, and HMAC. A
changed, inserted, reordered, or removed interior record fails verification.

HMAC authentication protects against modification by parties that do not hold
the key. It does not protect against a process or administrator that can read
the key, and a local chain alone cannot prove that valid records were removed
from the end. Periodically copy the log and reported final MAC to immutable
external storage when stronger retention guarantees are required.

## Rotate

1. Stop MCP workers that write to the file.
2. Run `audit-verify`.
3. Store the verified file and final MAC in the retention system.
4. Move the old file and restart the workers with a new empty path.

The size limit intentionally fails closed instead of silently dropping audit
events.
