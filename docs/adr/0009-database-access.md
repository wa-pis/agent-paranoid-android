# ADR-0009: Authorize database access before I/O

- Status: Accepted — retrospective baseline.
- Recorded: 2026-09-29. This is the recording date, not an invented original approval date.
- Authority and implementation boundaries: see Evidence below and the [register conventions](index.md#status-and-authority).

## Context

Database metadata and convenient configuration syntax can widen access if interpreted as authority.

## Decision

Keep PostgreSQL/Trino read-only, allowlisted and resource-bounded. Validate identifiers and authorization below transports before execution. PostgreSQL uses forced read-only sessions; clients own bounded fetches, deadlines and cleanup.

Credential-free JDBC-style strings are endpoint syntax only, not a JVM/JDBC runtime or a session-property escape. Reject secrets, unknown/session-changing options and component conflicts. Expand table-qualified column wildcards from bounded metadata into a frozen explicit-column set. A wildcard does not authorize literals, rows or preservation.

## Alternatives and consequences

Arbitrary SQL and permissive connection strings were not selected. Wildcards improve ergonomics but still require exact table authorization. Driver errors are redacted; a more specific safe category is permitted only from trusted typed evidence, not parsed backend messages.

## Evidence

Sources: [database safety guide](../agent-guides/trino-security.md), [configuration specification](https://github.com/wa-pis/agent-paranoid-android/blob/637065966c12584e11c9b437c1e8b8f8d708c0df/openspec/specs/database-source-configuration/spec.md), [allowlist specification](https://github.com/wa-pis/agent-paranoid-android/blob/637065966c12584e11c9b437c1e8b8f8d708c0df/openspec/specs/database-source-allowlists/spec.md).
Executable anchors: [PostgreSQL client](https://github.com/wa-pis/agent-paranoid-android/blob/637065966c12584e11c9b437c1e8b8f8d708c0df/tests/test_postgres_client.py), [Trino policy](https://github.com/wa-pis/agent-paranoid-android/blob/637065966c12584e11c9b437c1e8b8f8d708c0df/tests/test_trino_sql_policy.py), [source adapters](https://github.com/wa-pis/agent-paranoid-android/blob/637065966c12584e11c9b437c1e8b8f8d708c0df/tests/test_sql_query_adapters.py).

## Revisit when

New database operations, authentication boundaries or wildcard shapes require explicit authorization/safety work; configuration convenience is not permission expansion.

