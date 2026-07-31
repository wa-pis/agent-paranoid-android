# Public Contracts Delta

## Added Requirements

### Requirement: Versioned Golden Contract Catalog

Every golden public JSON and MCP fixture SHALL have an explicit contract
version and compatibility rule.

#### Scenario: A fixture is added

- **GIVEN** a new public contract fixture is checked in
- **WHEN** contract tests run
- **THEN** the fixture must be registered in the versioned catalog
- **AND** its change rule must be `additive_only` or `schema_versioned`

#### Scenario: A contract changes

- **GIVEN** a golden fixture differs from its reviewed baseline
- **WHEN** the change is assessed
- **THEN** additive-only changes preserve all existing valid consumers
- **AND** breaking schema-versioned changes advance the serialized version and
  provide migration guidance
