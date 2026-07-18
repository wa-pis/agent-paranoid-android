# Test Data Agent

Safe, deterministic synthetic test data generation for database and CSV-driven
test datasets.

The agent profiles schemas and safe aggregate metadata, detects likely
sensitive fields, builds generation specs, generates synthetic rows from an
explicit seed, validates the result, and exports data in common formats. It
never copies source rows into generated output.

## Project Status

Current package version: `0.3.0`.

The domain-agnostic `DatasetSpec` pipeline is the primary path for new work. It
supports safe CSV folder profiling, spec inference, deterministic multi-table
generation, constraint reconciliation, validation, and CSV/JSON/Parquet export.
The generator MCP server now exposes the same profile, infer, generate, validate,
and export workflow to AI clients without returning dataset rows through MCP.

Legacy `GenerationSpec` commands and imports remain available for compatibility,
but they emit deprecation warnings and should be treated as migration paths.

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

Likely PII and secret-like fields are treated as sensitive by default. Sensitive
CSV columns do not emit raw top values. Trino row-returning queries must be
read-only, bounded with `LIMIT`, and cannot use unrestricted `SELECT *`.
Local profile caches store only safe profile JSON: schema metadata,
aggregates, distributions, inferred rules, and masked patterns. They must not
store source rows or raw PII.

Forbidden behavior includes copying production rows, exposing raw PII, exporting
real rows, running DDL/DML SQL, and creating unrestricted SQL tools.

Generation APIs enforce a configurable per-entity row limit. The default is
`100000`; override it with `TEST_DATA_AGENT_MAX_GENERATION_COUNT`. Input and
output paths must be distinct, and folder bundles are assembled atomically.
Parquet keeps homogeneous numeric and boolean column types; intentionally mixed
invalid columns are stored as strings so negative datasets remain exportable.

## Install

Use Python 3.11 or newer.

```bash
python3 -m pip install -e ".[dev]"
```

## Quickstart

If you have one CSV file and just want synthetic data, start here:

```bash
test-data-agent generate-from-csv data/customers.csv \
  --count 100 \
  --seed 12345 \
  --format csv \
  --output out/customers.csv
```

If you have a folder with related CSV files, one file per table, start here:

```bash
test-data-agent generate-from-example data/example_dataset \
  --count 100 \
  --seed 12345 \
  --format csv \
  --output out/generated
```

On success, the CLI prints a short summary with the output location, generated
row counts, seed, validation status, and the `source rows copied: no` safety
check. It also writes review artifacts such as `generation_manifest.json` and
`validation_report.json`.

The example path below uses the checked-in fixture data and writes only local
artifacts under `out/`.

1. Install the package and run the test suite:

```bash
python3 -m pip install -e ".[dev]"
python3 -m pytest
```

After installation, the `test-data-agent` CLI should be available. If your shell
cannot find it, run the same commands as `python3 -m test_data_agent.cli ...`.

2. Generate a synthetic single-table CSV from an example source CSV:

```bash
test-data-agent generate-from-csv tests/fixtures/customers.csv \
  --count 25 \
  --seed 12345 \
  --format csv \
  --output out/customers.csv
```

This prints a summary and creates `out/customers.csv` plus review artifacts next
to it:
`csv_profile.json`, `generation_spec.json`, `validation_report.json`, and
`generation_manifest.json`.

3. Generate a related multi-table dataset from an example CSV folder:

```bash
test-data-agent generate-from-example tests/fixtures/example_dataset \
  --count 25 \
  --seed 12345 \
  --format csv \
  --output out/example_dataset
```

This creates synthetic `customers.csv` and `orders.csv` files, a
`dataset_spec.yaml`, a validation report, and a generation manifest.

4. Re-run with the same seed when you need identical output:

```bash
test-data-agent generate-from-example tests/fixtures/example_dataset \
  --count 25 \
  --seed 12345 \
  --format json \
  --output out/example_dataset_json
```

