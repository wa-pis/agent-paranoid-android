# Operational Readiness Specification

## Purpose

Define bounded, synthetic, and externally independent release checks for
installed product behavior and failure recovery.

## Requirements

### Requirement: Representative Resource Regression Gate

The release process SHALL exercise bounded representative profiling,
multi-entity generation, and validation workloads without external services or
non-synthetic input.

#### Scenario: Representative work stays within budget

- **GIVEN** a locally created synthetic two-entity input
- **WHEN** the operational resource gate profiles, generates, and validates it
- **THEN** every phase reports elapsed time and peak traced allocations
- **AND** the generated dataset has the expected row counts and validates
- **AND** the release gate passes only when every phase stays within its ceiling

#### Scenario: A regression exceeds a ceiling

- **GIVEN** a measured phase exceeds its wall-time or allocation ceiling
- **WHEN** the budget is enforced
- **THEN** the check fails with the phase and exceeded ceiling
- **AND** no external service or production data is involved

### Requirement: Container Vulnerability Gate

CI SHALL scan every native published container target for known fixable High
and Critical vulnerabilities before publication.

#### Scenario: Image has no release-blocking finding

- **GIVEN** a locally built CLI, generator MCP, or Trino MCP image
- **WHEN** its hardened runtime check succeeds
- **THEN** the pinned scanner checks operating-system and language packages
- **AND** validation succeeds when no fixable High or Critical finding exists

#### Scenario: Image contains a release-blocking finding

- **GIVEN** a fixable High or Critical vulnerability in a built target
- **WHEN** container validation scans the image
- **THEN** the target-specific job fails before merge
- **AND** tagged publication remains blocked by the failed validation

### Requirement: Supported Python Wheel Matrix

CI SHALL build and install the base wheel on every supported Python minor
version without replacing the full optional-profile wheel gate.

#### Scenario: Supported wheel is healthy

- **GIVEN** a supported Python version from 3.11 through 3.14
- **WHEN** CI builds and installs the wheel into an isolated environment
- **THEN** installed identity, metadata, dependencies, and size are valid
- **AND** base doctor completes using only local temporary artifacts

#### Scenario: Compatibility regression occurs

- **GIVEN** a wheel cannot build, install, or run on a supported Python version
- **WHEN** the compatibility matrix executes
- **THEN** that interpreter-specific job fails before release
- **AND** the existing full optional-profile wheel check remains independent
