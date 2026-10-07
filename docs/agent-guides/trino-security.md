# Trino and MCP safety guide

Read this guide for Trino clients, MCP tools, SQL policy, masking, profiling
budgets, or transport changes.

## Tool surface

Default generator and default aggregate-only Trino tools may return schema
metadata, aggregates, distributions, counts, validation status, manifest
context, and masked values. They must not return source rows.

Explicit opt-in row-returning tools, including `run_safe_select`, are a separate
surface. Keep them bounded, allowlisted, and masked according to their
contracts. Mask strings, binary representations and unsupported scalar types recursively
inside bounded composite values. Maps with nonnumeric keys are suppressed
entirely because their keys are source contents; numeric
map keys retain existing masking and budgets. Reject
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

JDBC-style endpoint strings are untrusted configuration, not executable JDBC.
Bound their bytes and parsed components before constructing a Python client;
keep credentials, allowlists, and budgets in their existing settings.
Table-qualified wildcard selectors are authorization shorthand only: expand
them through bounded metadata into a frozen explicit-column snapshot and never
emit a projection star.

`profile-query` is separate from normal table profiling and MCP caller SQL. It
accepts one bounded local regular file (special files reject without waiting
for a FIFO writer), validates one fully qualified single-table
`SELECT`, and executes only trusted no-row schema and aggregate wrappers.
Query text, literals, backend errors, endpoints, and rows must not cross into
profiles, generated data, logs, providers, or default MCP responses.
Unsupported JOIN and CTE/WITH shapes receive fixed recovery hints without table
names, query text or literals. This does not broaden the permitted SQL subset.
Boolean AND/OR predicates are permitted within that existing single-table
subset; they do not authorize additional functions, tables, query shapes or
larger work budgets.
Direct non-sensitive date/timestamp projections include validated min/max
aggregates in their existing column-summary query. Any sensitive source field
in the query, a sensitive output name, or a derived expression suppresses these
bounds; renaming a sensitive source cannot declassify it. Missing or malformed
nonempty bounds fail closed; all-null fields make no observed-period claim. No
query rows or extra aggregate round trips are added.

PostgreSQL connection failures expose only fixed categories when identifiable
from typed network/TLS exceptions or allowlisted SQLSTATE codes: timeout,
connection refused, name resolution, TLS, authentication/authorization, database
configuration or permissions. Unknown failures remain generic. Driver text is
never parsed for clues or returned; sanitized connection errors are detached
from the original exception context. Some drivers wrap network failures in a
generic exception, so a specific category is not guaranteed.

PostgreSQL local-category requests are checked against explicit column allowlists
before opening the profiling session or issuing queries. Wildcard configurations
first resolve bounded metadata into a fixed column snapshot; category validation
then runs before aggregate queries. Category queries bound character and encoded representation sizes inside
the same SQL statement before returning values. Oversized values produce a
NULL rejection sentinel; grouping and counts remain complete. PostgreSQL
also bounds the JSON representation to cover native CHAR padding.
Category count, value-content and disclosure
checks still apply, and these preflight checks do not grant preservation rights.

PostgreSQL table profiling includes date/timestamp minima and maxima in the same
column-summary aggregate for non-sensitive temporal columns. No extra query or
row sample is needed. Sensitive-name columns do not request or retain these
bounds. Nonempty temporal aggregates must have correctly typed, ordered endpoints
with compatible timezone metadata; malformed endpoints fail closed. All-null
columns have no observed bounds. Query-source profiling applies the same
temporal-bound guard to its derived output. Neither path certifies source-period
utility when bounds are missing.

Declared `numeric(p,s)` in PostgreSQL or allowed query metadata carries only
precision/scale into the profile; it does not authorize exact source extrema,
raw values, a wider SQL subset or a larger scan budget. Unbounded `numeric`
remains an explicitly approximate FLOAT inference, not exact DECIMAL evidence.
PostgreSQL no-row result descriptions retain valid driver-declared numeric
precision/scale as type metadata. Missing shape stays unbounded numeric;
malformed or unsupported declared shapes fail closed rather than rounding.

## Enforcement

