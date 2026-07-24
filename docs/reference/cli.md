# CLI Reference

The executable is `test-data-agent`.

Use built-in help as the authoritative option reference:

```bash
test-data-agent --help
test-data-agent COMMAND --help
```

## Commands

| Command | Purpose | Primary output |
| --- | --- | --- |
| `doctor` | Check installation and run a temporary smoke generation | Terminal report |
| `profile-csv` | Profile one CSV into safe metadata | Profile JSON |
| `profile-example` | Profile a folder with one CSV per entity | Profile JSON |
| `infer-spec` | Infer a reviewable `DatasetSpec` | YAML or JSON spec |
| `generate-from-csv` | Run the complete single-table workflow | Data file and review artifacts |
| `generate-from-example` | Run the complete related-table workflow | Dataset bundle |
| `generate` | Generate from a spec or safe profile | Data file or dataset bundle |
| `validate` | Validate a generated dataset folder against a `DatasetSpec` | Validation report |
| `agent-plan` | Profile and prepare a spec, then stop for review | Review workspace |
| `agent-approve` | Generate from an approved agent workspace | Dataset bundle |

Aliases:

- `profile-csv-folder` is an alias for `profile-example`;
- `generate-from-csv-folder` is an alias for `generate-from-example`.

## Common Generation Options

| Option | Meaning |
| --- | --- |
| `--count N` | Number of generated rows per entity or an override |
| `--seed N` | Non-negative deterministic seed |
| `--format csv|json|parquet` | Output format |
| `--mode valid|mixed|negative|edge|load_test` | Generation mode |
| `--invalid-ratio R` | Invalid share from `0` to `1` for applicable modes |
| `--business-rules PATH` | Reviewed YAML or JSON rule file |
| `--output PATH` | Output file or new output directory |
| `--overwrite` | Replace supported single-file outputs |

Folder bundle generation requires a new or empty output directory. It does not
silently merge into an existing dataset.

## Profiling Options

| Option | Meaning |
| --- | --- |
| `--table NAME` | Override the inferred entity name for one CSV |
| `--cache-dir PATH` | Safe profile cache location |
| `--no-cache` | Force fresh folder profiling |
| `--rule-sample-rows N` | Bound row-level relationship and rule mining |

Full-file schema and distribution profiling remains streaming. The rule sample
limit bounds comparisons that require row-level relationships.

## Agent Review Flow

```bash
test-data-agent agent-plan data/example_dataset \
  --source-type csv-folder \
  --workspace out/agent \
  --count 25 \
  --seed 12345 \
  --format csv

test-data-agent agent-approve out/agent
```

`agent-plan` must stop before generation. Review the prepared spec and manifest
context before running `agent-approve`.

## Exit Behavior

- exit code `0` means the requested command completed;
- invalid arguments are reported by `argparse`;
- safety, validation, resource, and configuration errors produce a concise
  CLI error and a non-zero exit code;
- intentional negative datasets can produce validation failures by design.

For recovery steps, see [Troubleshooting](../operations/troubleshooting.md).
