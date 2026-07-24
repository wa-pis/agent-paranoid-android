# Synthetic Generation Specification Delta

## ADDED Requirements

### Requirement: DatasetSpec Version Compatibility

DatasetSpec readers SHALL accept only explicitly supported schema versions and
SHALL fail closed on unknown versions before generation or validation.

#### Scenario: Future schema is loaded

- **GIVEN** a DatasetSpec declares an unsupported `schema_version`
- **WHEN** any serialized adapter loads it
- **THEN** loading fails and lists supported versions

### Requirement: Optional Integration Packaging

The base package SHALL support CSV and JSON generation without installing
Parquet, MCP, SQL parser, or Trino dependencies.

#### Scenario: Minimal package is installed

- **GIVEN** only base dependencies are installed
- **WHEN** `test-data-agent doctor` runs
- **THEN** core checks and CSV smoke generation pass
- **AND** unavailable integrations are reported as optional
