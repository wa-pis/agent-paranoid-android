# Dataset Profile And Spec Reference

This document describes the two main artifacts in the domain-agnostic pipeline:

- `DatasetProfile` JSON
- `DatasetSpec` YAML

## DatasetProfile JSON

A profile is safe metadata inferred from an example dataset.

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

Sensitive fields use masked patterns, not raw top values.

Common distribution kinds:

- `synthetic_identifier`
- `masked_patterns`
- `numeric`
- `boolean`
- `date_range`
- `datetime_range`
- `categorical`
- `string_pattern`

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
entities:
- name: customers
  row_count: 1000
  fields:
  - name: customer_id
    data_type: string
    nullable: false
    null_ratio: 0.0
    sensitive: false
    semantic_type: null
    is_identifier: true
    distribution:
      kind: synthetic_identifier
  - name: email
    data_type: string
    nullable: false
    null_ratio: 0.0
    sensitive: true
    semantic_type: email
    is_identifier: false
    distribution:
      kind: masked_patterns
      patterns:
      - pattern: email
        count: 3
  primary_key: customer_id

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
```

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
