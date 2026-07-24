# Related Tables

Use this workflow when a folder contains one CSV file per related table.
The file stem becomes the entity name.

## Input Layout

```text
example_dataset/
  customers.csv
  orders.csv
```

The checked-in fixture already has this shape.

## Generate The Dataset

```bash
test-data-agent generate-from-example tests/fixtures/example_dataset \
  --count 25 \
  --seed 12345 \
  --format csv \
  --output out/example_dataset
```

Expected summary:

```text
Generated synthetic dataset: out/example_dataset | rows: customers=25, orders=25 | seed: 12345 | validation: passed | source rows copied: no
```

The output contains:

```text
out/example_dataset/
  customers.csv
  orders.csv
  profile.json
  dataset_spec.yaml
  generation_manifest.json
  validation_report.json
```

## Review The Relationship

Open `out/example_dataset/dataset_spec.yaml` and locate `relationships`.
The inferred customer/order relationship should name:

```yaml
parent_entity: customers
parent_field: customer_id
child_entity: orders
child_field: customer_id
```

The generator creates new parent identifiers first and assigns child foreign
keys from those generated values. Source identifiers are not reused.

## Run The Stages Separately

Use separate commands when the inferred specification needs review or editing:

```bash
test-data-agent profile-example tests/fixtures/example_dataset \
  --output out/profile.json

test-data-agent infer-spec out/profile.json \
  --count 25 \
  --output out/dataset_spec.yaml

test-data-agent generate out/dataset_spec.yaml \
  --seed 12345 \
  --format csv \
  --output out/generated

test-data-agent validate out/dataset_spec.yaml out/generated \
  --output out/generated/validation_report.json
```

Do not generate until a reviewer accepts inferred relationships and
constraints for a new domain.

See [Profiles And Specs](../concepts/profiles-and-specs.md) for the purpose of
each stage.
