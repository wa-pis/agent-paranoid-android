# Trino and MCP safety guide

Read this guide for Trino clients, MCP tools, SQL policy, masking, profiling
budgets, or transport changes.

## Tool surface

Default generator and default aggregate-only Trino tools may return schema
metadata, aggregates, distributions, counts, validation status, manifest
context, and masked values. They must not return source rows.

Explicit opt-in row-returning tools, including `run_safe_select`, are a separate
surface. Keep them bounded, allowlisted, and masked according to their
contracts. Mask strings recursively inside bounded composite values and reject
excessive depth or value counts. Do not describe the whole MCP server as
source-free while such a capability exists, and never use its results as
generated output.

Allowed operations are limited to:

- listing catalogs, schemas, and tables;
- describing tables;
- profiling tables and columns;
- safe, read-only, allowlisted `SELECT` queries with explicit limits; and
- masked samples only when the tool contract explicitly requires them.

Never permit `INSERT`, `UPDATE`, `DELETE`, `MERGE`, `DROP`, `TRUNCATE`,
`ALTER`, `CREATE`, `GRANT`, `REVOKE`, unrestricted `SELECT *`, raw-row export,
or access to secrets, credentials, tokens, or raw PII.

## Enforcement

- Validate identifiers and enforce table/column allowlists before execution.
- Return raw categorical aggregates only for explicitly non-sensitive columns
  covered by both table and column allowlists; a table allowlist alone does not
  authorize category disclosure.
- Parse and reject unsafe SQL; do not rely on CLI or MCP schema validation as
  the only enforcement layer.
- Apply statement, column, row, scan, result, transport-response, and
  invocation-time budgets where the operation can exceed bounded work.
- Fail closed on budget exhaustion, malformed provider/database responses, or
  uncertain masking decisions.
- Keep source/database byte budgets separate from the final serialized
  transport response budget.
- Reserve the fixed bounded transport-error allowance before charging normal
  responses; the writer must clean the request registry even when writing,
  flushing, fallback serialization, or cancellation fails.
- Accept only string or integer JSON-RPC request IDs and key active requests by
  their exact serialized representation so distinct wire types cannot alias.
- Do not log SQL parameters, source values, credentials, prompts, or secrets.
- Replace FastMCP/Pydantic argument-validation failures with a fixed detached
  error before returning a tool result; never reflect rejected values.
- Reject malformed typed MCP requests and notifications before SDK dispatch;
  never pass their caller-controlled values into SDK logs or exceptions.
- Audit-log capacity must reject a new invocation before its `started` record
  unless one maximum-size terminal record is reserved; an admitted terminal
  event must not be dropped at the configured admission threshold.

Keep the Trino dependency optional for workflows that do not use Trino. Mock
Trino responses in normal unit tests; use live access only in explicitly gated
integration checks.
