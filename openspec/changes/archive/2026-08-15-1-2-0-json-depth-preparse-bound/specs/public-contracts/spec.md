# Public Contracts Specification Delta

## Added Requirements

### Requirement: Bounded Local JSON Import

Local JSON dataset, profile/spec, and profile-cache importers SHALL enforce a
finite structural-depth budget before application JSON/Pydantic materialization.

#### Scenario: JSON structure is within budget

- **GIVEN** a byte-bounded local JSON document
- **WHEN** its object and array nesting is within the configured depth budget
- **THEN** the application may parse and validate it
- **AND** structural characters inside JSON strings do not count as nesting

#### Scenario: JSON structure exceeds the budget

- **GIVEN** a local JSON document whose structure exceeds the configured depth
  budget
- **WHEN** a dataset, profile/spec, or profile-cache importer receives it
- **THEN** the document is rejected before application JSON/Pydantic parsing
- **AND** no partial dataset, profile, spec, or cache value is returned
