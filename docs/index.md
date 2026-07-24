# Agent Paranoid Android

Agent Paranoid Android generates deterministic synthetic test datasets from
CSV structure, safe profile metadata, or a reviewed `DatasetSpec`.

It is designed for cases where realistic schema, relationships, distributions,
and business rules matter, but source rows and raw PII must not appear in the
generated output.

## Choose Your Starting Point

| I have | Start here |
| --- | --- |
| One CSV file | [First CSV Dataset](getting-started/first-csv.md) |
| A folder of related CSV files | [Related Tables](getting-started/related-tables.md) |
| A safe profile or `DatasetSpec` | [Profiles And Specs](concepts/profiles-and-specs.md) |
| Business constraints | [Add Business Rules](how-to/business-rules.md) |
| An MCP-compatible AI client | [Connect An MCP Client](how-to/mcp.md) |
| A failed command | [Troubleshooting](operations/troubleshooting.md) |

## The Safe Workflow

1. Profile source structure and bounded aggregate metadata.
2. Review the inferred `DatasetSpec` and any business rules.
3. Generate fresh values from an explicit seed.
4. Validate schema, relationships, constraints, and business rules.
5. Review `generation_manifest.json` before accepting the dataset.

The generated bundle reports:

```json
{
  "synthetic": true,
  "source_rows_copied": false,
  "seed": 12345,
  "validation_valid": true
}
```

These fields are evidence produced by deterministic checks. They are not a
replacement for reviewing the inferred specification when a new data domain is
introduced.

## Five-Minute Check

Install the package and run the self-contained smoke test:

```bash
python3 -m pip install agent-paranoid-android
test-data-agent doctor
```

A healthy installation ends with:

```text
quickstart smoke: ok
doctor passed
```

Continue with [First CSV Dataset](getting-started/first-csv.md) to create and
inspect a complete synthetic output bundle.

## Safety Boundaries

The project intentionally refuses:

- copying or shuffling source rows;
- raw PII or secret values in profiles and rule literals;
- unrestricted SQL or write operations through Trino tools;
- output paths that overwrite source input;
- unbounded input, output, rule, query, or generation work.

Read [Safety Model](concepts/safety-model.md) before connecting the project to
production-adjacent data or an AI client.

## Project Status

The current package version is `0.7.0`. `DatasetSpec` is the generation and
validation contract for the CLI and Python API.

Development is substantially AI-assisted. Human review, automated tests, and
the documented security requirements still apply to every change.
