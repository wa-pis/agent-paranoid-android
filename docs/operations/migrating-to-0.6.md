# Migrating To 0.6

Version `0.6.0` makes `DatasetSpec` the only generation specification used by
the CLI and Python API. The `GenerationSpec` compatibility API deprecated in
`0.2.0` has been removed so every workflow uses the same privacy,
resource-limit, generation, and validation code.

## What Changed

- `generate` accepts a YAML or JSON `DatasetSpec`, or a safe profile through
  `--profile`.
- `validate` accepts a `DatasetSpec` and a generated dataset folder.
- Single-CSV workflows write `dataset_spec.json`.
- Deprecated specification models, converters, row generators, validators,
  and package-root exports are no longer available.

Safe profile JSON containing top-level `columns` remains supported. Use it with
`generate --profile` or convert it into a reviewable spec with `infer-spec`.

## Convert A Single-Table File

The removed format placed one table under `table`:

```json
{
  "seed": 11,
  "output_format": "json",
  "table": {
    "name": "customers",
    "row_count": 2,
    "columns": [
      {
        "name": "customer_id",
        "data_type": "integer",
        "strategy": "sequence"
      },
      {
        "name": "status",
        "data_type": "string",
        "strategy": "choice",
        "choices": ["new", "active"]
      }
    ]
  }
}
```

The equivalent `DatasetSpec` is explicit about entities, identifier behavior,
distributions, and generation settings:

```yaml
schema_version: "1.0"
entities:
  - name: customers
    row_count: 2
    primary_key: customer_id
    fields:
      - name: customer_id
        data_type: integer
        is_identifier: true
        distribution:
          kind: synthetic_identifier
      - name: status
        data_type: string
        distribution:
          kind: categorical
          categories:
            - value: new
              count: 1
            - value: active
              count: 1
generation_settings:
  seed: 11
  output_format: json
```

Review each conversion rather than mechanically changing key names:

| Removed field | `DatasetSpec` field |
| --- | --- |
| `table` | one item in `entities` |
| `tables` | `entities` |
| `columns` | `fields` |
| `foreign_keys` | `relationships` |
| `strategy: sequence` | identifier field plus `synthetic_identifier` distribution |
| `strategy: choice` | `categorical` distribution |
| numeric/date bounds | typed numeric, date, or datetime distribution |
| `sensitive` and Faker provider | privacy annotation plus `semantic_type` |
| root seed and output format | `generation_settings` |

The project intentionally does not silently convert removed specification
files. Automatic conversion could preserve an unsafe assumption or lose
generation intent.

## Update Commands

Generation continues to use the same command shape:

```bash
test-data-agent generate dataset_spec.yaml \
  --output out/generated
```

Validation now requires the generated folder:

```bash
test-data-agent validate dataset_spec.yaml out/generated \
  --output out/generated/validation_report.json
```

For a safe profile payload:

```bash
test-data-agent infer-spec profile.json \
  --count 100 \
  --output dataset_spec.yaml
```

## Update Python Imports

Use the dataset-oriented API:

```python
from test_data_agent import DatasetSpec, generate_dataset, validate_dataset
from test_data_agent.io import generate_dataset_bundle
```

Load and review the new contract before generation:

```python
from pathlib import Path

from test_data_agent.io import load_dataset_spec

spec = load_dataset_spec(Path("dataset_spec.yaml"))
```

See [Profiles And Specs](../concepts/profiles-and-specs.md) for the current
workflow and [DatasetSpec](../dataset_profile_and_spec.md) for the complete
field reference.
