# Multi-Source Bundle Delta

## ADDED Requirements

### Requirement: Sources Have Stable Non-Secret Identities

Every configured source SHALL have a user-chosen stable alias and source kind.
Entity identity in a multi-source profile SHALL be source-qualified by alias,
schema, and table. Hostnames, DSNs, credentials, and mutable infrastructure
coordinates SHALL NOT be used as public identity.

#### Scenario: Two PostgreSQL hosts contain the same table name

- **GIVEN** sources `hr` and `payroll` both contain `public.employees`
- **WHEN** their profiles are normalized into one bundle
- **THEN** the entities have distinct canonical identities
  `hr.public.employees` and `payroll.public.employees`
- **AND** their relationship and generation references remain unambiguous

#### Scenario: Source identity is serialized

- **GIVEN** a source bundle is written as a profile or metadata artifact
- **WHEN** the artifact is inspected
- **THEN** it contains only stable alias, source kind, schema/table scope, and
  profile evidence
- **AND** it contains no host, DSN, credential, or backend connection detail

### Requirement: Bundle Budgets Are Shared And Non-Resettable

A source bundle SHALL enforce a maximum source count, table/column count,
statement count, wall-clock deadline, and optional cumulative estimated scan
budget across all nested source profilers. Per-source budgets MAY be stricter,
but helper calls SHALL NOT reset the bundle budget.

#### Scenario: Many sources exceed the bundle limit

- **GIVEN** each individual source remains within its local limits
- **WHEN** cumulative source work exceeds the bundle statement, column, scan,
  or deadline limit
- **THEN** the bundle fails closed before starting the next operation
- **AND** no helper can reset the consumed work

### Requirement: Cross-Source Relationships Are Explicit Hypotheses

Relationships between different source aliases SHALL be represented separately
from declared local foreign keys. They SHALL retain evidence, confidence, and
review status, and SHALL require human approval before entering the generation
spec. AI MAY rank or explain them but SHALL NOT approve them.

#### Scenario: Two sources have compatible employee identifiers

- **GIVEN** `hr.public.employees.employee_id` and
  `payroll.public.salary.employee_id` appear compatible
- **WHEN** the bundle creates a relationship candidate
- **THEN** it records a cross-source hypothesis with bounded evidence
- **AND** the relationship remains unapproved until a reviewer accepts it
- **AND** no source identifier values are sent to an AI provider

#### Scenario: A source fails during bundle profiling

- **GIVEN** one required source cannot be connected or profiled
- **WHEN** the bundle operation completes
- **THEN** it returns a bounded failure
- **AND** it does not publish or pass a partial bundle to generation
