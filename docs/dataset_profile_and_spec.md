# Dataset Profile And Spec Reference

English · [Русский](ru/dataset_profile_and_spec.md)

This document describes the two main artifacts in the domain-agnostic pipeline:

- `DatasetProfile` JSON
- `DatasetSpec` YAML

## DatasetProfile JSON

A profile is safe metadata and bounded evidence inferred from a source. It is
not a complete description of the domain and must not imply that unobserved
rules are known.

## Evidence Envelope

### Planned evidence envelope (not a serialized contract)

Relationships and constraints currently expose numeric `confidence` in [0, 1]
and `status`. The following richer provenance envelope is a design target;
it is not emitted by the current profile models and must not be supplied as
supported relationship/constraint fields. In particular, `confidence: medium`
below is illustrative, not a valid current numeric confidence value.
The separate relationship-discovery and validation-utility reports have their
own shipped schemas; they do not add this envelope to DatasetProfile.

Proposed shape for a future observed rule or relationship:

```yaml
origin: observed
status: candidate
confidence: medium
evidence:
  sample_size: 200
  sampling: bounded
  time_window:
    from: '2026-01-01'
    to: '2026-03-31'
  rows_checked: 200
  violations: 0
source_fingerprint: sha256:...
assumptions: []
```

`high` confidence means strong support from the recorded evidence, not a
universal truth claim. DDL or ORM declarations are `declared`; facts measured
from a sample or live profile are `observed`; deterministic or AI proposals
are `inferred` until a human accepts them. AI receives this context as
untrusted metadata and cannot promote a hypothesis into a generation rule.

If sample size, sampling method, coverage, or time window is unknown, that
uncertainty must remain visible in the profile and review record.

Top-level shape:

```json
{
  "source_type": "csv_folder",
  "entities": [],
  "relationships": [],
  "constraints": []
}
```

### Entity Profile

Each CSV file becomes an entity:

```json
{
  "name": "customers",
  "row_count": 3,
  "fields": [],
  "primary_key_candidates": ["customer_id"]
}
```

### Field Profile

Field profiles contain schema and safe distribution metadata:

```json
{
  "name": "email",
  "data_type": "string",
  "nullable": false,
  "null_ratio": 0.0,
  "unique_ratio": 1.0,
  "sensitive": true,
  "semantic_type": "email",
  "is_identifier": false,
  "distribution": {
    "kind": "masked_patterns",
    "patterns": [
      {"pattern": "email", "count": 3}
    ]
  }
}
```

Sensitive fields use masked patterns, not raw top values. By default,
low-cardinality non-sensitive fields preserve category frequency ranks with
synthetic labels such as `category_1`. Exact values appear only for a field in
the typed local category allowlist after bounded non-sensitive content checks;
that exception does not apply to source rows, provider payloads, or default MCP
responses.

Common distribution kinds:

- `synthetic_identifier`
- `masked_patterns`
- `numeric`
- `decimal_range`
- `numeric_shape`
- `boolean`
- `date_range`
- `datetime_range`
- `categorical`
- `string_pattern`

For `synthetic_identifier`, `pool_size` controls the synthetic key pool. The
optional `prefix` property is legacy metadata retained for compatibility, not a
generation control. String identifiers always use `synthetic_` followed by an
ASCII integer; a supplied prefix is never copied into generated values.
`masked_patterns` describes safe profiling evidence, not literal templates to
copy into output. Sensitive values use their synthetic semantic formatter.
Typed CSV bundles write exact DECIMAL values in plain fixed-point notation,
including very small values, so standalone validation can restore their declared
precision and scale without accepting exponent-form source strings.
Declared precision 38, scale 38 supports both signs, including the smallest
nonzero unit and the largest fractional magnitude. The optional minus sign is
not part of the declared digit precision; values outside that precision and
oversized text still fail the bounded exact parser.
CSV formatting checks the exact-decimal width and finiteness before expanding a
Decimal exponent; unbounded or non-finite direct values fail with a value-free
error.

### Large Input Behavior

CSV-folder profiles are built with a streaming schema/distribution pass. The
profiler can read large local files without keeping all source rows in memory.
Only bounded samples are kept for row-level relationship and constraint mining.

The optional profile cache stores the `DatasetProfile` wrapper only. It is keyed
by CSV file names, sizes, and modification times and must remain metadata-only:
no source rows, no real identifiers, and no raw PII.

Trino-derived profiles should follow the same artifact shape but should be
computed with pushdown aggregate queries in Trino. The local agent should keep
the compact profile JSON, not a downloaded copy of the source table.

