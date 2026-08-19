# Change Proposal: database-source-documentation-reconciliation

## Summary

Reconcile every public and maintainer-facing documentation layer after the
JDBC URL, qualified column wildcard, and SQL query source changes are
implemented. The final documentation must describe one coherent database
source workflow and must match the exact shipped CLI, Python, configuration,
safety, example, and release contracts.

## Motivation

The three database-source changes affect different boundaries but are likely
to be used together. Updating only one how-to page per implementation would
leave conflicting setup instructions, stale absolute safety claims, missing
Python/configuration reference, or examples that do not match the installed
CLI.

Documentation is part of the public contract. It needs an explicit final gate
rather than relying on a best-effort search immediately before release.

## Dependencies

This change follows, and does not implement:

1. `database-jdbc-connection-urls`;
2. `qualified-column-wildcards`;
3. `sql-query-source-profiling`.

Each feature implementation updates its owned docs and examples. This change
performs the cross-feature audit after all implemented contracts are known.

## Scope

In scope:

- Product discovery and navigation: `README.md`, `docs/index.md`, installation,
  choosing-an-approach, and MkDocs navigation.
- Task journeys: PostgreSQL and Trino how-to pages plus every new launcher and
  README under `examples/local_postgres` and `examples/local_trino`.
- Public reference: CLI help/reference, configuration, stability/support,
  profiles/specs, public Python imports and typed request examples.
- Safety and operations: safety model, threat model, profiling and Trino agent
  guides, resource budgets, troubleshooting, and application boundaries.
- Planning and release-facing records: active/canonical OpenSpec, roadmap,
  changelog, release notes, and the acceptance checklist for the release that
  ships the behavior.
- Documentation contract tests, installed-wheel command/example smoke tests,
  link validation, and strict MkDocs build.
- Removal or correction of stale statements that conflict with the exact
  field, query, destination, and resource policies.

Out of scope:

- Implementing or changing JDBC parsing, wildcard expansion, SQL policy,
  profiling, generation, providers, MCP, or output formats.
- Publishing examples or commands before their runtime exists.
- Adding another database engine, connection syntax, query feature, or output
  format under a documentation-only change.
- Creating a release, tag, or package publication.

## Safety Impact

Documentation must preserve the distinction between authorization syntax and
executed SQL: qualified wildcard allowlists may expand to explicit columns,
but trusted queries never execute a projection star. SQL query sources remain
strictly parsed, allowlisted, read-only, aggregate-only inputs and never create
a source-row path into generation.

JDBC-style URLs are endpoint syntax only, not a Java/JDBC runtime or a place
for credentials. Query text, URL values, credentials, backend errors, source
literals, and source rows remain absent from external providers, default MCP,
logs, errors, profiles where forbidden, and generated artifacts.

## Compatibility

This change is documentation and contract-test only. It does not alter public
runtime behavior. Existing component/exact-table workflows remain documented
alongside the additive JDBC, wildcard, and query-source workflows.

## Release Impact

Documentation-only reconciliation does not require a new release candidate
when the accepted runtime tree is unchanged. It is nevertheless a mandatory
gate for the release that first publishes any of the three behaviors. This
proposal does not change the version, create a tag, or publish artifacts.
