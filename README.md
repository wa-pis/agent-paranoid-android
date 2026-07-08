# Test Data Agent

Safe, deterministic synthetic test data generation for database and CSV-driven
test datasets.

The project is intentionally conservative: it profiles schemas and aggregate
metadata, detects likely sensitive fields, builds generation specs, generates
synthetic rows from an explicit seed, validates the result, and exports data in
common formats. It never copies source rows into generated output.

## What It Does

- Inspects Trino-accessible schemas through a small read-only MCP server.
- Profiles CSV files into safe reusable metadata.
- Infers PII and secret-like fields from names, semantic hints, and values.
- Builds Pydantic generation specifications from explicit JSON, Trino profiles,
  or CSV profiles.
- Generates reproducible synthetic rows with Faker and deterministic random
  generation.
- Supports controlled invalid records for negative and mixed datasets.
- Validates generated rows against the requested schema.
- Exports JSON, CSV, and Parquet.
- Defines executable business rules for field, row, cross-table, formula,
  temporal, foreign-key, aggregate, and scenario validation.

## Safety Model

Generated data must be synthetic. Source data is used only for structure and
safe metadata:

- column names
- inferred data types
- null ratios
- approximate distinct counts
- enum-like distributions for non-sensitive fields
- numeric ranges and percentiles
- date and timestamp ranges
- masked sensitive patterns

The project treats likely PII as sensitive by default. Sensitive CSV columns do
not emit raw top values. Trino row-returning queries must be read-only, bounded
with `LIMIT`, and cannot use unrestricted `SELECT *`.

Forbidden behavior includes copying production rows, exposing raw PII, exporting
real rows, running DDL/DML SQL, and creating unrestricted SQL tools.

## Install

Use Python 3.11 or newer.

```bash
python -m pip install -e ".[dev]"
```

Run the test suite:

```bash
pytest
```

## Quick Start

Create a generation spec:

```json
{
  "seed": 42,
  "output_format": "json",
  "table": {
    "name": "customers",
    "row_count": 3,
    "columns": [
      {"name": "id", "data_type": "integer", "strategy": "sequence"},
      {"name": "email", "data_type": "email"},
      {
        "name": "status",
        "data_type": "string",
        "strategy": "choice",
        "choices": ["new", "active", "paused"]
      }
    ]
  }
}
```

Generate and validate synthetic rows:

```bash
test-data-agent generate spec.json --output customers.json
test-data-agent validate spec.json customers.json
```

Set `output_format` to `csv` or `parquet`, or override it from the CLI:

```bash
test-data-agent generate spec.json --format csv --output customers.csv
```

## Generate From A Safe Profile

The agent can infer a generation spec from profile metadata such as
`examples/orders_profile.json`.

```bash
test-data-agent generate \
  --profile examples/orders_profile.json \
  --count 10000 \
  --mode mixed \
  --invalid-ratio 0.02 \
  --seed 12345 \
  --format csv \
  --output out/orders.csv
```

This writes:

- `out/orders.csv`
- `out/generation_spec.json`
- `out/validation_report.json`

`mixed` mode injects controlled invalid values according to `--invalid-ratio`.
Use `valid` mode for datasets that should fully pass schema validation.

## CSV Workflow

Profile a CSV into safe metadata:

```bash
test-data-agent profile-csv data/customers.csv \
  --output out/customers_profile.json
```

Generate synthetic data directly from a CSV:

```bash
test-data-agent generate-from-csv data/customers.csv \
  --count 1000 \
  --mode mixed \
  --invalid-ratio 0.02 \
  --seed 12345 \
  --format parquet \
  --output out/customers.parquet
```

`generate-from-csv` writes the requested output plus:

- `csv_profile.json`
- `generation_spec.json`
- `validation_report.json`

The CSV profiler currently uses Python CSV parsing with header detection via
`csv.DictReader`. It emits aggregates, distributions, ranges, and masked
patterns; it does not preserve source rows.

## Business Rules

Business rules are YAML files layered on top of synthetic generation. They can
validate generated rows, apply deterministic scenario distributions, and create
controlled invalid cases. Supported modes are `valid`, `mixed`, `negative`,
`edge`, and `load_test`.

```yaml
field_rules:
  - table: orders
    field: status
    required: true
    allowed_values: [paid, refunded]

row_rules:
  - type: conditional_required
    table: orders
    when: {field: status, equals: refunded}
    required_fields: [refund_reason]

  - type: conditional_allowed_values
    table: orders
    field: shipping_method
    when: {field: status, equals: paid}
    allowed_values: [ground, air]

  - type: temporal_ordering
    table: orders
    start_field: created_at
    end_field: shipped_at

  - type: formula
    table: orders
    field: total
    expression: quantity * unit_price

cross_table_rules:
  - type: foreign_key
    child_table: orders
    child_field: customer_id
    parent_table: customers
    parent_field: customer_id

  - type: aggregate_formula
    table: orders
    field: total
    expression: "100"
    expected: 100

scenarios:
  - name: paid_ground
    weight: 8
    field_values:
      orders:
        status: paid
        shipping_method: ground
  - name: refunded
    weight: 1
    field_values:
      orders:
        status: refunded
        refund_reason: damaged
```

