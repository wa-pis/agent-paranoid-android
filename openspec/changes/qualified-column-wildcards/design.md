# Design: qualified-column-wildcards

## Approach

Extend only the column-selector parser and metadata phase. Keep existing exact
allowlist models and trusted query builders by normalizing wildcard input to
the same explicit qualified-column representation they already consume.

```text
schema/table allowlists + qualified column selectors
                         ↓
             bounded metadata expansion
                         ↓
         immutable sorted explicit column snapshot
                         ↓
       existing quoted aggregate query builders
```

The two accepted forms are:

```text
PostgreSQL: schema.table.*
Trino:      catalog.schema.table.*
```

## Data And Contracts

The config boundary distinguishes an exact field selector from a
table-qualified wildcard. A PostgreSQL wildcard is valid only when its exact
parent table is already authorized by `POSTGRES_ALLOWED_TABLES`. A Trino
wildcard itself names one exact table and is valid only when unrestricted mode
is disabled and its catalog and schema match the mandatory allowlists.

The metadata phase requests column names for only those authorized tables,
validates every returned identifier, applies adapter visibility rules, and
charges the existing invocation budget. It then creates one immutable,
deduplicated, lexicographically ordered explicit-column snapshot.

All subsequent metadata and aggregate queries for the invocation use that
snapshot. Query builders receive explicit column names and emit quoted
identifiers; they do not receive wildcard tokens. The profiler records bounded
safe source identity and schema metadata, not the wildcard or raw metadata
response.

Local category preservation continues to use an exact entity-and-field
selector. A wildcard must never expand a preservation allowlist or authorize
exact source literals.

## Failure Modes

- Bare, partially qualified, repeated, or embedded wildcard: reject before
  connecting.
- Wildcard parent table is not explicitly authorized: reject before metadata
  access.
- Metadata response is empty, duplicated, malformed, over budget, or contains
  a column outside the requested table: fail the profile invocation.
- Schema changes between snapshot and profiling: fail closed on a mismatch;
  do not silently broaden or publish a partial profile.
- Query builder receives a wildcard token: treat it as an internal policy
  error and execute no SQL.

## Alternatives

- **Execute `SELECT *`:** rejected because authorization and SQL projection
  are different boundaries and the latter can return unexpected source data.
- **Allow schema-wide wildcards:** rejected because a newly created table could
  silently enter scope.
- **Expand once and persist forever:** rejected because stale authorization is
  difficult to review; expansion is invocation-scoped and deterministic.