### SQL Query Source Profile

The query-source workflow introduced in stable `1.5.0` profiles one reviewed
PostgreSQL or Trino query as a virtual entity. Its `source_type` is `postgres_query` or
`trino_query`. It is retained in stable `1.6.0`; see [release status](1.6.0-release-status.md). Since RC5, the profile
records a stable `source_fingerprint`,
`source_policy_version: "1.1"`, and ordinary safe entity metadata and aggregates.
This source-policy version is separate from DatasetSpec's schema version;
older query fingerprints remain historical evidence.

The fingerprint identifies the validated query shape without serializing the
SQL. Query text, literals, physical endpoints, backend messages, and query
result rows are excluded. Generation reads the reviewed inferred
`DatasetSpec`, never query rows.

### Relationship Profile

Relationships are inferred with confidence:

```json
{
  "parent_entity": "customers",
  "parent_field": "customer_id",
  "child_entity": "orders",
  "child_field": "customer_id",
  "relationship_type": "many_to_one",
  "confidence": 1.0,
  "status": "inferred"
}
```

### Constraint Profile

Constraints are also inferred with confidence and status:

```json
{
  "type": "formula",
  "entity": "orders",
  "fields": ["amount", "quantity", "unit_price"],
  "expression": "quantity * unit_price",
  "confidence": 1.0,
  "status": "inferred"
}
```

Supported constraint types:

- `formula`
- `temporal`
- `conditional_required`
- `aggregate_mapping`

## DatasetSpec YAML

The spec is the editable generation contract. It has the same core concepts as
the profile, but it is intended for generation.

Small example:

```yaml
schema_version: '1.1'
entities:
- name: customers
  row_count: 2
  primary_key: customer_id
  fields:
  - name: customer_id
    data_type: integer
    is_identifier: true
    distribution: {kind: synthetic_identifier}
- name: orders
  row_count: 3
  primary_key: order_id
  fields:
  - name: order_id
    data_type: integer
    is_identifier: true
    distribution: {kind: synthetic_identifier}
  - name: customer_id
    data_type: integer
    is_identifier: true
    distribution: {kind: synthetic_identifier}
  - name: quantity
    data_type: integer
    distribution: {kind: numeric, min_value: 1, max_value: 4}
  - name: unit_price
    data_type: decimal
    distribution: {kind: decimal_range, precision: 4, scale: 2, min: '1.00', max: '5.00'}
  - name: amount
    data_type: decimal
    distribution: {kind: decimal_range, precision: 5, scale: 2, min: '0.00', max: '20.00'}

relationships:
- parent_entity: customers
  parent_field: customer_id
  child_entity: orders
  child_field: customer_id
  relationship_type: many_to_one
  confidence: 1.0
  status: inferred

constraints:
- type: formula
  entity: orders
  fields: [amount, quantity, unit_price]
  expression: quantity * unit_price
  confidence: 1.0
  status: inferred

generation_settings:
  seed: 12345
  output_format: json
```

`schema_version` is the serialized contract version and is independent from the
Python package version. New specifications default to `1.1`; exact DECIMAL
fields require it. Both supported versions validate unique entity/field names
and check that relationships, constraints, primary keys, and scoped privacy
rules refer to fields that exist. Older serialized specs without the key load
as `1.0` for backward compatibility.

Business rules can be embedded as `business_rules` in the reviewed spec or
supplied as a reviewed YAML/JSON rule file. Generation and validation settings
travel with the same spec across sources and output formats. See the
[source/output contract](reference/source-output-matrix.md) and
[business-rule workflow](how-to/business-rules.md).

## What You Can Edit

Useful manual edits:

- Change `row_count` per entity.
- Remove an inferred relationship if it is wrong.
- Remove or edit a constraint if confidence is low.
- Change categorical counts to steer scenario frequency.
- Mark a field as `sensitive: true` if unsure.
- Set `nullable` and `null_ratio` to shape missingness.

Avoid putting real source examples into the spec. Keep it metadata-only.

## Validation Report

Validation returns sections:

```json
{
  "valid": true,
  "sections": [
    {"name": "schema", "passed": 1, "failed": 0, "errors": []},
    {"name": "relationships", "passed": 1, "failed": 0, "errors": []},
    {"name": "constraints", "passed": 1, "failed": 0, "errors": []}
  ]
}
```

If `valid` is false, inspect the section errors first. They tell you whether the
problem is basic schema shape, relationship integrity, or constraint
reconciliation.
