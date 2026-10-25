## ADDED Requirements

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
