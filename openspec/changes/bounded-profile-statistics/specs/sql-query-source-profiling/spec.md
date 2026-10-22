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
