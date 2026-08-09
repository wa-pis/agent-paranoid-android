# Change Proposal: 1-0-0-postgres-multi-source

## Summary

Add a provider-neutral source-adapter boundary and a first direct PostgreSQL
adapter before stable `1.0.0`. The adapter will produce the existing safe
`DatasetProfile` contract from read-only PostgreSQL metadata and bounded
aggregate evidence, without making Trino a prerequisite.

Extend the same boundary to named source bundles. A bundle may contain several
PostgreSQL databases on different hosts, one Trino coordinator with multiple
catalogs, or several independent Trino coordinators. Stable source identities,
per-source budgets, and one bundle-wide budget will keep the resulting profile
and relationship graph unambiguous.

## Motivation

The current direct database path is Trino-specific. This works for teams that
already operate a Trino coordinator, but excludes a common PostgreSQL-only
deployment and makes the product appear to require an infrastructure layer the
user may not have.

Trino coordinators remain useful: one coordinator can federate several catalogs
and backend databases. They must be represented as a source boundary rather
than conflated with the databases behind them. Multiple coordinators and direct
PostgreSQL connections need the same review, profiling, and generation path.

The product must preserve relationships and order-of-magnitude shape across
several sources without copying source rows or silently treating an inferred
cross-source relationship as a declared foreign key.

## Scope

In scope:

- A small source-profiler port that normalizes source metadata and aggregate
  evidence into the existing deterministic profile/generation pipeline.
- An optional `postgres` installation profile with an injected driver boundary,
  validated read-only session setup, schema/table allowlists, and bounded work.
- PostgreSQL metadata extraction for tables, types, nullability, primary keys,
  foreign keys, and a supported safe subset of checks.
- Aggregate PostgreSQL profiling for row counts, null ratios, cardinality,
  ranges, safe distributions, and bounded relationship/reconciliation evidence.
- Named `SourceBundle` inputs for multiple PostgreSQL hosts, one Trino
  coordinator with multiple catalogs, or multiple Trino coordinators.
- Stable source-qualified entity identities and source metadata that do not
  use hostnames, DSNs, credentials, or provider payloads as public identity.
- Independent per-source budgets plus a non-resettable bundle-wide budget.
- Explicit handling of local declared relationships, cross-source hypotheses,
  and optional bounded same-coordinator cross-catalog aggregate checks.
- A documented CLI/Python path, synthetic PostgreSQL fixture, and clean-
  environment acceptance evidence before stable `1.0.0`.

Out of scope:

- Making Trino mandatory for PostgreSQL users.
- Arbitrary caller-provided SQL, write access, `SELECT *`, or row-returning
  profiling as a default capability.
- Automatic support for every relational database or automatic Django,
  SQLAlchemy, or other ORM introspection in this change.
- Cross-host raw-value joins, copying source rows between databases, or sending
  source values to an AI provider.
- Automatic approval of AI-discovered relationships or business rules.
- A requirement that AI, MCP, or a network provider be present for the
  deterministic PostgreSQL workflow.

## Safety Impact

Every PostgreSQL connection is read-only, allowlisted, and resource-bounded.
The adapter generates only trusted internal aggregate queries and metadata
queries; it does not expose a general SQL execution port. Connection failures,
DSNs, hostnames, backend error text, and credentials stay outside profiles,
manifests, logs, provider requests, and public errors.

Default profiles contain schema metadata, counts, non-reversible distributions,
and relationship evidence, not source rows. AI, when enabled, receives the same
safe profile and may rank hypotheses but cannot access a connection or approve
generation. A requested source or table that cannot be profiled fails closed;
the system must not silently publish a partial bundle as complete.

## Compatibility

- The base installation remains PostgreSQL- and Trino-free.
- The new `postgres` extra is optional and follows the existing dependency and
  support-matrix policy.
- Existing CSV, JSON, Parquet, Trino, CLI, MCP, `DatasetSpec`, and artifact
  contracts remain compatible unless an additive source-bundle contract is
  explicitly introduced and covered by golden fixtures.
- Single-source profiles continue to use the existing `DatasetProfile` shape.
- Multi-source profiles use stable qualified entity names and a versioned
  source-bundle metadata contract; credentials and host-specific connection
  details are never serialized.
- Existing Trino coordinator configuration remains valid. A coordinator is
  one named source with catalog/schema allowlists; catalogs are not modeled as
  independent credentials or connections.
