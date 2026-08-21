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
| A PostgreSQL database | [PostgreSQL Workflow](how-to/postgresql.md) |
| A Trino coordinator | [Trino Workflow](how-to/trino.md) |
| A safe profile or `DatasetSpec` | [Profiles And Specs](concepts/profiles-and-specs.md) |

## Advanced Integrations

[AI](ai_integration.md), [MCP](how-to/mcp.md),
[Containers](operations/containers.md), and
[Custom providers](how-to/custom-advisor-provider.md)

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

Install the exact stable release and run the self-contained smoke test:

```bash
python3 -m pip install "agent-paranoid-android==1.3.0"
test-data-agent doctor
test-data-agent demo --output out/demo
```

A healthy installation ends with:

```text
quickstart smoke: ok
doctor passed
```

Continue with [First CSV Dataset](getting-started/first-csv.md) to create and
inspect a complete synthetic output bundle.

Use `--json` on core commands for one versioned automation document, or
`test-data-agent completion SHELL` to generate completion for bash, zsh, fish,
or PowerShell from the installed command inventory.

## Safety Boundaries

The project intentionally refuses:

- copying or shuffling source rows;
- raw PII or secret values in profiles and rule literals;
- unrestricted SQL or write operations through Trino tools;
- output paths that overwrite source input;
- unbounded input, output, rule, query, or generation work.

Exact source literals are disabled by default. A field-scoped local allowlist
may retain only a reviewed bounded non-sensitive business enum or constant in
local profiles, deterministic generation, and local SQL export. It never
authorizes source rows, PII, secrets, identifiers, free text, external-provider
payloads, or default MCP responses.

Read [Safety Model](concepts/safety-model.md) before connecting the project to
production-adjacent data or an AI client.

## Project Status

The current stable `1.3.0` release uses `DatasetSpec` as the generation and
validation contract for the CLI and Python API.
Preview `1.3.1rc1` is an explicit opt-in patch candidate for documentation,
package metadata, build-tool, and workflow maintenance; it adds no application
runtime behavior.
