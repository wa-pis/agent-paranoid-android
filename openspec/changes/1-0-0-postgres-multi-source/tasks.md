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
- [ ] Extend the typed field-scoped local category policy to source-qualified
  PostgreSQL entities without adding a global masking bypass.
- [ ] Define the additive PostgreSQL SQL output contract and deterministic
  artifact metadata.

## Selective As-Is Preservation

- [ ] Reuse the explicit `LocalCategoryField` scope for local files and
  canonical source-qualified PostgreSQL fields.
- [ ] Require reviewed non-sensitive business enum/constant classification and
  fail-closed PII, secret, identifier, quasi-identifier, and free-text checks.
- [ ] Enforce cardinality, value-length, and profiling budgets before retaining
  exact values or counts.
- [ ] Preserve approved values, distributions, and conditional rules through
  local profile, specification, deterministic generation, and SQL export.
- [ ] Replace all source literals at external provider boundaries and suppress
  them from default MCP responses, logs, errors, and source metadata.
- [ ] Add focused tests for default-off behavior, exact approved values,
  rejected unsafe/unbounded values, source-row exclusion, and destination
  egress prevention.

## PostgreSQL Adapter

- [x] Add an optional `postgres` dependency profile with minimum/latest support
  evidence and no base-installation dependency.
- [x] Implement injected PostgreSQL driver and connection/session boundary.
- [ ] Enforce schema/table allowlists, read-only mode, identifier validation,
  statement timeout, lock timeout, cancellation, cleanup, and invocation
  budgets.
- [x] Add metadata query builders for tables, columns, nullability, primary
  keys, foreign keys, and supported CHECK constraints.
- [ ] Add aggregate query builders for row counts, cardinality, null ratios,
  ranges, safe categories, FK coverage, and configured reconciliation checks.
- [x] Normalize results into `DatasetProfile(source_type="postgres")` without
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

- [x] Add one documented CLI/configuration path and one Python API example from
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
  and roadmap documentation; record PostgreSQL, selective preservation, and
  SQL export as RC6 scope inherited by the stable gate.
- [ ] Add public wheel/install, `doctor`, profile, generation, validation, and
  upgrade acceptance for the `postgres` extra and base installation.
- [x] Add a documented CLI and Python path that writes one PostgreSQL `.sql`
  file from validated generated records.
- [x] Implement deterministic PostgreSQL identifier, type, scalar literal,
  NULL, DDL, INSERT, and relationship rendering without a live connection.
- [x] Publish SQL through a temporary sibling and atomic replacement; reject
  unsupported input without leaving a partial target.
- [x] Add golden and parser tests for valid PostgreSQL syntax, stable ordering,
  quoting, literals, NULL, foreign keys, approved as-is values, and failures.
- [ ] Add isolated-wheel PostgreSQL/SQL smoke coverage without live database
  access, plus an optional explicitly gated disposable-PostgreSQL execution
  check.
- [ ] Run lint, type checking, compile, focused tests, full tests, documentation
  build, dependency/license checks, and the release acceptance workflow on the
  exact implementation commit.
