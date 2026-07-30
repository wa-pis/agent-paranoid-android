# Agent Orchestration Specification Delta

## ADDED Requirements

### Requirement: CLI Boundaries Preserve Public Contracts

The CLI SHALL separate interface parsing and presentation from application
dispatch without changing its public contract.

#### Scenario: A CLI boundary is refactored

- **GIVEN** the supported command surface and golden contract fixtures
- **WHEN** parser, dispatch, or presentation code moves behind an internal
  boundary
- **THEN** command names, options, aliases, defaults, help, and exit codes
  remain compatible
- **AND** versioned JSON results and errors retain their schemas
- **AND** human and JSON output remains bounded and contains no dataset rows
- **AND** `test_data_agent.cli:main` remains the package entry point
