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

### Requirement: Cooperative Cancellation Cleanup

Generation workflows SHALL remove their staging directory when cooperative
process cancellation interrupts staged writing or validation.

#### Scenario: Cancellation interrupts staged publication

- **GIVEN** folder, review, or single-entity generation has created a staging
  directory
- **WHEN** interactive cancellation interrupts writing or validation
- **THEN** the staging directory is removed
- **AND** the final destination and success metadata are not published
- **AND** the cancellation is re-raised to the caller

#### Scenario: The process cannot run cleanup

- **GIVEN** hard termination or host failure prevents in-process cleanup
- **WHEN** the process stops
- **THEN** cooperative cleanup is not claimed
- **AND** abandoned-staging recovery remains a separate operational concern

### Requirement: ARM64 Container Validation

CI SHALL build and execute every published container target for Linux ARM64
before multi-platform publication.

#### Scenario: ARM64 target is healthy

- **GIVEN** a CLI, generator MCP, or Trino MCP container target
- **WHEN** pull-request CI builds and loads it for Linux ARM64
- **THEN** the image reports the ARM64 architecture
- **AND** the existing non-root, read-only, no-capability health contract passes
- **AND** no production service or credential is required

#### Scenario: ARM64 target regresses

- **GIVEN** a target cannot build or execute safely on ARM64
- **WHEN** validation runs through registered emulation
- **THEN** the target-specific job fails before merge
- **AND** tagged multi-platform publication depends on the failed validation

### Requirement: Dependency License Gate

CI SHALL verify the declared license of every package installed in locked
application, optional, development, and documentation environments.

#### Scenario: Dependency license is approved

- **GIVEN** an installed dependency declares an allowlisted SPDX expression,
  legacy license value, or OSI classifier
- **WHEN** the license gate evaluates the locked environment
- **THEN** the package and resolved declaration are reported
- **AND** validation continues without an external license service

#### Scenario: Dependency license is not approved

- **GIVEN** a dependency has unknown, proprietary, or non-allowlisted metadata
- **WHEN** the license gate evaluates the locked environment
- **THEN** validation fails with the package name and declaration
- **AND** release checks cannot silently bypass the policy

### Requirement: Mid-write Disk Exhaustion Cleanup

Staged generation workflows SHALL fail closed when the target filesystem
reports disk exhaustion after partial output has been written.

#### Scenario: A staged write runs out of space

- **GIVEN** folder, review, or single-entity generation has written a partial
  staged file
- **WHEN** the filesystem reports `ENOSPC`
- **THEN** the staging directory is removed
- **AND** the final destination and success metadata are not published
- **AND** the operating-system error is propagated to the caller

#### Scenario: The user retries after freeing space

- **GIVEN** a failed run left no published bundle
- **WHEN** sufficient capacity is restored
- **THEN** the user can retry from the same reviewed spec and seed
- **AND** no partial file is treated as successful input

### Requirement: MCP Doctor Capability Smoke

Doctor SHALL verify the required MCP capability by constructing the real local
generator transport and registering a tool through the installed SDK.

#### Scenario: MCP capability is healthy

- **GIVEN** the MCP extra is required and importable
- **WHEN** doctor runs without `--skip-smoke`
- **THEN** it constructs the generator `FastMCP` transport
- **AND** an audited local probe appears in the public tool listing
- **AND** no server, port, client, tool invocation, or external service is used

#### Scenario: MCP capability fails

- **GIVEN** transport construction or tool registration raises an exception
- **WHEN** doctor reports the failure
- **THEN** doctor exits unsuccessfully with exact extra reinstall guidance
- **AND** exception text, audit secrets, and internal details are not exposed

### Requirement: Parquet Doctor Capability Smoke

Doctor SHALL verify the required Parquet capability with local artifact
generation and read-back, not importability alone.

#### Scenario: Parquet capability is healthy

- **GIVEN** the Parquet extra is required and importable
- **WHEN** doctor runs without `--skip-smoke`
- **THEN** it generates and reads a temporary two-entity Parquet bundle
- **AND** row counts, output format, and manifest safety flags are valid
- **AND** no external service or repository fixture is required

