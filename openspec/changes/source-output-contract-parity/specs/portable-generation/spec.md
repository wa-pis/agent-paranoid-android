## ADDED Requirements

### Requirement: Complete transition matrix
Every supported source SHALL normalize into safe evidence and a reviewed DatasetSpec
that can generate each supported CSV, JSON, Parquet and SQL output. Supported source
families SHALL be documented and tested explicitly, including database table/query
metadata and saved profiles. Database routes SHALL retain existing read-only,
allowlist and resource limits; tests SHALL use fictional data.

#### Scenario: Complete reviewed specification from any source
- WHEN a supported source is profiled and its complete specification is reviewed
- THEN field types, distributions, relationships, settings and business rules use
  the same generation engine for every output format.

### Requirement: Representation-independent validation
Generation options and rule meanings SHALL NOT depend on a source or an output
adapter. Saved output SHALL be revalidated without reassigning targets or silently
losing decimal precision, boolean/date types or null/text distinctions. Legacy
unmarked artifacts SHALL retain their documented interpretation.

#### Scenario: Typed conditions after reload
- WHEN CSV, JSON, Parquet or SQL represents the same logical dataset
- THEN boolean, date, decimal and null conditions produce the same rule results.

#### Scenario: SQL is data, not execution
- WHEN a generated SQL bundle is revalidated
- THEN only bounded generated INSERT data is decoded and no SQL is executed.

### Requirement: Complete profiles and negative artifacts
A multi-entity safe profile SHALL reach the same bundle engine as a reviewed spec.
All declared generation modes SHALL have common semantics. Controlled-invalid
artifacts SHALL preserve planned violations and evidence through typed output;
encoding failure SHALL NOT be reported as a successful generated dataset.

#### Scenario: Multi-entity profile to each format
- WHEN a reviewed profile contains related entities
- THEN its generation preserves the entities, relationships and validation evidence
  for every output format.
