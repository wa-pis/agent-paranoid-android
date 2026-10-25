## ADDED Requirements

### Requirement: RC3 feedback contract
Relationship validation SHALL report zero checked and passed links when none are declared. It SHALL report per-link resolution and cardinality without key values. Active links SHALL have matching field types and a unique binding per child field.

#### Scenario: Deterministic enforcement
- **WHEN** the corresponding CLI or direct service is invoked
- **THEN** the contract is enforced before publication and tested with fictional inputs

### Requirement: Conservative inferred field bindings
CSV inference SHALL require matching descriptive identifier names and field
types. Generic keys and multiple candidate parent domains SHALL require explicit
reviewed declarations. Old cached inferences SHALL be invalidated.

#### Scenario: Unrelated numeric domains overlap
- **GIVEN** customer_id and product_id contain the same fictional integers
- **WHEN** folder profiling runs
- **THEN** no relationship is inferred between those fields