#### Scenario: Parquet capability fails

- **GIVEN** Parquet generation or read-back raises an exception
- **WHEN** doctor reports the failure
- **THEN** doctor exits unsuccessfully with exact extra reinstall guidance
- **AND** exception text, temporary paths, and sensitive values are not exposed

### Requirement: Provider Doctor Capability Smoke

Doctor SHALL verify the required provider capability with local SDK and
adapter construction, not importability alone.

#### Scenario: Provider capability is healthy

- **GIVEN** the OpenAI extra is required and importable
- **WHEN** doctor runs without `--skip-smoke`
- **THEN** it constructs and closes an SDK client with a non-secret placeholder
- **AND** it verifies structured response parsing and advisor construction
- **AND** no credentials, provider request, or external service is required

#### Scenario: Provider capability fails

- **GIVEN** SDK or adapter construction raises an exception
- **WHEN** doctor reports the failure
- **THEN** doctor exits unsuccessfully with exact extra reinstall guidance
- **AND** exception text, credentials, and sensitive data are not exposed

### Requirement: Trino Doctor Capability Smoke

Doctor SHALL verify the required Trino capability with local safe-query
validation and client construction, not importability alone.

#### Scenario: Trino capability is healthy

- **GIVEN** the Trino extra is required and importable
- **WHEN** doctor runs without `--skip-smoke`
- **THEN** it validates a bounded allowlisted query with no sensitive fields
- **AND** it constructs and closes a DBAPI client without opening a cursor
- **AND** no credentials, external service, or repository fixture is required

#### Scenario: Trino capability fails

- **GIVEN** safe-query validation or client construction raises an exception
- **WHEN** doctor reports the failure
- **THEN** doctor exits unsuccessfully with exact extra reinstall guidance
- **AND** exception text, configuration values, and sensitive data are not exposed

### Requirement: Interrupted Publication Rollback

Generation workflows SHALL roll back output when publication is interrupted
after commit has begun but before success returns to the caller.

#### Scenario: Folder rename completes before interruption

- **GIVEN** a folder or review staging directory has been atomically renamed
- **WHEN** publication is interrupted before success returns
- **THEN** the renamed destination is removed
- **AND** no manifest or output is reported as successful

#### Scenario: Single-entity commit is partially complete

- **GIVEN** some staged files have moved into an existing output directory
- **WHEN** publication is interrupted
- **THEN** new files are removed and replaced files are restored
- **AND** unrelated files remain unchanged
- **AND** the original interruption error is propagated

### Requirement: Auditable Security Review Disposition

Before operational readiness is declared, maintainers SHALL record the result
and disposition of dependency, license, source, secret, container, and
supply-chain checks against an identified commit.

#### Scenario: Release-blocking finding exists

- **GIVEN** a Critical or High runtime, code, dependency, secret, license, or
  fixable container finding
- **WHEN** the readiness review is performed
- **THEN** the review remains incomplete until the finding is fixed
- **AND** the release candidate cannot treat an undocumented exception as safe

#### Scenario: Governance or maturity finding is accepted or deferred

- **GIVEN** a scanner finding does not identify an exploitable product defect
- **WHEN** maintainers determine it is not release-blocking
- **THEN** the review records its rationale, mitigation, owner, and revisit
  date and trigger
- **AND** the automated scanner remains enabled to detect changed conditions

### Requirement: Staged Timeout Cleanup

Every staged generation output shape SHALL fail closed when its deterministic
generation deadline expires before publication.

#### Scenario: A workflow deadline expires after staging

- **GIVEN** folder, review, or single-entity generation has staged output
- **WHEN** a workflow boundary detects the expired generation deadline
- **THEN** the entire staging directory is removed
- **AND** the final destination and success metadata are not published
- **AND** the timeout error is propagated to the caller

#### Scenario: A user retries a timed-out run

- **GIVEN** a timeout left no published partial bundle
- **WHEN** the user retries with an appropriate deadline
- **THEN** the same reviewed spec and seed produce deterministic output
- **AND** the abandoned attempt is not treated as successful
