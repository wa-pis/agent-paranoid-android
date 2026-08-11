# Selective Source Value Preservation Delta

## ADDED Requirements

### Requirement: As-Is Preservation Is Explicit, Field Scoped, And Default-Off

Source values SHALL be preserved without masking or replacement only for a
field present in the typed local preservation allowlist. The default for every
other field SHALL remain the existing mask, suppress, or synthetic replacement
policy. The system SHALL NOT expose a global masking bypass.

#### Scenario: A reviewed business enum is allowlisted

- **GIVEN** `orders.status` is explicitly allowlisted for local preservation
- **AND** the field is reviewed as a bounded non-sensitive business enum
- **WHEN** its local profile and generation specification are built
- **THEN** its exact approved values and bounded counts are retained
- **AND** generated records may use those values as-is

#### Scenario: Preservation is not requested

- **GIVEN** a field is absent from the typed local preservation allowlist
- **WHEN** it is profiled and used for generation
- **THEN** no source literal is preserved because of type or low cardinality
- **AND** existing masking, suppression, or synthetic replacement applies

### Requirement: Authorization Does Not Override Sensitive-Content Checks

An allowlisted field SHALL pass explicit non-sensitive classification,
cardinality, value-length, and content checks before any exact value is
retained. PII, secrets, credentials, tokens, identifiers, quasi-identifiers,
and free text SHALL NOT be eligible for as-is preservation. A failed requested
preservation SHALL fail closed without publishing a partial trusted profile.

#### Scenario: An allowlisted field contains unsafe content

- **GIVEN** an allowlisted field contains recognizable PII, a secret,
  identifier-like values, quasi-identifiers, or free text
- **WHEN** the profiler validates the preservation request
- **THEN** the request fails closed
- **AND** no exact value is published in a profile, specification, artifact,
  log, error, MCP response, or provider payload

#### Scenario: An allowlisted domain exceeds its budget

- **GIVEN** an allowlisted field exceeds its cardinality or value-length limit
- **WHEN** profiling reaches the configured limit
- **THEN** preservation is rejected before a trusted profile is published
- **AND** the caller cannot raise or reset the limit from nested helper code

### Requirement: PostgreSQL Preservation Uses Qualified Column Scope

For PostgreSQL sources, preservation authorization SHALL resolve through the
stable source-qualified entity identity and field name to exactly one
allowlisted source, schema, table, and column. A schema or table allowlist alone
SHALL NOT authorize exact category values.

#### Scenario: Two PostgreSQL sources contain the same field name

- **GIVEN** `hr.public.employees.status` and
  `payroll.public.employees.status` both exist
- **AND** only the HR field is explicitly authorized
- **WHEN** the bundle is profiled
- **THEN** only approved bounded HR status values may be retained
- **AND** payroll status values remain masked, suppressed, or replaced

### Requirement: Preserved Values Remain Local To Approved Destinations

Approved exact values MAY appear in local profiles, reviewed specifications,
deterministically generated records, and local SQL export. External LLM or
provider payloads SHALL replace them with deterministic field-scoped labels.
Default MCP responses, logs, public errors, and source-bundle metadata SHALL
remain source-literal free.

#### Scenario: An approved value reaches local SQL export

- **GIVEN** a reviewed generation specification preserves the approved values
  `pending` and `complete` for `orders.status`
- **WHEN** deterministic rows are generated and exported locally as SQL
- **THEN** generated INSERT statements may contain `pending` and `complete`
- **AND** the output is derived from generated records rather than source rows

#### Scenario: The same field reaches an external advisor

- **GIVEN** a local profile retains approved exact status values
- **WHEN** an advisor request is serialized for an external provider
- **THEN** the provider receives deterministic labels and bounded counts only
- **AND** neither exact status value crosses the provider boundary

### Requirement: Preservation Does Not Copy Source Rows

As-is preservation SHALL retain only an approved bounded value domain and its
safe aggregate evidence. It SHALL NOT retain row order, complete source rows,
or a row-reconstruction mapping. Generated output SHALL continue to pass the
existing no-copy and privacy validation boundaries.

#### Scenario: Source rows combine several preserved fields

- **GIVEN** two approved fields retain bounded value domains and distributions
- **WHEN** deterministic generation combines their values
- **THEN** generation follows the reviewed specification and seed
- **AND** it does not replay complete source rows or source row order
