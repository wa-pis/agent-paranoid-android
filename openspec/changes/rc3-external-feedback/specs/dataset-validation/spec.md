## ADDED Requirements

### Requirement: RC3 feedback contract
Relationship validation SHALL report zero checked and passed links when none are declared. It SHALL report per-link resolution and cardinality without key values. Active links SHALL have matching field types and a unique binding per child field.

#### Scenario: Deterministic enforcement
- **WHEN** the corresponding CLI or direct service is invoked
- **THEN** the contract is enforced before publication and tested with fictional inputs
