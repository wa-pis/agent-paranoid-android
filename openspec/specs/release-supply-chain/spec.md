# Release Supply Chain Specification

## Purpose

Define how built Python distributions are verified and published through
short-lived identities without exposing long-lived registry credentials.

## Requirements

### Requirement: Tokenless PyPI Publication

The project SHALL publish Python distributions through PyPI Trusted Publishing
without a stored PyPI password or API token.

#### Scenario: A GitHub Release is published

- **GIVEN** a published release with a wheel and source distribution
- **WHEN** the PyPI workflow runs
- **THEN** it obtains a short-lived token through GitHub OIDC
- **AND** publication runs in the scoped `pypi` environment

### Requirement: Published Distribution Identity

The PyPI workflow SHALL publish only the distributions already attached to the
selected published GitHub Release.

#### Scenario: Release artifacts match the selected tag

- **GIVEN** exactly one wheel and one source distribution
- **WHEN** their provenance and embedded metadata are validated
- **THEN** both were attested by `release.yml` from the selected tag
- **AND** both names equal `agent-paranoid-android`
- **AND** both versions equal the selected release tag

#### Scenario: Release artifacts are unsafe or ambiguous

- **GIVEN** missing, extra, non-regular, oversized, malformed, or mismatched
  distribution files
- **WHEN** pre-publication validation runs
- **THEN** the workflow fails before requesting PyPI publication

### Requirement: Signed OCI Publication

The project SHALL publish container images only from matching version tags and
SHALL authenticate image manifests without stored signing keys.

#### Scenario: Release images are published

- **GIVEN** a version tag that matches the package version
- **WHEN** the container workflow pushes its three target images
- **THEN** the manifest digests receive SBOM and provenance attestations
- **AND** Cosign signs each digest with GitHub OIDC
- **AND** pull-request builds never receive package write permission

### Requirement: Path-Aware Heavy Verification

Heavy Python, container, and security verification SHALL run for code,
dependency, workflow, configuration, example, release, and unknown changes.
Documentation-only pull requests SHALL retain a strict documentation gate,
while CodeQL SHALL analyze every commit that reaches the default branch.

#### Scenario: A documentation-only change is proposed

- **GIVEN** every changed path is Markdown, `docs/**`, `openspec/**`, or
  `mkdocs.yml`
- **WHEN** pull-request workflows classify the change
- **THEN** the strict documentation workflow runs
- **AND** heavy Python, container, and security jobs are skipped successfully

#### Scenario: A documentation-only change reaches the default branch

- **GIVEN** a documentation-only pull request was accepted
- **WHEN** its commit reaches the default branch
- **THEN** CodeQL analyzes that default-branch commit
- **AND** other heavy Python, container, and security jobs remain skipped

#### Scenario: Classification is uncertain

- **GIVEN** an empty change set, invalid commit identity, release tag, scheduled
  run, workflow dispatch, or unrecognized path
- **WHEN** workflow scope is classified
- **THEN** heavy verification runs fail closed