The source CSV files are used only for schema and safe profile metadata. The
generated rows should not copy source rows or expose raw PII.

Run tests:

```bash
python3 -m pytest
```

Run the same quality checks used by CI:

```bash
python3 -m ruff check src tests
python3 -m compileall -q src tests
python3 -m pytest --cov=test_data_agent --cov-report=term-missing --cov-fail-under=85
```

CI runs these checks on Python 3.11 and 3.12. The security regression suite
also uses Hypothesis to exercise variations of PII aliases, SQL statement
tails, duplicate CSV headers, and sensitive-value masking.

## Documentation

Start here if you want to understand the newer domain-agnostic multi-table
pipeline:

- [Domain-Agnostic Workflow](docs/domain_agnostic_workflow.md)
- [Dataset Profile And Spec Reference](docs/dataset_profile_and_spec.md)
- [AI Integration](docs/ai_integration.md)
- [Generator MCP Design Rationale](docs/mcp_generator_design.md)
- [OpenSpec Baseline](openspec/project.md)
- [Roadmap](docs/roadmap.md)
- [Changelog](CHANGELOG.md)
- [Implementation Map](docs/implementation_map.md)
- [Architecture Diagram](docs/architecture.puml)

## How To Use It

There are five normal ways to use the project:

1. Start from a hand-written generation spec.
2. Start from a CSV file and let the agent infer a safe profile.
3. Start from safe Trino/profile metadata and generate from that profile.
4. Start from an example multi-table CSV folder and infer a dataset spec.
5. Let an MCP-compatible AI client orchestrate the same safe workflow.

Each flow produces synthetic data plus validation artifacts.

### 1. Generate From A Spec

Create `dataset_spec.yaml`:

```yaml
schema_version: '1.0'
entities:
- name: customers
  row_count: 3
  primary_key: customer_id
  fields:
  - name: customer_id
    data_type: integer
    is_identifier: true
    distribution:
      kind: synthetic_identifier
  - name: email
    data_type: string
    sensitive: true
    semantic_type: email
    distribution:
      kind: masked_patterns
      patterns:
      - pattern: email
        count: 1
  - name: status
    data_type: string
    distribution:
      kind: categorical
      categories:
      - {value: new, count: 1}
      - {value: active, count: 2}
relationships: []
constraints: []
generation_settings:
  seed: 42
  output_format: json
```

Generate rows:

```bash
test-data-agent generate dataset_spec.yaml --output out/customers
```

Validate rows against the spec:

```bash
test-data-agent validate out/customers/dataset_spec.yaml out/customers
```

The `generate` command writes:

- `out/customers/customers.json`
- `out/customers/dataset_spec.yaml`
- `out/customers/validation_report.json`
- `out/customers/generation_manifest.json`

### 2. Generate From A CSV

First create a safe CSV profile:

```bash
test-data-agent profile-csv data/customers.csv \
  --output out/customers_profile.json
```

Inspect the profile before using it. It should contain schema, aggregates,
distributions, ranges, and masked patterns, not raw sensitive values.

Generate synthetic data from the CSV:

```bash
test-data-agent generate-from-csv data/customers.csv \
  --count 1000 \
  --mode valid \
  --seed 12345 \
  --format csv \
  --output out/customers.csv
```

For a mixed valid/invalid dataset:

```bash
test-data-agent generate-from-csv data/customers.csv \
  --count 1000 \
  --mode mixed \
  --invalid-ratio 0.02 \
  --seed 12345 \
  --format parquet \
  --output out/customers.parquet
```

`generate-from-csv` writes:

- the requested output file
- `csv_profile.json`
- `generation_spec.json`
- `validation_report.json`
- `generation_manifest.json`

Supported output formats are `json`, `csv`, and `parquet`.

### 3. Generate From A Profile

Use a safe profile such as `examples/orders_profile.json`:

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
- `out/generation_manifest.json`

