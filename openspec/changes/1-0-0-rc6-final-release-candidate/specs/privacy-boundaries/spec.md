# RC6 Field And Destination Privacy Delta

## ADDED Requirements

### Requirement: Local Category Preservation Is Explicit And Field Scoped

Local profiling and deterministic generation MAY preserve source category
values only for a field explicitly allowlisted as a bounded, non-sensitive
business enum. The effective policy SHALL consider field classification and
destination independently. A default `internal` classification or failure to
detect PII SHALL NOT by itself authorize preservation.

#### Scenario: An allowlisted business enum is profiled locally

- **GIVEN** `orders.status` is explicitly allowlisted as a non-sensitive
  bounded enum
- **AND** its values contain no recognizable PII, secrets, identifiers, or
  free text
- **WHEN** a local profile and reviewed generation specification are built
- **THEN** bounded status values and counts may be preserved
- **AND** generated rows may use those reviewed business values

#### Scenario: An unknown categorical field is profiled

- **GIVEN** a string field is not explicitly allowlisted for local category
  preservation
- **WHEN** it is profiled
- **THEN** its source literals are replaced, masked, or suppressed
- **AND** low cardinality alone does not make the literals safe

#### Scenario: An allowlisted field contains unsafe content

- **GIVEN** a locally allowlisted field contains recognizable PII, a secret,
  identifier-like content, or free text
- **WHEN** profiling validates the effective policy
- **THEN** preservation fails closed or the values are transformed
- **AND** the allowlist cannot weaken content-based sensitive detection

### Requirement: External Provider Payloads Remain Source-Literal Free

Every categorical source literal crossing an external LLM or provider boundary
SHALL be replaced by a deterministic field-scoped label, even when the same
field is explicitly allowlisted for local preservation. Provider responses
SHALL be mapped and validated against the local reviewed field policy before
persistence.

#### Scenario: A preserved local enum is sent to an advisor

- **GIVEN** a reviewed local profile preserves `orders.status` values
- **WHEN** an advisor request is serialized for an external provider
- **THEN** the provider receives only field-scoped synthetic labels and counts
- **AND** no original status literal crosses the provider boundary
- **AND** accepted provider predicates are restored only inside the local,
  fingerprint-bound review workflow

### Requirement: Trino And MCP Category Disclosure Requires Two Allowlists

Trino and MCP surfaces MAY return bounded category aggregates only when both
the source table and the specific column are allowlisted and the field is
classified as non-sensitive. Sensitive, unknown, identifier-like, or free-text
categories SHALL be masked, replaced, or suppressed. Source rows remain
forbidden on default aggregate-only surfaces.

#### Scenario: A safe aggregate category is requested

- **GIVEN** a read-only Trino table and its `currency` column are allowlisted
- **AND** `currency` is classified as a bounded non-sensitive enum
- **WHEN** the aggregate profile is returned through MCP
- **THEN** bounded currency values and counts may be returned
- **AND** no source row or non-allowlisted column value is returned

#### Scenario: Only the table is allowlisted

- **GIVEN** a table is allowlisted but its categorical column is not
- **WHEN** the column is profiled through MCP
- **THEN** raw category literals are not returned
- **AND** the result contains only masked, synthetic, or suppressed metadata

### Requirement: Synthetic Labels Cannot Alias Source Values

Whenever policy requires category replacement, the sanitizer SHALL reserve
all original values and every generated label before selecting the next
field-scoped label. This collision rule applies to transformed fields; it SHALL
NOT be used as a reason to transform an explicitly allowlisted safe local enum.

#### Scenario: A transformed source value resembles a label

- **GIVEN** a non-allowlisted or provider-bound category equals `category_1`
- **WHEN** the sanitizer assigns deterministic labels
- **THEN** it selects a distinct label such as `category_1_1`
- **AND** the original value cannot survive by aliasing the generated label

