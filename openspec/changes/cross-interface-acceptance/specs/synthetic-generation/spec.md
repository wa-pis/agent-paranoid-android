## MODIFIED Requirements

### Requirement: Reviewable Negative Validation Artifacts

Controlled invalid generation SHALL record bounded expected and observed
business-rule violation counts without including generated row values. Expected
counts SHALL include collateral rule failures caused by selected mutations.
Injection SHALL refuse an invalid business-rule baseline before mutation,
without treating pre-existing failures as authorized invalid cases.
Accounting SHALL retain shared operation and deadline budgets.

#### Scenario: Selected violations are observed

- **GIVEN** controlled invalid generation selects one or more rule violations
- **WHEN** business validation runs
- **THEN** the report records expected and observed counts per rule
- **AND** `expectations_met` is true when no expected violation is missing and
  no unexpected violation is observed

#### Scenario: Selected mutation breaks overlapping rules

- **GIVEN** a selected mutation breaks a required rule and a conditional-required
  rule, or a row formula and an aggregate formula
- **WHEN** before/after audits establish newly caused failures
- **THEN** every caused failure is included in the expected counts
- **AND** the selected rule is not counted twice for the same mutation

#### Scenario: An unplanned failure is observed

- **GIVEN** validation observes more failures than generation selected or caused
- **WHEN** the business-validation report is produced
- **THEN** the excess is counted as unexpected
- **AND** no generated row values are added to the manifest summary

#### Scenario: A baseline is already invalid

- **GIVEN** one or more business rules fail before controlled invalid injection
- **WHEN** negative or mixed injection starts
- **THEN** it refuses the invalid baseline before mutation with a value-free error
- **AND** a selected mutation cannot authorize or silently repair that failure

#### Scenario: A selected mutation does not produce its violation

- **GIVEN** a selected invalid mutation leaves its selected rule satisfied
- **WHEN** final validation compares planned and observed counts
- **THEN** the missing expected violation remains visible
- **AND** collateral accounting cannot silently mark the run accepted