Profile input should contain safe metadata only. Do not include raw production
samples.

### 4. Generate From An Example Dataset

For domain-agnostic multi-table generation, place one CSV per table in a folder:

```text
example_dataset/
  customers.csv
  orders.csv
```

Profile the folder without exposing raw PII:

```bash
test-data-agent profile-example example_dataset \
  --output out/profile.json
```

Infer a YAML dataset spec with schema, relationships, distributions, formulas,
temporal rules, conditional rules, and aggregate mappings:

```bash
test-data-agent infer-spec out/profile.json \
  --count 1000 \
  --output out/dataset_spec.yaml
```

Generate all related tables:

```bash
test-data-agent generate out/dataset_spec.yaml \
  --seed 12345 \
  --format csv \
  --output out/generated
```

Validate the generated folder:

```bash
test-data-agent validate out/generated/dataset_spec.yaml out/generated \
  --output out/generated/validation_report.json
```

Or run the full flow in one command:

```bash
test-data-agent generate-from-example example_dataset \
  --seed 12345 \
  --count 1000 \
  --format parquet \
  --output out/generated
```

All identifiers are regenerated synthetically. Foreign keys are preserved by
wiring child rows to generated parent IDs, never by reusing source IDs.
The generated folder also contains the effective `dataset_spec.yaml`,
`validation_report.json`, and `generation_manifest.json`.

Large CSV folders are profiled in a streaming pass, so the profiler does not
hold every source row in memory. Schema, null ratios, safe distributions, and
field metadata are computed across the full files. Relationship and constraint
mining use a bounded local sample because they need row-level comparisons:

```bash
test-data-agent profile-example example_dataset \
  --output out/profile.json \
  --rule-sample-rows 100000
```

Profiles are cached by CSV file names, sizes, modification times, and the
`--rule-sample-rows` value:

```bash
test-data-agent profile-example example_dataset \
  --output out/profile.json \
  --cache-dir .test_data_agent_cache/profiles
```

Use `--no-cache` when you need to force a fresh profile. The cache contains
safe profile metadata only, not source rows. Cache writes are atomic, and a
stale or incomplete cache is treated as a miss.

## CLI Reference

Profile an example multi-table CSV folder:

```bash
test-data-agent profile-example INPUT_FOLDER --output PROFILE.json
```

Infer a YAML dataset spec:

```bash
test-data-agent infer-spec PROFILE.json --output DATASET_SPEC.yaml
```

Profile a CSV:

```bash
test-data-agent profile-csv INPUT.csv --output PROFILE.json
```

Generate from a spec:

```bash
test-data-agent generate DATASET_SPEC.yaml --format csv --output OUTPUT_FOLDER
# Deprecated compatibility path:
test-data-agent generate LEGACY_GENERATION_SPEC.json --output OUTPUT.json
```

Generate from a safe profile:

```bash
test-data-agent generate \
  --profile PROFILE.json \
  --count 1000 \
  --seed 12345 \
  --format json \
  --output OUTPUT.json
```

Generate directly from CSV:

```bash
test-data-agent generate-from-csv INPUT.csv \
  --count 1000 \
  --seed 12345 \
  --format csv \
  --output OUTPUT.csv
```

Generate directly from an example multi-table folder:

```bash
test-data-agent generate-from-example INPUT_FOLDER \
  --count 1000 \
  --seed 12345 \
  --format csv \
  --output OUTPUT_FOLDER
```

Validate generated rows (the first form is the deprecated compatibility path):

```bash
test-data-agent validate SPEC.json ROWS.json
test-data-agent validate DATASET_SPEC.yaml OUTPUT_FOLDER
```

Useful options:

- `--count` overrides or supplies row count.
- `--seed` makes generation reproducible.
- `--format json|csv|parquet` selects output format.
- `--mode valid|mixed|negative|edge|load_test` selects the generation mode.
- `--invalid-ratio 0.02` injects invalid values in `mixed` mode; `negative`
  mode intentionally makes every generated value invalid.
