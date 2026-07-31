# Synthetic Generation Delta

## Added Requirements

### Requirement: Reviewable Negative Validation Artifacts

Controlled invalid generation SHALL record bounded expected and observed
business-rule violation counts without including generated row values.

#### Scenario: Selected violations are observed

- **GIVEN** controlled invalid generation selects one or more rule violations
- **WHEN** business validation runs
- **THEN** the report records expected and observed counts per rule
- **AND** `expectations_met` is true when no expected violation is missing and
  no unexpected violation is observed

#### Scenario: An unplanned failure is observed

- **GIVEN** validation observes more failures than generation selected
- **WHEN** the business-validation report is produced
- **THEN** the excess is counted as unexpected
- **AND** no generated row values are added to the manifest summary
