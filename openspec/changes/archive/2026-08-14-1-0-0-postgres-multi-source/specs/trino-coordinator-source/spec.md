# Trino Coordinator Source Delta

## ADDED Requirements

### Requirement: A Trino Source Represents One Coordinator Boundary

A configured Trino source SHALL represent one coordinator endpoint with
allowlisted catalogs and schemas. Catalogs behind that coordinator SHALL share
the same connection boundary and SHALL be qualified as
`source_id.catalog.schema.table` in multi-source profiles.

#### Scenario: One coordinator exposes several catalogs

- **GIVEN** source `warehouse` exposes `hr`, `payroll`, and `crm` catalogs
- **WHEN** the source is profiled
- **THEN** all selected entities use the `warehouse` source alias
- **AND** catalog/schema/table allowlists are applied before profiling
- **AND** the adapter does not create an independent credential boundary per
  catalog

### Requirement: Multiple Coordinators Are Independent Sources

Two Trino coordinators SHALL be configured as two independent source aliases.
Each coordinator SHALL retain independent credentials, allowlists, local
budgets, failures, and audit correlation. A coordinator SHALL NOT be inferred
to have access to another coordinator's catalogs.

#### Scenario: EU and US coordinators expose similar catalogs

- **GIVEN** `analytics_eu` and `analytics_us` are separate coordinators
- **WHEN** both are included in a source bundle
- **THEN** their entities remain source-qualified and distinct
- **AND** one coordinator cannot execute a query through the other
- **AND** the bundle budget covers both independently

### Requirement: Cross-Catalog Checks Are Explicit And Aggregate-Only

Same-coordinator cross-catalog relationship or reconciliation checks SHALL be
disabled unless explicitly enabled by policy. When enabled, they SHALL use
internally generated bounded aggregate queries, preserve the coordinator's
allowlists, and consume both local and bundle budgets. Direct PostgreSQL sources
on different hosts SHALL NOT receive implicit cross-source join capability.

#### Scenario: Cross-catalog check is not enabled

- **GIVEN** two allowlisted catalogs are behind one coordinator
- **WHEN** a profile requests a cross-catalog check without the explicit policy
- **THEN** the check is not executed
- **AND** the result remains a reviewable hypothesis or unknown

#### Scenario: Cross-catalog aggregate exceeds a budget

- **GIVEN** an explicitly enabled cross-catalog aggregate would exceed the
  remaining invocation or bundle budget
- **WHEN** the check is planned
- **THEN** it is rejected before execution
- **AND** no source rows or partial join result are returned