- `--table NAME` sets the table name for CSV profiling.
- `--cache-dir PATH` selects the safe profile cache for example-folder
  profiling.
- `--no-cache` disables profile cache reuse.
- `--overwrite` allows replacing existing single-file outputs such as generated
  CSV/JSON/Parquet files, profile JSON files, validation reports, and inferred
  specs. Without it, the CLI refuses to overwrite existing files.
- `--rule-sample-rows N` bounds row-level relationship and constraint mining
  while full-file schema and distribution profiling remains streaming.

## Architecture

The high-level flow is documented as PlantUML in
`docs/architecture.puml`. It shows the CLI, CSV and Trino profiling paths,
safe profile metadata, generation spec inference, deterministic generation,
business-rule validation, and exported artifacts.

## Legacy GenerationSpec Compatibility

Legacy single-table specs are Pydantic models serialized as JSON. New
integrations should use the versioned `DatasetSpec` shown above. Legacy data
types remain:

- `integer`
- `float`
- `boolean`
- `string`
- `date`
- `datetime`
- `email`
- `phone`
- `name`
- `address`
- `uuid`

Supported strategies:

- `sequence`
- `random_int`
- `random_float`
- `random_boolean`
- `faker`
- `choice`
- `constant`
- `date_range`
- `datetime_range`
- `uuid`

Example with ranges and nullable values:

```json
{
  "seed": 7,
  "output_format": "csv",
  "table": {
    "name": "orders",
    "row_count": 100,
    "columns": [
      {"name": "order_id", "data_type": "integer", "strategy": "sequence"},
      {
        "name": "status",
        "data_type": "string",
        "strategy": "choice",
        "choices": ["new", "paid", "shipped", "cancelled"]
      },
      {
        "name": "order_total",
        "data_type": "float",
        "min_value": 1,
        "max_value": 500
      },
      {
        "name": "created_at",
        "data_type": "datetime",
        "min_datetime": "2024-01-01T00:00:00",
        "max_datetime": "2024-12-31T23:59:59"
      },
      {
        "name": "coupon_code",
        "data_type": "string",
        "nullable": true,
        "null_probability": 0.25
      }
    ]
  }
}
```

## Trino MCP Server

The MCP server exposes small safe tools for metadata and profiling:

- `list_catalogs`
- `list_schemas`
- `list_tables`
- `describe_table`
- `profile_table`
- `profile_table_safe`
- `profile_column`
- `profile_foreign_key`
- `profile_temporal_ordering`
- `profile_formula_rule`
- `profile_conditional_required`
- `profile_conditional_allowed_values`
- `profile_aggregate_mapping`
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
python3 -m test_data_agent.mcp_trino_server
```

`run_safe_select` rejects DDL, DML, executable statements, multiple statements,
unbounded row-returning queries without a top-level `LIMIT`, unrestricted
`SELECT *`, and projections of likely PII fields even when they are aliased.
When catalog or schema allowlists are configured, arbitrary selects must use
fully qualified `catalog.schema.table` references that match those allowlists.
SQL validation uses `sqlglot` AST parsing for Trino syntax. Masked sampling uses
conservative field-name detection for likely PII and secrets.

For large Trino tables, use safe profiling instead of downloading rows. The
safe profile path pushes aggregate work into Trino: row counts, null ratios,
approximate distinct counts, numeric ranges and percentiles, and timestamp
ranges are returned as compact metadata. Low-cardinality top values are fetched
only for non-sensitive string columns and always with a bounded `LIMIT`.
Sensitive columns never return raw top values. Save the resulting profile JSON
and reuse it for generation so repeated runs do not re-query the source table.

Consistency profiling is also aggregate-only. Use the dedicated rule tools to
measure whether inferred or proposed rules hold before adding them to a dataset
spec:

- `profile_foreign_key` returns child checked/matched/orphan counts.
- `profile_temporal_ordering` returns pass/fail counts for timestamp ordering.
- `profile_formula_rule` returns pass/fail counts and numeric residuals for
  simple arithmetic formulas.
- `profile_conditional_required` returns scoped present/missing counts without
  echoing condition values.
- `profile_conditional_allowed_values` returns scoped allowed/violation counts.
- `profile_aggregate_mapping` compares parent aggregate fields with child
  `sum` or `count` aggregates.

Each rule profile includes `confidence` and `status`. The tools do not return
source rows, identifiers, or raw PII values.

## Generator MCP Server

The second MCP server exposes the synthetic pipeline to AI clients:

- `profile_csv`
- `infer_dataset_spec`
- `generate_dataset`
- `validate_dataset`
- `export_dataset`

Start it from the workspace that contains allowed inputs and outputs:

```bash
TEST_DATA_AGENT_WORKSPACE_ROOT=/path/to/allowed/workspace \
  python3 -m test_data_agent.mcp_generator_server
