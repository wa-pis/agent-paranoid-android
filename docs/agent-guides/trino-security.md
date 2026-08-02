# Trino and MCP safety guide

Read this guide for Trino clients, MCP tools, SQL policy, masking, profiling
budgets, or transport changes.

## Tool surface

Default profiling and generator tools may return schema metadata, aggregates,
distributions, counts, validation status, manifest context, and masked values.
They must not return source rows.

`run_safe_select` or another explicit row-returning capability is a separate
opt-in surface. Keep it bounded, allowlisted, and masked according to its
contract. Do not describe the whole MCP server as source-free while such a
capability exists, and never use its results as generated output.

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
- Parse and reject unsafe SQL; do not rely on CLI or MCP schema validation as
  the only enforcement layer.
- Apply statement, column, row, scan, result, transport-response, and
  invocation-time budgets where the operation can exceed bounded work.
- Fail closed on budget exhaustion, malformed provider/database responses, or
  uncertain masking decisions.
- Keep source/database byte budgets separate from the final serialized
  transport response budget.
- Do not log SQL parameters, source values, credentials, prompts, or secrets.

Keep the Trino dependency optional for workflows that do not use Trino. Mock
Trino responses in normal unit tests; use live access only in explicitly gated
integration checks.
