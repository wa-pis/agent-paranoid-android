# CLI Command Index

The executable is `test-data-agent`. Built-in help is the authoritative option
reference for the installed version:

```bash
test-data-agent
test-data-agent --help
test-data-agent COMMAND --help
test-data-agent --version
```

Running without a command prints the available commands and safe starting
points, then exits successfully.

Use these focused references for task detail:

- [CLI Workflows](cli-workflows.md)
- [CLI Automation And JSON](cli-automation.md)
- [CLI Errors And Exit Codes](cli-errors.md)
- [Shell Completion](shell-completion.md)

## Generate And Validate

| Command | Purpose | Primary output |
| --- | --- | --- |
| `demo` | Run the offline fictional example | Synthetic CSV bundle |
| `profile-csv` | Profile one CSV into safe metadata | Profile JSON |
| `profile-example` | Profile a folder with one CSV per entity | Profile JSON |
| `infer-spec` | Infer a reviewable `DatasetSpec` | YAML or JSON spec |
| `generate-from-csv` | Run the complete single-table workflow | Data file and review artifacts |
| `generate-from-example` | Run the complete related-table workflow | Dataset bundle |
| `generate` | Generate from a spec or safe profile | Data file or dataset bundle |
| `validate` | Validate generated data against a `DatasetSpec` | Validation report |

## Database Sources And SQL

| Command | Purpose | Primary output |
| --- | --- | --- |
| `profile-postgres` | Profile an allowlisted read-only PostgreSQL source | Profile JSON |
| `profile-query` | Profile one reviewed PostgreSQL or Trino query as an aggregate-only virtual source | Profile JSON |
| `export-postgres-sql` | Generate and export executable PostgreSQL DDL and INSERT statements | `.sql` file |

Database connection, allowlist, JDBC-style endpoint, qualified wildcard, and
query-source requirements are documented in the
[PostgreSQL](../how-to/postgresql.md) and [Trino](../how-to/trino.md) guides.

## Review-First Agent Flow

| Command | Purpose |
| --- | --- |
| `agent-plan` | Profile and prepare a spec, then stop for review |
| `agent-review` | Inspect a metadata-only approval checklist |
| `agent-advise` | Ask an installed provider for validated spec changes |
| `agent-advisor-request` | Export safe metadata for an external advisor |
| `agent-advisor-apply` | Validate and apply an external proposal |
| `agent-status` | Inspect phase and next action without changing state |
| `agent-approve` | Generate from an exactly approved workspace |
| `agent-recover` | Revalidate and finish an interrupted approval |

See [CLI Workflows](cli-workflows.md#review-first-agent-flow) for the command
sequence and [CLI Automation And JSON](cli-automation.md) for stable response
contracts.

## Utilities

| Command | Purpose |
| --- | --- |
| `examples` | Show complete examples for common workflows |
| `doctor` | Check installation and run a temporary smoke generation |
| `completion` | Generate completion for bash, zsh, fish, or PowerShell |
| `audit-verify` | Verify an HMAC-authenticated MCP audit log |

Aliases:

- `profile-csv-folder` is an alias for `profile-example`;
- `generate-from-csv-folder` is an alias for `generate-from-example`.