Use rules with CSV-derived or Trino-derived profiles:

```bash
test-data-agent generate-from-csv data/orders.csv \
  --count 1000 \
  --mode mixed \
  --invalid-ratio 0.05 \
  --seed 12345 \
  --format json \
  --output out/orders.json \
  --business-rules rules/orders.yaml
```

When rules are provided, the output directory also gets
`business_validation_report.json` with rule pass/fail counts and failed-rule
details.

## Trino MCP Server

The MCP server exposes small safe tools for metadata and profiling:

- `list_catalogs`
- `list_schemas`
- `list_tables`
- `describe_table`
- `profile_table`
- `profile_column`
- `sample_rows_masked`
- `run_safe_select`

Configure Trino with environment variables:

```bash
TRINO_HOST=trino.example.internal
TRINO_PORT=443
TRINO_USER=your_user
TRINO_HTTP_SCHEME=https
TRINO_ALLOWED_CATALOGS=hive,iceberg
TRINO_ALLOWED_SCHEMAS=dev,test,staging
```

Start the server:

```bash
python -m test_data_agent.mcp_trino_server
```

`run_safe_select` rejects DDL, DML, executable statements, multiple statements,
unbounded row-returning queries, and unrestricted `SELECT *`. Masked sampling
uses conservative field-name detection for likely PII and secrets.

## Business Rules

Business logic is represented as structured YAML or JSON and enforced by code,
not by free-form LLM reasoning. The current rule models support:

- field rules
- conditional required fields
- conditional allowed values
- temporal ordering
- row formulas
- foreign keys
- aggregate formulas
- scenario distributions

Example:

```yaml
field_rules:
  - table: orders
    field: status
    required: true
    allowed_values: [new, paid, shipped, cancelled]
  - table: orders
    field: order_total
    required: true
    min_value: 0

row_rules:
  - type: temporal_ordering
    table: orders
    start_field: created_at
    end_field: fulfilled_at
    allow_equal: true

scenarios:
  - name: paid_order
    weight: 8
    field_values:
      orders:
        status: paid
  - name: cancelled_order
    weight: 1
    field_values:
      orders:
        status: cancelled
```

Use `test_data_agent.business_rules.load_business_rules`,
`test_data_agent.rules_engine.apply_business_rules`, and
`test_data_agent.business_validator.validate_business_rules` from Python code to
apply and validate these rules.

## Python API

```python
from test_data_agent.generator import generate_rows
from test_data_agent.spec import GenerationSpec
from test_data_agent.validator import validate_rows_report

profile = {
    "table": "events",
    "columns": [
        {
            "name": "status",
            "data_type": "varchar",
            "top_values": [{"value": "new"}, {"value": "done"}],
            "approx_distinct_count": 2,
        },
        {
            "name": "amount",
            "data_type": "double",
            "p05": 10,
            "p95": 200,
            "null_ratio": 0.05,
        },
        {
            "name": "created_at",
            "data_type": "timestamp",
            "min_timestamp": "2024-01-01T00:00:00",
            "max_timestamp": "2024-01-31T23:59:59",
        },
    ],
}

spec = GenerationSpec.from_trino_profile(profile, seed=123, row_count=100)
rows = generate_rows(spec)
report = validate_rows_report(rows, spec)
```

Profile input should contain safe metadata only. Do not pass raw production
samples into profile dictionaries.

## Project Layout

- `src/test_data_agent/spec.py` - Pydantic generation specs and profile inference.
- `src/test_data_agent/generator.py` - deterministic synthetic row generation.
- `src/test_data_agent/validator.py` - schema validation for generated rows.
- `src/test_data_agent/csv_profiler.py` - safe CSV profiling.
- `src/test_data_agent/mcp_trino_server.py` - safe read-only Trino MCP tools.
- `src/test_data_agent/business_rules.py` - business-rule models and YAML loader.
- `src/test_data_agent/rules_engine.py` - scenario application and invalid-case injection.
- `src/test_data_agent/business_validator.py` - executable business-rule validation.
- `src/test_data_agent/cli.py` - local command-line interface.
- `examples/` - safe profile examples.
- `prompts/` - agent prompt templates.
- `tests/` - unit tests with mocked/local inputs.

## Development Notes

- Keep generation deterministic with an explicit seed.
- Keep Trino tools small, explicit, read-only, and bounded.
- Prefer profiles, aggregates, distributions, and masked examples over samples.
- Add tests for safety checks, PII masking, schema matching, and generator
  behavior when changing core logic.
- Normal unit tests must not require real Trino access.
