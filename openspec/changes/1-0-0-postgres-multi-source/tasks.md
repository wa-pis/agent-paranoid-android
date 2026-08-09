# Tasks: 1-0-0-postgres-multi-source

## Contracts And Models

- [ ] Define the typed source-profiler port and keep deterministic profile
  conversion independent of database drivers.
- [ ] Define `SourceScope`, `SourceRef`, `PostgresSource`, source-bundle
  metadata, and canonical qualified entity identity.
- [ ] Define additive, versioned source-bundle/profile metadata fixtures without
  placing credentials, DSNs, hostnames, or raw source values in artifacts.
- [ ] Define local declared relationship versus cross-source hypothesis status
  and evidence semantics.

## PostgreSQL Adapter

- [ ] Add an optional `postgres` dependency profile with minimum/latest support
  evidence and no base-installation dependency.
- [ ] Implement injected PostgreSQL driver and connection/session boundary.
- [ ] Enforce schema/table allowlists, read-only mode, identifier validation,
  statement timeout, lock timeout, cancellation, cleanup, and invocation
  budgets.
- [ ] Add metadata query builders for tables, columns, nullability, primary
  keys, foreign keys, and supported CHECK constraints.
- [ ] Add aggregate query builders for row counts, cardinality, null ratios,
  ranges, safe categories, FK coverage, and configured reconciliation checks.
- [ ] Normalize results into `DatasetProfile(source_type="postgres")` without
  returning source rows or exact sensitive numeric values.
- [ ] Convert unsupported/ambiguous database constraints into bounded review
  warnings rather than silently dropping them or exposing raw expressions.

## Multi-Source And Trino Federation

- [ ] Implement the source-bundle orchestrator with independent source budgets
  and one non-resettable bundle-wide budget.
- [ ] Support multiple PostgreSQL hosts as independent source aliases.
- [ ] Reuse the existing Trino boundary for one coordinator with multiple
  catalogs and for multiple coordinator aliases.
- [ ] Allow same-coordinator cross-catalog aggregate checks only behind explicit
  policy; do not add implicit cross-host joins.
- [ ] Fail closed on missing sources or required operations; never publish a
  partial bundle as complete.
- [ ] Keep AI optional and pass only safe profile metadata/hypotheses across the
  advisor boundary.

## User Workflow And Release Evidence

- [ ] Add one documented CLI/configuration path and one Python API example from
  PostgreSQL profile to reviewed spec, generation, and validation.
- [ ] Add a synthetic PostgreSQL fixture with multiple tables, PK/FK/CHECK,
  nullable fields, distributions, and one reconciliation rule.
- [ ] Add isolated unit tests with a fake driver; normal tests must not require
  a live PostgreSQL or Trino coordinator.
- [ ] Add opt-in integration coverage against a disposable PostgreSQL service
  and a disposable Trino coordinator with multiple catalogs where CI supports it.
- [ ] Add regression tests for source-row, secret, DSN, host, backend-error,
  arbitrary-SQL, partial-profile, cross-source, and budget bypass attempts.
- [ ] Update README, installation, configuration, product-validation, support,
  and roadmap documentation; distinguish current RC6 support from the new
  stable gate.
- [ ] Add public wheel/install, `doctor`, profile, generation, validation, and
  upgrade acceptance for the `postgres` extra and base installation.
- [ ] Run lint, type checking, compile, focused tests, full tests, documentation
  build, dependency/license checks, and the release acceptance workflow on the
  exact implementation commit.
