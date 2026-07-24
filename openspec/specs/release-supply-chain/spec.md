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
