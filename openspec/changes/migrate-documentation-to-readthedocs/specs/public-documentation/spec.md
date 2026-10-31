## ADDED Requirements

### Requirement: Managed Hosting Preserves Verified Documentation Editions

Read the Docs hosting SHALL preserve existing MkDocs content, verified edition
identities and portable downloads. A host build or newly discovered tag SHALL
NOT alone advance the verified stable/default edition.

#### Scenario: Reader selects an edition

- **GIVEN** stable, candidate and development documentation editions
- **WHEN** a reader selects one on Read the Docs
- **THEN** bilingual navigation and default search stay within that edition
- **AND** package/source/documentation identities and release status are visible

#### Scenario: Historical release lacks hosting configuration

- **WHEN** an immutable old release is made discoverable
- **THEN** a matching reviewed documentation ref or retained verified snapshot
  preserves its original content and package identity
- **AND** release tags are not moved and current prose is not relabelled

#### Scenario: Normal edition provides downloads

- **WHEN** a normal version build is published
- **THEN** PDF, standalone HTML, Markdown ZIP and offline site ZIP remain
  available with identity, chapter inventory and verified hashes
- **AND** public manifest, chapter inventory and file hashes match retained
  evidence from the same trusted build, not only a manifest served by the site
- **AND** a missing or mismatched required export prevents verified promotion

### Requirement: Documentation Pull Request Previews Are Isolated

Documentation PRs SHALL have a visible build status and a labelled preview on
success. Untrusted previews SHALL NOT receive private variables, production
inputs or verified-edition publication credentials, or change stable defaults.

#### Scenario: Contributor proposes a change

- **WHEN** a fictional documentation PR is built
- **THEN** its preview is distinguishable from released guidance
- **AND** failure reports a failed build without replacing a verified edition
- **AND** existing strict documentation and release identity gates stay enforced

### Requirement: Documentation Hosting Switch Retains Verified Recovery

The canonical entry point SHALL switch only after parallel strict build,
identity, version, link and download checks pass. Existing Pages URLs SHALL
remain usable through retained content or tested mappings. A known-good
retained deployment and documented rollback SHALL remain available.

#### Scenario: Parallel validation fails

- **WHEN** a build, public identity, version mapping or hash check fails
- **THEN** the known-good default stays unchanged
- **AND** failure is not recorded as verified or used to retire fallback

#### Scenario: Host switches successfully

- **GIVEN** parallel verification and rollback rehearsal have passed
- **WHEN** the canonical entry point changes
- **THEN** old deep links, historical evidence and downloads remain usable
- **AND** only replaced hosting steps are removed, retaining CI/export/release
  verification and recovery functionality
