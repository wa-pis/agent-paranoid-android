# Add Business Rules

Use structured YAML or JSON when generated rows must satisfy domain rules.
The deterministic rule engine applies and validates the rules; an LLM is not
the enforcement mechanism.

## Create A Rule File

The checked-in example at `examples/orders_rules.yaml` contains:

```yaml
field_rules:
  - table: orders
    field: status
    required: true
    allowed_values: [paid, cancelled]
  - table: orders
    field: amount
    required: true
    min_value: 0

row_rules:
  - type: temporal_ordering
    table: orders
    start_field: created_at
    end_field: fulfilled_at
    allow_equal: true

  - type: formula
    table: orders
    field: amount
    expression: quantity * unit_price
```

Rule references must match fields in the effective `DatasetSpec`. Unknown keys,
tables, fields, rule types, and formula syntax are rejected.

## Prepare A Reviewed Spec

```bash
test-data-agent profile-example tests/fixtures/example_dataset \
  --output out/rules/profile.json

test-data-agent infer-spec out/rules/profile.json \
  --count 25 \
  --output out/rules/dataset_spec.yaml
```

Review `out/rules/dataset_spec.yaml`, then generate with rules:

```bash
test-data-agent generate out/rules/dataset_spec.yaml \
  --seed 12345 \
  --format csv \
  --business-rules examples/orders_rules.yaml \
  --output out/rules/generated
```

Review:

```text
out/rules/generated/
  business_validation_report.json
  generation_manifest.json
  validation_report.json
```

The generation manifest records a normalized rule fingerprint, rule counts,
pass/fail counts, truncation status, and overall business validity.

## Supported Rule Categories

| Category | Use |
| --- | --- |
| Field rule | Required values, allowed values, numeric bounds |
| Conditional required | Require fields when a condition matches |
| Conditional allowed values | Restrict a field under a condition |
| Temporal ordering | Enforce start/end ordering |
| Formula | Calculate or validate bounded arithmetic |
| Foreign key | Preserve cross-table references |
| Aggregate formula | Validate an aggregate expectation |
| Scenario | Control weighted combinations of field values |

## Generate Controlled Invalid Cases

Use an explicit generation mode:

```bash
test-data-agent generate out/rules/dataset_spec.yaml \
  --count 100 \
  --seed 12345 \
  --format csv \
  --mode mixed \
  --invalid-ratio 0.02 \
  --business-rules examples/orders_rules.yaml \
  --output out/rules/mixed_cases
```

`mixed` introduces the requested share of invalid values.
`negative` intentionally makes generated values invalid. Keep these datasets
clearly separated from valid fixtures and review the validation report rather
than expecting it to pass.

## Safety Restrictions

Do not put real identifiers, emails, phone numbers, addresses, credentials,
tokens, or other production literals into rule files. Sensitive-looking
literals are rejected by CLI and MCP entry points.

Formula syntax is a bounded arithmetic subset, not Python or SQL. Rule payload
size, expression complexity, and estimated row/rule evaluations are limited.

See [Configuration](../reference/configuration.md) for adjustable limits.
