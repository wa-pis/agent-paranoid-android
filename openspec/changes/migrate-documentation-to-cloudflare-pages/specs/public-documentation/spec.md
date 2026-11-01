## ADDED Requirements

### Requirement: Managed Hosting Preserves Verified Documentation Editions

Cloudflare Pages hosting SHALL preserve existing MkDocs content, verified edition
identities and portable downloads. A host build or newly discovered tag SHALL
NOT alone advance the verified stable/default edition.

#### Scenario: Reader selects an edition

- **GIVEN** stable, candidate and development documentation editions
- **WHEN** a reader selects one on Cloudflare Pages
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

### Requirement: Cloudflare Publication Consumes Trusted Static Artifacts

Cloudflare publication SHALL use static artifacts from a verified source run.
Deployment credentials SHALL be unavailable to source/PR execution. The initial
parallel upload SHALL NOT select the production branch or grant release acceptance.

#### Scenario: An untrusted or unrelated run is offered for normal deployment

- **WHEN** a normal-edition run is not a completed successful main-push Documentation workflow
  from this repository, or the payload contains backend code or exceeds asset limits
- **THEN** publication rejects it before using Cloudflare credentials
- **AND** the current accepted publication and canonical URLs stay unchanged

#### Scenario: A standalone HTML artifact is downloaded

- **WHEN** a reader follows a normal edition's standalone HTML download link
- **THEN** Cloudflare serves the exact retained artifact bytes as an attachment
- **AND** no service scripts are injected and its offline contract remains valid

#### Scenario: A PR artifact is offered to the isolated preview publisher

- **WHEN** a completed Documentation PR run is associated through GitHub API
  metadata with exactly one open PR at its current source head
- **THEN** trusted default-branch code may upload its validated static preview
  to a separate preview project/origin and report a status for that exact head
- **AND** source execution never receives the publication environment or secret
- **AND** a stale, closed, ambiguous, unrelated or failed source cannot replace
  a successful preview or verified normal edition
- **AND** no PR code is checked out or executed by the credentialed publisher


#### Scenario: A trusted main build updates normal production after acceptance

- **GIVEN** parallel preview, edition/download and hosted recovery acceptance have passed
- **WHEN** the trusted publisher receives a successful main-push Documentation completion
- **THEN** it validates source API provenance, retained hashes and the current main SHA before upload
- **AND** only this automatic path selects normal production; manual rehearsals stay isolated
- **AND** both immutable and production-base URLs must match every retained edition and required download
- **AND** old GitHub Pages publication and immutable historical bytes remain available for recovery
