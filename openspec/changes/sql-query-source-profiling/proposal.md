# Change Proposal: sql-query-source-profiling

## Summary

Let a user define one read-only SQL `SELECT` as a local virtual database source
for the existing safe pipeline:

```text
query file -> safe aggregate profile -> infer spec -> deterministic generation
```

The query identifies and shapes source evidence. Its result rows are never
returned, persisted, sent to a provider, or used directly as generated rows.

## Motivation

Real test-data tasks often start from a reviewed reporting query rather than a
whole physical table. Requiring users to create a database view first adds
operational work and excludes derived columns and filters that already express
the intended test-data shape.

## Dependencies

- JDBC-style URL support is the intended common connection UX but is not a
  prerequisite for the underlying typed Python request.
- `SELECT *` or `alias.*` support in a query is blocked until the
  `qualified-column-wildcards` change is implemented. Without that dependency,
  every projected field must be explicit.
- Implementation is a separate PR after both lower-level contracts are
  reviewed; it must not be combined with either parser change.

## Scope

In scope:

- A local query-file input for one PostgreSQL or Trino `SELECT` statement.
- A user-supplied safe source id and one virtual entity with unique validated
  output field names.
- AST validation before database access and engine-specific trusted schema and
  aggregate profiling around the validated derived relation.
- Explicit projections, aliases, deterministic scalar expressions, filters,
  and allowlisted table references within a deliberately small documented SQL
  subset.
- Existing connection, schema/table/column authorization and all resource
  budgets, including a bound on query-file bytes and AST complexity.
- A source-free profile containing a query fingerprint, safe schema metadata,
  aggregates, assumptions, and warnings.
- The existing `infer-spec`, review, generate, validate, and export stages.
- Runnable PostgreSQL and Trino query-source examples using checked-in SQL over
  disposable synthetic sources and the complete deterministic pipeline.

Out of scope:

- DDL, DML, commands, procedures, side-effecting or volatile functions,
  multiple statements, comments carrying directives, or unrestricted SQL.
- Returning query rows, exporting query results, using query rows as generated
  fixtures, or preserving row order.
- Provider or MCP access to query text, query literals, backend errors, or
  result values.
- A general SQL execution command or extending the existing row-returning
  Trino tool.
- Joins, CTEs, recursive queries, subqueries, set operations, windows, table
  functions, or dialect features in the first implementation. They require
  later focused deltas with resource and semantic evidence.
- Automatic relationship inference from one derived entity.

## Safety Impact

The SQL file is untrusted and secret-adjacent because it may contain business
logic or literals. It is byte-bounded, parsed locally, validated against a
strict AST policy, and never serialized or echoed. Every referenced physical
table and column must already be authorized.

The adapter does not fetch the derived result set. It uses trusted,
adapter-owned schema introspection and aggregate queries around the validated
relation. Backend read-only enforcement, statement/scan/result/time budgets,
response accumulation limits, and cleanup remain mandatory. A query
fingerprint may be retained; query text and source literals may not.

## Compatibility

This is an additive source-profiling surface. Existing CSV, PostgreSQL table,
Trino, MCP, Python, `DatasetProfile`, `DatasetSpec`, generation, validation,
and output contracts retain their defaults. Generated data remains synthetic
and deterministic under an explicit seed.

Existing table-profile examples remain available. Query examples are additive
and must identify their virtual entity and source fingerprint without storing
the SQL text in generated artifacts.

## Release Impact

Implementation adds a public input surface and a new SQL security boundary and
therefore requires a future minor release candidate and focused independent
review. This proposal does not change the package version, create a tag, or
publish artifacts.
