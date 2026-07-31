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
pass/fail counts, truncation status, overall business validity, and bounded
expected-versus-observed violation counts.

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

For tables with several field and row rules, selected rows are distributed
deterministically across required, allowed-value, numeric-bound, conditional,
temporal, and formula violations. Reusing the same seed, mode, ratio, and rule
file reproduces the same negative cases. Foreign-key violations use synthetic
missing parent keys without changing the parent table. Aggregate-formula
violations change only the configured concrete numeric field. Count-style
aggregate rules with `field: "*"` are validation-only because changing row
counts would also break the dataset shape.

The business validation report compares expected and observed violations per
rule. `unexpected_violation_count` identifies failures that were not selected
by controlled invalid generation; `missing_expected_violation_count` identifies
selected cases that validation did not observe. `expectations_met` is true only
when both counts are zero. These fields contain counts only, never generated
row values.

### Reproduce The Same Cases Through CLI And MCP

The checked-in `examples/negative_cases/` bundle fixes the spec, rule file,
seed (`1300`), mode (`mixed`), and invalid ratio (`0.5`). Run it through CLI:

```bash
test-data-agent generate examples/negative_cases/dataset_spec.yaml \
  --seed 1300 \
  --mode mixed \
  --invalid-ratio 0.5 \
  --format json \
  --business-rules examples/negative_cases/business_rules.yaml \
  --output out/negative-cli
```

The MCP equivalent uses the same files after copying the example bundle below
the configured generator workspace. The mode and invalid ratio are already
recorded in `dataset_spec.yaml`:

```json
{
  "name": "generate_dataset",
  "arguments": {
    "spec_path": "negative_cases/dataset_spec.yaml",
    "output_folder": "negative-mcp",
    "output_format": "json",
    "seed": 1300,
    "business_rules_path": "negative_cases/business_rules.yaml"
  }
}
```

Both paths produce identical synthetic row files and matching expected versus
observed violation counts. Use separate empty output folders when repeating the
example.

## Safety Restrictions

Do not put real identifiers, emails, phone numbers, addresses, credentials,
tokens, or other production literals into rule files. Sensitive-looking
literals are rejected by CLI and MCP entry points.

Formula syntax is a bounded arithmetic subset, not Python or SQL. Rule payload
size, expression complexity, and estimated row/rule evaluations are limited.

See [Configuration](../reference/configuration.md) for adjustable limits.
