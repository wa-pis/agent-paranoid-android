# Design: sql-query-source-profiling

## Approach

Add a typed `SqlQueryProfileRequest` at the application/source-profiler
boundary and provider-specific policy adapters. Reuse the installed `sqlglot`
parser in database extras; do not add SQL parsing to the base installation.

```text
local bounded query file
        ↓
dialect parse + strict AST/source authorization
        ↓
trusted no-row schema inspection + aggregate query builders
        ↓
DatasetProfile(query fingerprint, schema, aggregates)
        ↓
existing infer -> review -> generate -> validate -> export
```

The public workflow uses `profile-query QUERY_FILE --adapter postgres|trino`
with explicit source id, virtual entity, and output options, followed by the
existing pipeline commands. SQL is accepted from a file, not as a command-line
string, to avoid shell history and process-list disclosure.

## Data And Contracts

A request contains:

- adapter kind (`postgresql` or `trino`);
- a stable user-supplied `source_id` and virtual entity name;
- a local query-file path;
- existing typed connection, allowlist, and budget configuration;
- optional exact local-category fields using virtual output field names.

The query file has a byte limit and UTF-8 requirement. Parsing must produce
exactly one `SELECT` in the selected adapter dialect. The initial subset allows
one physical table, explicit projections, unique aliases, deterministic scalar
expressions/casts, and a bounded filter expression. It rejects joins, CTEs,
subqueries, set operations, windows, table functions, commands, volatile or
unknown functions, locking clauses, and multiple statements.

Every physical table and source column resolves to the existing qualified
allowlists. A projection star is expanded to sorted explicit authorized
columns through the separate qualified-wildcard contract before trusted SQL
construction.

The query is canonicalized only for local validation and SHA-256
fingerprinting. The profile stores the fingerprint and a bounded policy
version, never the SQL text or SQL literals. Output aliases become virtual
field names only after identifier, uniqueness, count, and length validation.

Provider-specific query builders own schema introspection and aggregate SQL.
They may wrap the validated relation, but they must not execute it as a
row-returning request. Cursor/client APIs expose only bounded metadata and
aggregate result shapes to the profiler. The profile converter rejects any
unexpected row-shaped payload.

The resulting profile feeds the existing deterministic pipeline. Generation
uses schema and aggregate evidence, not query rows. Local preserve-as-is is
still exact-field, default-off, and subject to the existing classification,
content, cardinality, and length checks.

## Runnable Examples

Add one checked-in explicit-projection query and launcher per existing
disposable database example:

- `examples/local_postgres/query.sql` and
  `examples/local_postgres/run-query.sh OUTPUT` profile one filtered virtual
  entity from the checked-in synthetic PostgreSQL source.
- `examples/local_trino/query.sql` and
  `examples/local_trino/run-query.sh OUTPUT` profile one filtered virtual entity
  from the pinned synthetic Trino catalog.

The SQL files contain no credential or production-derived literal and stay
within the initial single-table subset. Each launcher runs from an installed
wheel, uses a stable source id, fixed seed, strict allowlists/budgets, and the
final frozen query-profile CLI contract. It completes profile, infer, generate,
and validate twice and proves deterministic output.

Example smoke tests assert that the profile contains the query fingerprint but
not query text or literals, manifests report `synthetic: true` and
`source_rows_copied: false`, generated rows do not equal the small checked-in
source rows, and cleanup removes disposable services. Fake/no-network tests
cover normal CI; live runs remain explicitly gated with the existing local
database examples.

## Failure Modes

- Missing, oversized, non-UTF-8, or changed-during-read query file: reject
  before database access.
- Parse error, multiple statements, forbidden AST node/function, ambiguous or
  duplicate output name, or unauthorized reference: reject before execution.
- Wildcard expansion exceeds authorization or metadata budgets: reject with a
  fixed source-free policy error before aggregate execution.
- Schema introspection returns an unsupported type or unexpected result shape:
  fail the whole profile.
- Timeout, scan/statement/result budget exhaustion, cancellation, backend
  failure, or schema drift: close resources and publish no partial profile.
- Error presentation: return only a fixed reason code, source id, and optional
  safe location; never SQL text, literals, endpoint, backend message, or source
  values.

## Alternatives

- **Fetch query rows and feed them to generation:** rejected because that
  creates a source-row copying path.
- **Expose arbitrary read-only SQL:** rejected because read-only does not bound
  resource use, data disclosure, volatile functions, or query complexity.
- **Accept SQL directly on the command line:** rejected because SQL and its
  literals can enter shell history and process listings.
- **Support the full SELECT grammar immediately:** rejected because joins,
  CTEs, subqueries, and windows need separate semantics and resource evidence.
- **Require users to create a view:** safe but unnecessarily operationally
  heavy for a reviewed local query workflow.
