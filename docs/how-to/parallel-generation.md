# Parallel Generation And Streaming CSV

This page describes **stable 1.8.0 features**; check
[publication status](../1.8.0-release-status.md) before installing.
Published 1.7.1 does not include `--stream-csv` or the `tiled-v1` Python API.
Existing ordinary generation and reviewed
`scalable-v1`/`scalable-relational-v1` policies remain available; see
[capacity and scalable generation](dataset-capacity.md).

## Choose The Export Path

| Path | When to use it | Data and memory contract |
| --- | --- | --- |
| Ordinary `generate` | Existing specs, rules, modes and supported relationships | Existing seeded engine and limits; materialized rows |
| Reviewed `scalable-v1` / `scalable-relational-v1` | The released bounded independent/eligible linked-table workflows | Explicit execution policy, streaming validation/recovery and capacity tooling |
| New `generate --stream-csv` | One independent valid-mode entity without global rules | Fixed tiles, explicit worker count, CSV only; separate `tiled-v1` seed stream |
| New Python `generate_dataset_parallel` | Callers that need generated rows in memory | Parallel candidates, then global solving/validation; full result remains materialized |

An export does not switch engines merely because it is large. The new public
streaming writer uses Python's CSV encoder and needs neither Arrow nor DuckDB.
The optional `profiling` extra serves large input distinct counting, not CSV
generation. Install the exact stable version:

```bash
python -m pip install "agent-paranoid-android==1.8.0"
```

## Export A Reviewed Spec

Use a reviewed DatasetSpec, for example this independently authored synthetic
spec saved as `large-csv.yaml`:

```yaml
entities:
  - name: items
    row_count: 750000
    primary_key: item_id
    fields:
      - name: item_id
        data_type: integer
        is_identifier: true
      - name: metric
        data_type: integer
        distribution:
          kind: numeric
          min_value: 0
          max_value: 100
generation_settings:
  seed: 42
  output_format: csv
```

Start with a small output, then run the reviewed count in a separate directory:

```bash
test-data-agent generate large-csv.yaml --count 1000 --stream-csv --workers 1 --output out/tiled-smoke
test-data-agent validate out/tiled-smoke/dataset_spec.yaml out/tiled-smoke
test-data-agent generate large-csv.yaml --stream-csv --workers 4 --output out/tiled-full
```

CLI streaming supplies at most 1,000,000 rows and 25,000,000 cells, with four
workers by default; `--workers` accepts 1–4 and requires `--stream-csv`.
The existing output-byte, disk-space and invocation/deadline limits remain
additional ceilings. The option accepts a DatasetSpec, not `--profile`, and
defaults to CSV; requesting another output format is an error.

Streaming is eligible only for one entity with fields, valid mode, no
relationships, native constraints, embedded business rules or relational
scenarios. Unsupported specs, callback business rules and source-folder checks
keep the ordinary materialized path and its ordinary row limits. A large
streaming request can therefore be refused after fallback. An existing reviewed
`execution_policy` and this option are mutually exclusive: keep the selected
released engine or remove the separate streaming request.

The bundle contains the CSV, effective specification, validation report and
generation manifest. Check
`generation_manifest.json` → `reproducibility.generator_algorithm_version`:
an actual streaming export records `tiled-v1`; fallback records the ordinary
algorithm identity. The effective spec alone does not select `tiled-v1` for a
later run: pass the option again.

## Call From Python

Use an importable module with the normal process-entry guard. The Python policy
defaults differ from the CLI: one worker, `max_rows=None` (the existing configured
row ceiling), and 10,000,000 cells. Supply explicit bounds for a larger run:

```python
from pathlib import Path

from test_data_agent.adapters.parallel_generation import ParallelGenerationPolicy
from test_data_agent.io.readers import load_dataset_spec
from test_data_agent.io.workflows import generate_dataset_bundle


def main() -> None:
    spec = load_dataset_spec(Path("large-csv.yaml"))
    result = generate_dataset_bundle(
        spec,
        output_folder=Path("out/tiled-python"),
        seed=42,
        streaming=ParallelGenerationPolicy(
            workers=2, max_rows=1_000_000, max_cells=25_000_000,
        ),
    )
    assert result.validation.valid


if __name__ == "__main__":
    main()
```

`generate_dataset_artifacts` and `generate_dataset_from_spec_path` also accept
the explicit `streaming` policy. For in-memory results,
`test_data_agent.adapters.parallel_generation.generate_dataset_parallel(spec,
seed, policy=...)` collects ordered tiles before global solving and validation.
It rejects embedded business rules, relational scenarios and execution policies;
it does not provide bounded-memory export or replace the reviewed relational
engine. Process creation uses `spawn`; no start-method option is exposed.

## Determinism, Checks And Publication

`tiled-v1` derives each fixed 4,096-row tile from the engine version, seed,
entity and tile index. For the same spec, seed and dependency environment,
changing between one, two and four workers preserves rows, order and CSV data
bytes. This stream deliberately differs from ordinary generation and the
released scalable engines. Review engine changes and keep the manifest when
reproducing an export.

Every tile undergoes schema/type, normalization, constraint and privacy checks.
Global row counts and declared primary-key uniqueness are reconciled before
publication; source rows are never used to fill the output. The typed CSV
contract retains null/empty distinction, formula protection and exact DECIMAL
text. Existing reviewed DECIMAL `numeric_measure` exceptions remain scoped;
numeric storage or an unknown semantic label cannot disable privacy checks.

Before workers or output open, the existing conservative allocation estimate
checks all simultaneously in-flight tiles against the output-byte ceiling;
it does not estimate the full requested dataset. Worker/Faker overhead and the
global primary-key set consume additional memory. This is not an
operating-system RSS cap. Output is written inside private staging with actual byte accounting
and the existing atomic bundle publication/rollback path. Cancellation and
ordinary failures clean workers and staging; hard process termination can still
require checking abandoned staging before retrying in a new directory.

## Measure On The Target Machine

The repository's `scripts/benchmark_public_csv.py`,
`scripts/benchmark_paired_csv.py` and generation benchmark helpers compare
stages, process-tree peak-memory samples, determinism and validation on
synthetic inputs. Earlier 100,000/750,000 × 25-field results belong to the
pre-port implementation and environment. They are historical evidence, not
measurements or speed promises for this 1.7.1-based branch. Re-run the selected
benchmark against the exact checkout and dependency versions before making a
performance decision.
