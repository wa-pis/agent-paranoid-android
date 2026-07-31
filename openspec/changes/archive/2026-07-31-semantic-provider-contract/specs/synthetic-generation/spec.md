# Synthetic Generation Specification Delta

## ADDED Requirements

### Requirement: Semantic Providers Cannot Bypass Privacy Validation

The Python generation API SHALL accept optional semantic value providers only
through a row-free, deterministic contract.

#### Scenario: A provider supplies an organization-specific value

- **GIVEN** a non-sensitive semantic field and a configured provider
- **WHEN** the provider returns a candidate with the declared field type
- **THEN** the candidate is used only after core privacy validation succeeds
- **AND** the provider receives no source rows, samples, or credentials

#### Scenario: A provider targets sensitive data

- **GIVEN** an identifier or conservatively sensitive field
- **WHEN** generation runs with a semantic provider
- **THEN** the provider is not called for that field
- **AND** core synthetic generation remains authoritative

#### Scenario: A provider returns unsafe output

- **GIVEN** a semantic provider returns recognizable PII, a secret, an invalid
  type, or an oversized value
- **WHEN** core generation validates the candidate
- **THEN** generation fails before the value is returned
