# Synthetic Generation Delta

## Added Requirements

### Requirement: Controlled Cross-Table Negative Cases

Negative and mixed generation SHALL create deterministic, validator-observable
violations for supported cross-table business rules without modifying
unrelated parent or row values.

#### Scenario: Foreign key is selected

- **GIVEN** generated child rows satisfy a foreign-key rule
- **WHEN** a child row is selected for that negative case
- **THEN** its child key is replaced with a synthetic key absent from the
  generated parent keys
- **AND** parent rows remain unchanged
- **AND** foreign-key validation reports the violation

#### Scenario: Concrete aggregate field is selected

- **GIVEN** generated rows satisfy an aggregate-formula rule over a concrete
  numeric field
- **WHEN** a row is selected for that negative case
- **THEN** only that configured field is perturbed outside the rule tolerance
- **AND** aggregate validation reports the violation

#### Scenario: Count aggregate is configured

- **GIVEN** an aggregate-formula rule uses `field: "*"`
- **WHEN** controlled invalid cases are compiled
- **THEN** no automatic row-count mutation is created
- **AND** the rule remains available for validation
