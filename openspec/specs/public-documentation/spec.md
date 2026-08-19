# Public Documentation Specification

## Purpose

Keep public database-source guidance executable and aligned with shipped safety
contracts.

## Requirements

### Requirement: Database Source Documentation Matches Shipped Behavior

Every public documentation layer SHALL describe the same shipped JDBC URL,
qualified wildcard, and SQL query source contracts as CLI help, Python models,
configuration validation, safety policy, and runnable examples.

#### Scenario: Feature is not yet implemented

- **GIVEN** an active OpenSpec whose runtime has not shipped
- **WHEN** stable README, how-to, reference, support, and example pages are
  rendered
- **THEN** they do not present its commands or configuration as available
- **AND** proposal status is limited to roadmap and active OpenSpec material

#### Scenario: Feature is implemented

- **GIVEN** an implemented database source contract
- **WHEN** documentation reconciliation runs
- **THEN** discovery, how-to, example, CLI, Python, configuration, safety,
  architecture, operations, roadmap, changelog, and release layers describe
  the same behavior and terminology
- **AND** all displayed commands and imports are verified against an installed
  package

### Requirement: Documentation Preserves Database Safety Boundaries

Documentation SHALL distinguish JDBC-style endpoint syntax from JDBC runtime,
qualified wildcard authorization from SQL projection, and SQL query profiling
from arbitrary SQL or row-returning execution.

#### Scenario: Qualified wildcard is documented

- **GIVEN** a PostgreSQL or Trino table-qualified wildcard example
- **WHEN** a user follows the documentation
- **THEN** the wildcard expands through bounded metadata to explicit columns
- **AND** the documentation does not claim that executed SQL contains
  `SELECT *` or that preserve-as-is is implicitly enabled

#### Scenario: SQL query source is documented

- **GIVEN** a checked-in safe query-source example
- **WHEN** a user follows the complete workflow
- **THEN** it produces a safe aggregate profile and deterministic synthetic
  output without returning or copying query rows
- **AND** query text, literals, credentials, endpoints, and backend errors are
  documented as forbidden at external and generated-artifact boundaries

### Requirement: Documentation And Examples Are Executable

The repository SHALL validate public links, CLI commands, Python imports,
configuration snippets, and all PostgreSQL/Trino component, JDBC, wildcard,
and query-source launchers through documentation contracts and installed-wheel
smoke tests.

#### Scenario: Documentation verification succeeds

- **GIVEN** the exact candidate package and checked synthetic fixtures
- **WHEN** documentation and example verification runs
- **THEN** links and strict MkDocs build pass
- **AND** each launcher validates deterministic generated output whose manifest
  reports `synthetic: true` and `source_rows_copied: false`

#### Scenario: Documentation drifts from runtime

- **GIVEN** a stale flag, import, default, error, output, link, support claim,
  or safety statement
- **WHEN** documentation contracts run
- **THEN** CI fails
- **AND** the documentation reconciliation change remains incomplete
