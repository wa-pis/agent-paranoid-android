# Design: database-source-documentation-reconciliation

## Approach

Use a layer-by-layer documentation matrix after all three runtime OpenSpecs are
implemented. Update each fact at its owning layer, then run a repository-wide
terminology and command audit.

Do not publish speculative user instructions. Before a feature is released,
active OpenSpec and roadmap may describe it as proposed, while README, how-to,
CLI reference, and stable support pages continue to describe only shipped
behavior.

## Documentation Matrix

### Discovery And Navigation

- `README.md`: concise supported-input summary, installation extras, and links
  to the complete workflows without presenting a JDBC implementation as Java.
- `docs/index.md`: route users by CSV, PostgreSQL table, Trino table, or SQL
  query source.
- `docs/getting-started/installation.md`: exact extras and no unnecessary base
  dependency.
- `docs/concepts/choosing-an-approach.md`: when to use component configuration,
  JDBC URL syntax, exact columns, qualified wildcard, or query source.
- `mkdocs.yml`: expose every new public page exactly once in a predictable
  section.

### Task Journeys And Examples

- `docs/how-to/postgresql.md` and `docs/how-to/trino.md`: complete commands for
  component/exact baseline, JDBC, qualified wildcard, and query-source paths.
- `examples/local_postgres/README.md` and
  `examples/local_trino/README.md`: prerequisites, explicit launcher matrix,
  safe placeholder configuration, outputs, cleanup, and expected failures.
- Runnable files required by the three feature OpenSpecs use only disposable
  synthetic sources, fixed seeds, installed-wheel commands, and checked-in
  non-sensitive SQL.

### Public Contracts And Reference

- `docs/reference/cli.md`: exact flags, defaults, mutual exclusion, input-file
  behavior, exit codes, JSON result shapes, and examples from current help.
- `docs/reference/configuration.md`: JDBC URL/component precedence, safe URL
  properties, exact/wildcard selectors, query and AST limits, secret
  indirection, and redacted errors.
- `docs/reference/stability.md`, `docs/reference/support-policy.md`, and
  `docs/reference/compatibility.md`: support level and additive/breaking rules.
- `docs/dataset_profile_and_spec.md`: virtual source identity, query
  fingerprint, aggregate evidence, and unchanged deterministic synthesis
  boundary.
- Public Python docstrings/import tables and one typed PostgreSQL/Trino request
  example match the exported API exactly.

### Safety, Architecture, And Operations

- `docs/concepts/safety-model.md` and `docs/concepts/threat-model.md`: URL/query
  inputs are untrusted and secret-adjacent; no query rows feed generation.
- `docs/operations/resource-budgets.md`: URL byte/component limits, wildcard
  expansion budgets, query bytes/AST complexity, and existing database work
  budgets.
- `docs/operations/troubleshooting.md`: fixed source-free recovery for malformed
  URLs, conflicts, unauthorized wildcard/query references, unsupported SQL,
  schema drift, and budget exhaustion.
- `docs/agent-guides/trino-security.md`, `docs/agent-guides/profiling.md`,
  `docs/implementation_map.md`, and
  `docs/reference/application-boundaries.md`: policy ownership and dependency
  direction match implementation.

### Planning And Release Records

- `docs/roadmap.md`, `CHANGELOG.md`, active/canonical OpenSpec, and release
  notes use the same feature names and status.
- The release acceptance checklist identifies exact runnable examples,
  installed-wheel commands, fake/no-network regressions, and any explicitly
  gated disposable integration evidence.
- Completed feature and documentation OpenSpecs are baselined and archived only
  after public docs describe the actual shipped behavior.

## Consistency Rules

Use these phrases consistently:

- **JDBC-style URL:** accepted syntax parsed into Python adapters; no JVM or
  JDBC driver.
- **Qualified column wildcard:** allowlist convenience expanded through
  metadata; executed trusted SQL enumerates explicit quoted columns.
- **SQL query source:** one bounded validated local `SELECT` profiled as a
  virtual aggregate-only source; not a general SQL runner.
- **Synthetic generation:** generated rows come from reviewed schema and
  aggregate evidence, never query or source rows.

No page may claim blanket unrestricted SQL, blanket `SELECT *`, credentials in
URLs, query-result export, or source-row generation. No page may retain the
obsolete absolute claim that wildcard syntax is impossible once the qualified
allowlist form ships.

## Verification

- Execute every displayed CLI command or extract it from a checked runnable
  example using an installed wheel.
- Freeze changed help, JSON, Python, and artifact contracts with focused golden
  or schema tests.
- Run fake/no-network PostgreSQL and Trino tests in normal CI; keep live
  disposable services explicitly gated and self-cleaning.
- Scan public docs for stale terms and contradictory safety claims.
- Run documentation contract tests, link checks, and `mkdocs build --strict`.
- Confirm manifests from all six new example launchers report
  `synthetic: true` and `source_rows_copied: false`.

## Failure Modes

- Runtime and docs disagree: fail documentation contracts and do not mark the
  reconciliation complete.
- A command requires a checkout-only path, unstated extra, live credential, or
  production service: reject the example and replace it with an installed-wheel
  synthetic path.
- Links, anchors, CLI help, JSON schema, or Python imports drift: fail CI.
- A safety statement is broader or weaker than enforced policy: keep the
  OpenSpec active and block release documentation completion.

## Alternatives

- **Update only README and two how-to pages:** rejected because public
  reference, safety, examples, architecture, and release evidence would drift.
- **Write all user docs before runtime:** rejected because speculative commands
  become false stable documentation.
- **Rely on manual release-day search:** rejected because the repository already
  supports executable documentation and contract checks.
