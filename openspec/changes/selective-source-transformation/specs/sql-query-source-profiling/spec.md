## ADDED Requirements

### Requirement: Bounded Single-Table Aggregate Queries

SQL source policy 1.1 SHALL accept aliased SUM, COUNT, MIN, MAX and AVG over
one authorized physical table, optionally grouped by explicit authorized source
columns. Other projections SHALL be grouping keys. COUNT(*) SHALL count rows
without authorizing projection-star disclosure. Nested/wrapped aggregates,
DISTINCT aggregates, HAVING, grouping expressions/ordinals, ROLLUP and grouping
sets SHALL remain unsupported. Sensitive-name source references in grouped or
aggregate queries SHALL fail closed regardless of output aliases. All existing
SQL exclusions, authorization, resource budgets and source-free wrappers SHALL
remain enforced. Aggregate profiles SHALL be marked unsupported for automatic
dependency-preserving generation inference, including COUNT(*) queries.

#### Scenario: Grouped count is profiled without source rows

- **GIVEN** an authorized single-table query selecting a grouping column and
  aliased COUNT(*) within all existing budgets
- **WHEN** query-source profiling runs
- **THEN** only trusted schema and aggregate wrappers execute and the profile
  contains metadata, no query rows or SQL literals
- **AND** automatic specification inference fails explicitly

#### Scenario: Aggregate query does not bypass policy

- **GIVEN** a grouped query referencing an unauthorized or sensitive-name column,
  an unsupported aggregate shape, or work exceeding an existing budget
- **WHEN** query-source profiling is requested
- **THEN** the operation fails closed without a successful partial profile or
  source-bearing error
