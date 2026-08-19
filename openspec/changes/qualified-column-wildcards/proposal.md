# Change Proposal: qualified-column-wildcards

## Summary

Allow a table-qualified wildcard in PostgreSQL and Trino column allowlists as
a convenience for authorizing all columns currently visible on one explicitly
allowlisted table. The wildcard is expanded through bounded metadata discovery
into a stable explicit column snapshot before any profiling query is built.

This change does not permit `SELECT *` in executed SQL.

## Motivation

Exact column allowlists are safest but tedious for wide tables and fragile when
a team intentionally authorizes a whole table. Users should be able to express
that intent once without weakening table scope, query construction, or resource
budgets.

## Scope

In scope:

- PostgreSQL selectors of the exact form `schema.table.*`.
- Trino selectors of the exact form `catalog.schema.table.*`.
- Metadata-only expansion for a PostgreSQL table already present in its exact
  table allowlist, or a Trino table named exactly by the selector inside
  mandatory catalog/schema allowlists.
- Deterministic deduplication and ordering when exact and wildcard selectors
  are combined.
- One invocation-scoped expansion snapshot with existing table, column,
  statement, response, scan, and wall-clock budgets.
- Explicit quoted columns in every downstream trusted query.

Out of scope:

- Bare `*`, schema/catalog wildcards, recursive discovery, pattern matching,
  or wildcard table names.
- Allowing projection stars in caller-provided SQL or changing
  `run_safe_select` policy.
- Treating a wildcard as permission to return rows, preserve source values,
  disclose literals, or bypass sensitive-field handling.
- Automatic inclusion of columns that appear after the invocation snapshot.

## Safety Impact

Wildcard expansion occurs only after schema and table authorization and before
aggregate query construction. Expansion fails closed if metadata is missing,
ambiguous, empty, changes during the operation, or exceeds any budget. Trusted
queries continue to enumerate correctly quoted identifiers.

The wildcard authorizes aggregate profiling scope only. It never authorizes
local preserve-as-is, source-row return, provider disclosure, MCP literal
return, or raw SQL. Preserve-as-is remains exact-field, explicit, default-off,
and independently validated.

## Compatibility

Existing exact column selectors keep their meaning. Qualified wildcard support
is additive, and exact plus wildcard entries normalize to the same deterministic
explicit snapshot. Existing SQL policy continues to reject actual projection
stars.

## Release Impact

Implementation changes public database configuration and authorization
behavior and therefore requires a future minor release candidate. This
proposal does not change the package version, create a tag, or publish
artifacts.
