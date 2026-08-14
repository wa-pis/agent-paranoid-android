# Operational Readiness Specification Delta

## Added Requirements

### Requirement: CLI Cancellation Is Actionable

The installed CLI SHALL convert cooperative user cancellation into a bounded
result after workflow cleanup.

#### Scenario: Ctrl+C interrupts generation

- **GIVEN** a staged or pre-publication operation
- **WHEN** the user sends SIGINT
- **THEN** the workflow removes catchable staging output
- **AND** the CLI exits with code `130`
- **AND** it prints no traceback unless debug mode is explicit
- **AND** it states that no successful bundle was published

### Requirement: Doctor Distinguishes Installation From Reachability

Doctor SHALL report installed capabilities without implying that external
configuration or reachability was tested.

#### Scenario: An optional extra is installed

- **GIVEN** the dependency imports and its local smoke passes
- **WHEN** doctor runs
- **THEN** its human and JSON status distinguishes installed/local-passed from
  configured or reachable
- **AND** network access is skipped unless a separately authorized live check
  exists

#### Scenario: An optional extra is missing

- **GIVEN** a required extra is not installed
- **WHEN** doctor runs
- **THEN** the result uses the missing-dependency category
- **AND** it includes a copy-ready versioned installation command
- **AND** no import traceback is displayed

### Requirement: Installed Optional Entry Points Fail Cleanly

Optional console entry points SHALL explain missing extras without exposing a
Python traceback.

#### Scenario: Base wheel invokes an MCP entry point

- **GIVEN** the base wheel without MCP or Trino dependencies
- **WHEN** a user invokes either optional MCP console script
- **THEN** stderr contains one concise versioned installation command
- **AND** the process exits unsuccessfully without a traceback
