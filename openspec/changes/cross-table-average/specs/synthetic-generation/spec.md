# Synthetic Generation Specification Delta

## ADDED Requirements

### Requirement: Cross-Table Average Reconciliation

Aggregate mappings SHALL support deterministic average reconciliation across
a declared parent-child relationship.

#### Scenario: Child values include nulls

- **GIVEN** an average mapping from a parent field to a numeric child field
- **WHEN** generated child rows contain numeric and null values
- **THEN** the parent field equals the average of non-null numeric values
- **AND** validation applies the same rule

#### Scenario: Trino average consistency is profiled

- **GIVEN** allowlisted parent and child tables
- **WHEN** average mapping profiling is requested
- **THEN** the server executes a fixed grouped `avg` query
- **AND** returns only aggregate consistency metadata
