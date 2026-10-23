## ADDED Requirements

### Requirement: Honest Bounded Numeric Shape Evidence

Numeric shape evidence SHALL preserve valid negative base-10 exponents and
distinguish unavailable distribution evidence from observed zero mass.

#### Scenario: All nonzero values have absolute value below one
- **WHEN** safe magnitude metadata is computed
- **THEN** negative exponents remain representable
- **AND** values below one are not discarded or rounded to unit magnitude

#### Scenario: Mixed scales cannot be represented by one maximum
- **WHEN** additional safe zero/subunit evidence is available
- **THEN** its denominator and uncertainty are explicit
- **AND** missing evidence is not interpreted as a measured zero ratio

### Requirement: Read-Only Profile Cost Improvements

Query cost optimization SHALL preserve allowlists, aggregate-only output and
all resource budgets without creating materialized or temporary database tables.

#### Scenario: A wide query profile exceeds a work budget
- **WHEN** profiling cannot finish within its declared budget
- **THEN** it fails without publishing a trusted partial profile
- **AND** it does not issue database writes as a workaround

### Requirement: Category Scope Preflight Before Row Aggregates

SQL query profiling SHALL validate requested local-category scope, lineage and
output type after no-row schema inspection and before row-count or column
aggregates. Query-builder category limits SHALL be positive integers and retain
their existing upper/result-row budget checks.

#### Scenario: A requested category does not match authorized output
- **WHEN** the requested entity or field is outside the exact authorized output
- **THEN** profiling rejects before fetching a row-count or column aggregate
- **AND** no trusted partial profile is published
