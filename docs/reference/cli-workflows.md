# CLI Workflows

## Offline Demo

```bash
test-data-agent demo --output out/demo
```

The destination must not exist. The command uses a bundled fictional fixture,
seed `20260801`, and no network or optional integration.

## One CSV

```bash
test-data-agent generate-from-csv data/customers.csv \
  --count 100 \
  --seed 12345 \
  --format csv \
  --output out/customers.csv
```

For explanation and review steps, use [First CSV Dataset](../getting-started/first-csv.md).

## Related CSV Tables

```bash
test-data-agent generate-from-example data/example_dataset \
  --count 100 \
  --seed 12345 \
  --format csv \
  --output out/generated
```

See [Related Tables](../getting-started/related-tables.md) for relationship and
business-rule guidance.

## Reviewed DatasetSpec

```bash
test-data-agent generate dataset_spec.yaml \
  --seed 12345 \
  --format csv \
  --output out/generated
```

For previously reviewed safe profile metadata, use `--profile`:

```bash
test-data-agent generate --profile profile.json \
  --count 100 \
  --seed 12345 \
  --format csv \
  --output out/customers.csv
```

`generate` accepts exactly one of a `DatasetSpec` path or `--profile`. Spec
generation writes a dataset folder. Single-table profile generation writes one
data file and requires `--count` and `--seed`.

## Database Sources

Database workflows require mandatory physical-source allowlists and resource
budgets. Connection components and credential-free JDBC-style endpoint input
are environment configuration, never command-line secrets. Qualified column
wildcards expand only against allowlisted metadata and never become a
projection star. Reviewed query files use `profile-query`; query rows, SQL text,
literals, endpoints, and backend messages are excluded from the profile.

Follow the source-specific walkthrough instead of assembling commands from this
reference:

- [PostgreSQL Workflow](../how-to/postgresql.md)
- [Trino Workflow](../how-to/trino.md)

## Review-First Agent Flow

```bash
test-data-agent agent-plan data/example_dataset \
  --workspace out/agent \
  --count 25 \
  --seed 12345 \
  --format csv

test-data-agent agent-review out/agent
REVIEWED_SPEC_SHA256=replace-with-current-hash-from-review
test-data-agent agent-approve out/agent \
  --reviewed-spec-sha256 "$REVIEWED_SPEC_SHA256"
```

`agent-plan` stops before generation. Review `dataset_spec.yaml`, record the
current fingerprint from `agent-review`, and approve exactly that fingerprint.
Optional provider advice changes the spec and therefore requires another review:

```bash
test-data-agent agent-advise out/agent --provider openai
# Or explicitly select the experimental adapter:
test-data-agent agent-advise out/agent --provider gigachat
test-data-agent agent-review out/agent
```

OpenAI remains the default provider; GigaChat is an explicit experimental
choice. Providers receive safe metadata, cannot approve, and cannot generate.
See [Connect An AI Client](../ai_integration.md) for provider-neutral exchange
and trust-channel guidance.

## Generation Options

| Option | Meaning |
| --- | --- |
| `--count N` | Number of generated rows per entity or an override |
| `--seed N` | Non-negative deterministic seed |
| `--format csv\|json\|sql\|parquet` | Output format |
| `--mode valid\|mixed\|negative\|edge\|load_test` | Generation mode |
| `--invalid-ratio R` | Invalid share from `0` to `1` for applicable modes |
| `--business-rules PATH` | Reviewed YAML or JSON rule file |
| `--output PATH` | Output file or new output directory |
| `--overwrite` | Replace one valid manifest-owned target |

Folder generation requires a new or empty destination. Single-entity output
suffixes must match the selected format. Overwrite fails closed when ownership,
manifest, format, or sibling-file checks do not match.

## Profiling Options

| Option | Meaning |
| --- | --- |
| `--table NAME` | Override the inferred entity name for one CSV |
| `--cache-dir PATH` | Safe profile cache location |
| `--no-cache` | Force fresh folder profiling |
| `--rule-sample-rows N` | Bound row-level relationship and rule mining |
| `--local-category ENTITY.FIELD` | Retain one reviewed bounded non-sensitive local enum or constant; repeatable and default-off |

The local-category selector does not bypass sensitive-name, content,
cardinality, value-length, destination, or resource checks. Exact approved
values remain local and are replaced before external-provider requests.
