# Release Supply Chain Delta: stable-release-classifier

## Added Requirements

### Requirement: Distribution Maturity Matches Release Phase

Built Python distributions SHALL declare a development-status classifier that
matches whether the package version is a prerelease or stable release.

#### Scenario: A release candidate is built

- **GIVEN** the package version is a PEP 440 prerelease
- **WHEN** wheel and source-distribution metadata are validated
- **THEN** both declare `Development Status :: 4 - Beta`

#### Scenario: A stable release is built

- **GIVEN** the package version is not a PEP 440 prerelease
- **WHEN** wheel and source-distribution metadata are validated
- **THEN** both declare `Development Status :: 5 - Production/Stable`
- **AND** publication fails if either artifact retains the Beta classifier
