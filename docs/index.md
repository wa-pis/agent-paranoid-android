# Agent Paranoid Android

Create repeatable test datasets with useful relationships and business rules,
without copying source rows. Start with a file, safe database metadata, or an
explicit specification, then review the plan before generating fresh values.

<a id="project-status"></a>

Stable `1.6.0` is the recommended release.
Use the CLI below or the runnable
[Python API example](https://github.com/wa-pis/agent-paranoid-android/tree/v1.6.0/examples/python_api).

## Five-Minute Check

```bash
python3 -m pip install "agent-paranoid-android==1.6.0"
test-data-agent doctor
test-data-agent demo --output out/demo
```

The demo uses a bundled fictional fixture. After installation it needs no
network, database or AI provider. A healthy installation reports:

```text
quickstart smoke: ok
doctor passed
```

## Choose Your Starting Point

| I have | Start here |
| --- | --- |
| One CSV file | [First CSV Dataset](getting-started/first-csv.md) |
| Related CSV files | [Related Tables](getting-started/related-tables.md) |
| PostgreSQL | [PostgreSQL Workflow](how-to/postgresql.md) |
| Trino | [Trino Workflow](how-to/trino.md) |
| A safe profile or a plan | [Profiles And Specs](concepts/profiles-and-specs.md) |

<a id="the-safe-workflow"></a>

## Generation Or Transformation?

**Synthetic generation** creates new rows from a reviewed `DatasetSpec`. Use it
for valid, boundary, load or controlled-invalid test cases. The normal process
is profile, review the specification, generate, validate, then
[review the output](getting-started/review-output.md).

**Selective transformation** keeps one-to-one correspondence with input rows
and applies explicit field actions. Its result has mixed origin. Source-value
preservation requires a non-sensitive field decision and fresh local-terminal
approval of the exact inputs and plan; agents and MCP cannot issue it.
Start with [Transform Local Data](how-to/transformation.md).

## Rules And Formats

Use [business rules](how-to/business-rules.md) for formulas, field conditions,
foreign keys and aggregate checks. The
[source/output matrix](reference/source-output-matrix.md) shows routes to CSV,
JSON, Parquet and generated SQL. SQL export writes a file, not a database.

## Advanced Integrations

[AI](ai_integration.md), [MCP](how-to/mcp.md),
[Containers](operations/containers.md), and
[Custom providers](how-to/custom-advisor-provider.md)

<a id="safety-boundaries"></a>

## Before Sharing A Dataset

Review the specification, validation reports and `generation_manifest.json`.
For a valid synthetic dataset expect `synthetic: true`,
`source_rows_copied: false` and `validation_valid: true`.
These checks do not certify statistical anonymity or detect every sensitive
value. Explicit mixed/negative datasets can intentionally fail validation.

Database access remains allowlisted, read-only and bounded. AI receives safe
metadata, never raw PII, secrets or source rows. See the
[Safety Model](concepts/safety-model.md) and
[Troubleshooting](operations/troubleshooting.md).

For offline reading use [Downloads](downloads.md). For another release use
[Documentation Versions](versions.md). Maintainer and release records live in
[History And Maintenance](history.md).