```

All tool paths are resolved inside `TEST_DATA_AGENT_WORKSPACE_ROOT`; traversal
and symlink escapes are rejected. MCP responses contain paths, row counts,
version metadata, and validation results, never generated rows. `export_dataset`
always generates fresh synthetic data from a `DatasetSpec`; it cannot convert or
export arbitrary source rows.

Generated bundles contain `dataset_spec.yaml`, `validation_report.json`, and
`generation_manifest.json`. The manifest records the package and schema
versions, spec fingerprint, seed, output format, row counts, validation status,
and the explicit provenance flags `synthetic: true` and
`source_rows_copied: false`.

`infer_dataset_spec` accepts exactly one of a workspace `profile_path` or an
inline `profile_payload` from the Trino MCP server. MCP tools never overwrite
existing output files, and generation requires a new or empty output folder.

Run the local end-to-end example from safe Trino profile metadata:

```bash
python scripts/run_ai_demo.py --output out/ai_demo --count 100 --seed 12345
```

## DatasetSpec Generation

Use `DatasetSpec` when synthetic datasets need deterministic relationships such
as foreign keys:

```python
from test_data_agent.core.dataset import DatasetSpec
from test_data_agent.core.entity import EntitySpec
from test_data_agent.core.field import FieldSpec
from test_data_agent.core.relationship import Relationship
from test_data_agent.core.settings import GenerationSettings
from test_data_agent.generation.entity_generator import generate_dataset

spec = DatasetSpec(
    entities=[
        EntitySpec(
            name="customers",
            row_count=100,
            primary_key="customer_id",
            fields=[
                FieldSpec(name="customer_id", data_type="integer", is_identifier=True),
                FieldSpec(name="status", data_type="string"),
            ],
        ),
        EntitySpec(
            name="orders",
            row_count=1000,
            primary_key="order_id",
            fields=[
                FieldSpec(name="order_id", data_type="integer", is_identifier=True),
                FieldSpec(name="customer_id", data_type="integer"),
            ],
        ),
    ],
    relationships=[
        Relationship(
            child_entity="orders",
            child_field="customer_id",
            parent_entity="customers",
            parent_field="customer_id",
            confidence=1.0,
            status="confirmed",
        )
    ],
    generation_settings=GenerationSettings(seed=12345),
)

rows_by_entity = generate_dataset(spec, seed=12345)
```

Parent and child rows are generated synthetically from safe CSV-derived or
Trino-derived profile metadata. Foreign-key values are assigned from generated
parent rows, never copied from source data. Legacy `MultiTableGenerationSpec`
support remains available through compatibility adapters while downstream code
migrates.

## Business Rules

Business logic is represented as structured YAML or JSON and enforced by code,
not by free-form LLM reasoning. Current rule models support:

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

Business rules can be applied from the CLI with `--business-rules` on
`generate`, `generate-from-csv`, and profile-based generation. They are also
available from Python:

```python
from pathlib import Path

