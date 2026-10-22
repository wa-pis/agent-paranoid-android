# Public Documentation Specification

## Purpose

Keep user guidance concise, version-bound, executable and aligned with shipped
safety contracts, with separate historical evidence and portable exports.

## Requirements

### Requirement: Database Source Documentation Matches Shipped Behavior

Public docs SHALL match CLI help, Python models, configuration, safety policy
and runnable examples for shipped JDBC URL, wildcard, SQL source, generation,
artifact and CLI/MCP contracts. Guides SHALL distinguish stable and candidate
versions, registered surfaces, dataset authorization and unfinished acceptance.
Historical evidence SHALL retain its original source identity.

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

#### Scenario: Registered candidate surface has remaining acceptance work

- **GIVEN** a published candidate registers a CLI command or MCP tool and a
  separate acceptance campaign remains incomplete
- **WHEN** current usage, configuration and architecture pages are reconciled
- **THEN** they identify the installed surface and its actual arguments without
  describing it as unregistered or claiming the separate campaign passed
- **AND** registration and release acceptance do not grant dataset permission
  or replace required local preservation approval

#### Scenario: Current artifacts differ from a historical representation

- **GIVEN** a supported schema or manifest-marked output representation changes
- **WHEN** current examples and migration guidance are checked
- **THEN** examples parse under their declared schema and agree on logical
  values, format markers and overwrite behavior
- **AND** legacy unmarked artifacts and historical release evidence retain
  their explicitly documented contracts

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

### Requirement: Stable Documentation Is Task Oriented

Public documentation SHALL default to concise guidance for the latest publicly
verified stable release. Primary navigation SHALL prioritize user tasks and
canonical reference over release history, RC progress and acceptance evidence.
Consolidation SHALL retain operation-specific safety preconditions and preserve
historical evidence and accepted architectural decisions.

#### Scenario: Reader completes a current task

- **GIVEN** the stable documentation entry point
- **WHEN** a reader follows demo, generation, rules or transformation guidance
- **THEN** the route explains purpose, prerequisites, executable steps and result
- **AND** it does not require reading historical RC or acceptance narratives
- **AND** source-free generation and mixed-origin transformation stay distinct,
  including local approval conditions when preserving source values

#### Scenario: Historical material remains available

- **GIVEN** an old release or RC page removed from primary navigation
- **WHEN** a reader opens its previous link or uses the explicit archive
- **THEN** the evidence remains accessible with its original version/source identity
- **AND** its status is distinguishable from current stable guidance

### Requirement: Documentation Has Explicit Version Identity

Published version guides SHALL identify the package version, its bound source
commit and the documentation revision separately. Later guide corrections SHALL
NOT inherit the package source review. The default and version selector SHALL distinguish verified stable,
historical and prerelease documentation. Selected-version navigation and default
search SHALL avoid silently mixing those contracts.

#### Scenario: Reader selects an older release

- **GIVEN** an available version-bound documentation snapshot
- **WHEN** a reader selects it
- **THEN** guidance and examples match that release's supported behavior
- **AND** its version is visible and current stable guidance remains discoverable
- **AND** package and DatasetSpec schema versions are not conflated

#### Scenario: Snapshot does not exist

- **GIVEN** a historical release with evidence but no verified documentation snapshot
- **WHEN** versions are published or selected
- **THEN** current prose is not relabelled as that release's documentation
- **AND** historical evidence remains accessible with its actual provenance

### Requirement: Release Publication Keeps Documentation Current

The release procedure SHALL publish and verify matching versioned documentation
and preserve existing links. The stable pointer SHALL advance only after public
release verification and documentation checks succeed. These checks SHALL NOT
grant dataset access, preservation authority or activation of new extensions.

#### Scenario: New stable release becomes the default

- **GIVEN** a publicly verified stable release and matching documentation build
- **WHEN** version metadata, strict build, links and fictional installed-package
  examples pass and deployment identity is verified
- **THEN** the default points to that release and prior versions remain discoverable
- **AND** current roadmap and usage pages no longer describe completed release
  preparation as pending work

#### Scenario: Documentation publication fails

- **GIVEN** an existing known-good stable documentation default
- **WHEN** a new build or pre-deployment identity/export check fails
- **THEN** the prior deployed default is not replaced
- **AND** a deployment that fails public verification is not recorded as verified
- **AND** the documented recovery uses a retained successful deployment artifact

### Requirement: Version Bound Portable Documentation

Documentation builds SHALL provide a user handbook in PDF and standalone HTML,
a Markdown documentation source ZIP and a selected-version offline site ZIP. Exports SHALL identify package version,
package source and documentation revision, and include a chapter inventory and
artifact hashes. Docs export SHALL NOT read user datasets, receipts or secrets.

#### Scenario: Reader downloads documentation

- **GIVEN** a successfully built documentation version
- **WHEN** the reader selects PDF, HTML, Markdown or offline site download
- **THEN** the export matches that version and records its source identity
- **AND** bundled chapter links work offline and external reference links are explicit
- **AND** a failed export prevents publication of an incomplete new site

#### Scenario: Download is stale or mismatched

- **GIVEN** a deployed documentation identity and its export manifest
- **WHEN** a downloadable artifact or entry page differs from the built hashes
- **THEN** public documentation verification fails
- **AND** no package, data-access or preservation acceptance is inferred
