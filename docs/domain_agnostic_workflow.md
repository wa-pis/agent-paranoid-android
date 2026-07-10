# Domain-Agnostic Dataset Workflow

This guide explains the new multi-table synthetic dataset pipeline.

The goal is to start from an example folder of related CSV files and generate a
new synthetic dataset that preserves useful structure without copying source
rows or identifiers.

## Mental Model

The pipeline has five stages:

1. **Profile**
   Read example CSVs and produce safe metadata.

2. **Infer Spec**
   Convert the profile into an editable YAML `DatasetSpec`.

3. **Generate**
   Generate synthetic rows from the spec and an explicit seed.

4. **Solve Constraints**
   Reconcile generated rows so relationships, formulas, temporal ordering, and
   aggregate mappings hold.

5. **Validate**
   Produce a validation report for schema, relationships, and constraints.

## Folder Layout

Input uses one CSV file per table:

```text
example_dataset/
  customers.csv
  orders.csv
```

The file stem becomes the entity/table name. In this example, the entities are
`customers` and `orders`.

## Commands

Profile the example folder:

```bash
python -m test_data_agent.cli profile-example tests/fixtures/example_dataset \
  --output out/profile.json
```

Infer an editable YAML spec:

```bash
python -m test_data_agent.cli infer-spec out/profile.json \
  --count 1000 \
  --output out/dataset_spec.yaml
```

Generate related tables:

```bash
python -m test_data_agent.cli generate out/dataset_spec.yaml \
  --seed 12345 \
  --format csv \
  --output out/generated
```

Validate the generated folder:

```bash
python -m test_data_agent.cli validate out/dataset_spec.yaml out/generated \
  --output out/generated/validation_report.json
```

Run everything in one command:

```bash
python -m test_data_agent.cli generate-from-example tests/fixtures/example_dataset \
  --seed 12345 \
  --count 1000 \
  --format parquet \
  --output out/generated
```

## Large Inputs And Profile Cache

CSV folder profiling streams each file for schema, null ratios, safe
distributions, and field metadata. It does not keep the full source dataset in
memory, so datasets with hundreds of thousands of rows can be profiled locally
without repeatedly re-reading everything.

Relationship and constraint mining still need row-level comparisons, so those
steps use a bounded local sample:

```bash
python -m test_data_agent.cli profile-example tests/fixtures/example_dataset \
  --output out/profile.json \
  --rule-sample-rows 100000
```

Profiles are cached under `.test_data_agent_cache/profiles` by default. The
cache key is based on CSV file names, sizes, and modification times.

```bash
python -m test_data_agent.cli profile-example tests/fixtures/example_dataset \
  --output out/profile.json \
  --cache-dir .test_data_agent_cache/profiles
```

Use `--no-cache` to force a fresh profile. Cache files contain only profile
metadata: schemas, aggregates, safe distributions, relationships, constraints,
and masked patterns. They must never contain source rows or raw PII.

## Large Trino Tables

For Trino sources, do not download large raw result sets for profiling. Use the
safe MCP profiling path so aggregate work happens inside Trino and the agent
receives compact metadata only.

The safe profile includes row counts, null ratios, approximate distinct counts,
numeric ranges and percentiles, timestamp ranges, and bounded top values only
for non-sensitive low-cardinality string fields. Sensitive fields never return
raw top values.

Save the safe profile JSON and reuse it for generation. Repeated generation
runs should read the profile, not re-query the production table.

Use aggregate-only consistency tools for rules and relationships:

- `profile_foreign_key` for parent/child coverage.
- `profile_temporal_ordering` for timestamp/date ordering.
- `profile_formula_rule` for arithmetic formulas such as
  `amount = quantity * unit_price`.
- `profile_conditional_required` for required fields under a condition.
- `profile_conditional_allowed_values` for allowed states under a condition.
- `profile_aggregate_mapping` for parent totals derived from child rows.

These tools return counts, residual metrics, `confidence`, and `status`. They
do not return raw rows or raw PII. Use high-confidence results as candidates in
the YAML `DatasetSpec`, then let generation and validation enforce them.

## What Gets Written

`profile-example` writes:

- `profile.json`

`infer-spec` writes:

- `dataset_spec.yaml`

`generate` with a YAML spec writes:

- one output file per entity, such as `customers.csv` and `orders.csv`
- the effective `dataset_spec.yaml`
- `validation_report.json`
- `generation_manifest.json`

`generate-from-example` writes:

- one output file per entity
- `profile.json`
- `dataset_spec.yaml`
- `validation_report.json`
- `generation_manifest.json`

## How Relationships Are Preserved

Relationship inference looks for identifier-like fields where child values are
mostly contained in a parent key candidate. For example:

```yaml
relationships:
- parent_entity: customers
  parent_field: customer_id
  child_entity: orders
  child_field: customer_id
  relationship_type: many_to_one
  confidence: 1.0
  status: inferred
```

During generation, parent IDs are generated synthetically first. Child foreign
keys are then assigned from those generated parent IDs. Source IDs are never
reused.

## How Constraints Are Preserved

The constraint miner currently infers:

- formula constraints, such as `amount = quantity * unit_price`
- temporal constraints, such as `created_at <= fulfilled_at`
- conditional required constraints, such as `cancellation_reason` required when
  `status == cancelled`
- aggregate mappings, such as a parent total matching the sum of child amounts

Every inferred constraint has:

- `confidence`
- `status`

Treat inferred rules as reviewable metadata. They are useful defaults, not magic
truth.

## Safety Notes

The profiler may read source rows locally to compute safe metadata, but profile
output does not contain raw PII values for sensitive fields. Generated output is
created from the spec and seed, not from shuffled or sampled source rows.

Identifiers are regenerated. Sensitive values are generated synthetically via
Faker or safe fallback generation.