from test_data_agent.business_rules import load_business_rules
from test_data_agent.business_validator import validate_business_rules
from test_data_agent.rules_engine import apply_business_rules

rules = load_business_rules(Path("rules/orders.yaml"))
rows_by_table = {"orders": rows}

apply_business_rules(
    rows_by_table,
    rules,
    seed=12345,
    mode="mixed",
    invalid_ratio=0.02,
)

report = validate_business_rules(rows_by_table, rules)
```

## Python API

```python
from test_data_agent.core.dataset import DatasetSpec
from test_data_agent.core.entity import EntitySpec
from test_data_agent.core.field import FieldSpec
from test_data_agent.core.settings import GenerationSettings
from test_data_agent.generation.entity_generator import generate_dataset
from test_data_agent.validation import validate_dataset

spec = DatasetSpec(
    entities=[
        EntitySpec(
            name="events",
            row_count=100,
            primary_key="event_id",
            fields=[
                FieldSpec(name="event_id", data_type="integer", is_identifier=True),
                FieldSpec(name="status", data_type="string"),
                FieldSpec(name="amount", data_type="float"),
                FieldSpec(name="created_at", data_type="datetime"),
            ],
        )
    ],
    generation_settings=GenerationSettings(seed=123),
)

rows_by_entity = generate_dataset(spec, seed=123)
report = validate_dataset(rows_by_entity, spec)
events = rows_by_entity["events"]
```

Use adapter helpers when converting legacy Trino or CSV profile payloads into a
`DatasetSpec`. Legacy `GenerationSpec` APIs remain supported for compatibility,
but new integrations should target the domain-agnostic modules.

## Project Layout

- `src/test_data_agent/core/` - domain-agnostic dataset, entity, field,
  constraint, privacy, distribution, and settings models.
- `src/test_data_agent/generation/` - deterministic synthetic dataset
  generation.
- `src/test_data_agent/validation/` - dataset validation and rule checks.
- `src/test_data_agent/adapters/` - safe adapters from CSV, JSON, Trino, and
  legacy specs into `DatasetProfile` or `DatasetSpec`.
- `src/test_data_agent/csv_profiler.py` - safe single-CSV profiling.
- `src/test_data_agent/mcp_trino_server.py` - safe read-only Trino MCP tools.
- `src/test_data_agent/mcp_generator_server.py` - workspace-bounded MCP tools
  for profiling, spec inference, generation, validation, and export.
- `src/test_data_agent/safety.py` - profile and source-row reuse safety checks.
- `src/test_data_agent/profiling/` - domain-agnostic CSV-folder profiling,
  relationship inference, constraint mining, and safe profile caching.
- `src/test_data_agent/business_rules.py` - business-rule models and YAML loader.
- `src/test_data_agent/rules_engine.py` - scenario application and invalid-case injection.
- `src/test_data_agent/business_validator.py` - executable business-rule validation.
- `src/test_data_agent/spec.py` - legacy single-table compatibility models.
- `src/test_data_agent/generator.py` - legacy row-generation compatibility path.
- `src/test_data_agent/validator.py` - legacy row-validation compatibility path.
- `src/test_data_agent/cli.py` - local command-line interface.
- `examples/` - safe profile examples.
- `scripts/run_ai_demo.py` - Trino-profile to synthetic CSV demonstration.
- `prompts/` - agent prompt templates.
- `tests/` - unit tests with mocked/local inputs.

## Development Notes

- Keep generation deterministic with an explicit seed.
- Keep Trino tools small, explicit, read-only, and bounded.
- Prefer profiles, aggregates, distributions, and masked examples over samples.
- Add tests for safety checks, PII masking, schema matching, and generator
  behavior when changing core logic.
- Normal unit tests must not require real Trino access.