SQL source policy 1.1 permits aliased SUM/COUNT/MIN/MAX/AVG projections and
optional GROUP BY on explicit authorized source columns of one physical table.
COUNT(*) is a row count, never a projection wildcard. Non-aggregate projections
use physical source-column identity: table column-alias lists and decorated
wildcards are rejected, including outside grouped queries. Ordinary table
aliases remain supported. Non-aggregate projections
must be grouping keys; nested/wrapped aggregates, HAVING, DISTINCT aggregates,
grouping expressions/ordinals, ROLLUP and grouping sets remain rejected.
Grouped/aggregate queries referencing sensitive-name source columns fail closed
before derived queries, including aliases and predicate-only references.
Existing table/column authorization, AST/statement/scan/result/time budgets and
source-free profile wrappers apply unchanged. Grouping does not declassify values
or authorize disclosure of small groups. Aggregate profiles do not support
automatic dependency-preserving inference, including COUNT(*) without columns.

Query profiles carry value-free `has_unmodeled_expressions` metadata. A
source-dependent non-column projection marks the profile unsupported for
automatic `infer_dataset_spec`; profiling itself remains permitted. Direct
column aliases do not set the flag. Saved SQL profiles lacking this metadata
must be reprofiled before automatic inference; non-query legacy profiles keep
their prior inference behavior. No SQL expressions or literals are persisted by
this flag. Explicit independently authored specifications are not automatic
SQL-dependency inference and must not be advertised as preserving query formulas.

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
- MCP 2 unexpected errors remain generic and detached. Only exact typed
  transformation-limit and query-work-budget failures retain reconstructed,
  value-free dimensions, counters and supported recovery settings; never forward
  arbitrary exception messages or backend causes.
- Reject malformed typed MCP requests and notifications before SDK dispatch;
  never pass their caller-controlled values into SDK logs or exceptions.
- Audit-log capacity must reject a new invocation before its `started` record
  unless one maximum-size terminal record is reserved; an admitted terminal
  event must not be dropped at the configured admission threshold.

Keep the Trino dependency optional for workflows that do not use Trino. Mock
Trino responses in normal unit tests; use live access only in explicitly gated
integration checks.

MCP transformation adapters check the active request deadline at every existing
transformation work checkpoint, including immediately before publication. The
generation deadline also applies. Detached parser failures are rechecked at the
adapter boundary to retain typed deadline diagnostics; cleanup-incomplete errors
retain precedence over deadline reporting.

Rule residual queries reject sensitive-name target and arithmetic/value operands before execution. Formula dependencies share the existing name sensitivity classifier; aggregate mappings guard parent values and numeric child values. Relationship keys remain usable without returning their values. These checks do not claim content detection for innocuously named source columns.

SQL-query exact local categories require an authorized direct physical-column projection. Both physical source and output names must pass the shared sensitive, identifier and quasi-identifier policy. Aliases cannot grant disclosure permission; derived expressions and manually constructed plans without explicit category authorization fail closed. This applies to PostgreSQL and Trino.

PostgreSQL defaults to certificate and hostname verification (`verify-full`). All weaker TLS modes require explicit local insecure opt-in before password resolution or driver connection. JDBC and component configuration share this guard; driver errors never trigger a weaker-mode retry.

Ordinary Trino table category summaries bound the projected VARCHAR inside
the grouping query before driver return: at most
`TEST_DATA_AGENT_MAX_INPUT_CELL_CHARS` characters (default 1,000,000) and four
times that many UTF-8 bytes. Guard and projection use the same representation,
including CHAR conversion; grouping/counts retain the original column.
Oversized values yield a NULL sentinel that rejects the whole profile before
sensitivity classification. No truncation, filtering or incomplete summary
is published. Existing cumulative result and query budgets still apply.

SQL syntax and tokenizer failures (including unterminated strings, quoted
identifiers and block comments) use a fixed `invalid SQL` diagnostic detached from parser
exception cause and context. Parser excerpts and query literals must never reach
direct API errors or MCP responses, including the supported MCP 1 transport.

Formula syntax errors and local query-source parser failures also detach the
original parser cause/context, preserving fixed value-free recovery messages.

The closed candidate Trino result-capture mapper retains declared scalar integer
widths and decimal precision/scale. Unsupported declarations reject with a fixed
error; they must not be coerced into text or rounded. This helper is not a public
row-returning registration or proof of supervised capture acceptance.
