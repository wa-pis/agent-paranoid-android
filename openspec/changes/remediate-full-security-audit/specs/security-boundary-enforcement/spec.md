## ADDED Requirements

### Requirement: Sensitive Evidence Is Preserved Across Boundaries
Profiling and advisor services SHALL enforce sensitivity using source lineage and canonical content before retaining statistics, categories or sending provider requests. Local category opt-in SHALL authorize only bounded non-sensitive local enum evidence and SHALL NOT authorize external disclosure.

#### Scenario: Sensitive SQL alias
- **WHEN** a sensitive physical numeric column is aliased to a harmless output name with local-category opt-in
- **THEN** profiling rejects raw category preservation independent of alias

#### Scenario: Sensitive Trino residual
- **WHEN** a rule profile uses a sensitive target or expression/value operand
- **THEN** exact sensitive residual metrics are rejected or suppressed before disclosure

#### Scenario: Canonical numeric identifier
- **WHEN** folder CSV uses exponent notation for a recognizable numeric identifier
- **THEN** no exact identifier extrema or percentiles enter profile/cache artifacts

#### Scenario: Local category reaches provider
- **WHEN** OpenAI advice is requested for locally preserved categories
- **THEN** provider-bound profile/spec/predicates use field-scoped synthetic labels and no original category literal

### Requirement: Cache Reuse Preserves Current Authorization
Profile cache reuse SHALL be bound to the current local-category authorization and SHALL invalidate stale entries when policy cannot be established.

#### Scenario: Revoked category permission
- **WHEN** a prior allowed-category cache is reused without that permission
- **THEN** original category literals and predicates are not returned

### Requirement: Resource Checks Precede Materialization And Publication
Shared services SHALL enforce effective resource limits before dangerous formula operations, decoded dataset retention, audit record parsing and trusted profile publication.

#### Scenario: Formula sequence multiplication
- **WHEN** a short formula requests an excessive sequence or numeric result
- **THEN** evaluation fails within configured work bounds before allocation

#### Scenario: Parquet expansion
- **WHEN** dictionary-encoded data exceeds decoded-byte or cumulative dataset-cell limits
- **THEN** validation rejects before unbounded Python-list materialization

#### Scenario: Expired CSV invocation
- **WHEN** a CSV profiling invocation deadline expires during work
- **THEN** the service fails and publishes no trusted partial profile

#### Scenario: Oversized audit record
- **WHEN** an audit record exceeds its byte limit
- **THEN** the verifier rejects after a bounded read before JSON/HMAC processing

### Requirement: RC Follows Completed Remediation And Fresh Review
An RC SHALL be published only after all validated findings are fixed, the complete final SHA passes fresh full security review and required tests, and original transformation acceptance plus release gates are satisfied.

#### Scenario: Fresh review finds a defect
- **WHEN** fresh full review confirms a security defect
- **THEN** automation returns to remediation and does not publish RC

#### Scenario: Clean review and release gates
- **WHEN** the exact release SHA has clean complete review and all required release/approval/signature/artifact gates pass
- **THEN** automation may publish the unused 1.6.0 RC and verify its public artifacts without publishing stable
