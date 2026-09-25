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

## Selective Transformation (Review And Policy Decisions)

`transform-review SOURCE.csv POLICY.yaml` reads a fixed local CSV snapshot and
the policy's referenced local mapping files, then prints value-free field
decisions and a snapshot digest. It does not approve, transform, or export
source rows. Mapping paths in the policy are relative to the policy file's
directory. Use `--table NAME` when the entity name differs from the source
filename stem; `--json` wraps the same review in the standard CLI response.
For review-only exact-text plans, a single-file policy may declare a top-level
`file_text_mapping` and optional CSV `mapping` on each `replace_text` field.
The review reports configured scopes but never shows mapping literals;
matching field rules take priority over file-wide rules, without cascading.
Duplicate keys within either table are rejected. These declarations do not enable
replacement output.

Add `--trace` to the same read-only command for up to 50 row/column/rule
ordinal events plus match counts. It reads only the fixed snapshot (at most
10,000 replacement cells), returns no source or replacement literals or
value hashes, and fails closed above the limit. Unmatched cells are counted,
not copied. This is debugging metadata, not a preview of output or approval.

No source-preserving transformation command is available yet. The separate
local approval and execution gates in the active OpenSpec are not satisfied by
this read-only review.

### Edit Field Decisions Locally

`transform-review SOURCE.csv POLICY.yaml --decide` edits an existing valid
policy in place. For every column it displays the value-free system comment,
observed sensitivity and current action, then requires an explicit
`sensitive`, `non_sensitive`, or `unknown` answer. There is no accept-all or
default answer. Actions, mapping references, unmatched behavior and operator
comments are retained unchanged; serialization may normalize YAML formatting.

The wizard displays the revised review and requires `SAVE` before atomically
replacing the owner-only policy file. Invalid answers, conflicts, timeouts,
or source/policy/mapping changes observed before saving leave the policy
untouched. Each answer has a 60-second timeout, within the command's overall
work budget. Input and prompt output must be terminals; piped answers are
rejected. With `--json`, prompts remain on terminal stderr and the final
`policy_saved` result is emitted on stdout. Run `--trace` separately afterward.

This is policy editing, not data approval: no receipt is issued, no rows are
transformed, and a `non_sensitive` answer cannot override conflicting evidence
or enable preservation. A future approval must revalidate and bind all exact
snapshots again. The wizard currently requires a reviewable policy; it does not
repair an invalid input policy.

Add `--edit-actions` with `--decide` to choose each field's action as well:
`keep` retains its existing configuration; `drop`, `preserve`, `synthesize`,
`substitute`, `replace_text`, and `derive` request the corresponding versioned
policy action. There is no implicit choice. Preservation asks for a reference
and rationale, synthesis for a local generation-policy reference, derivation
for an expression and a JSON array of dependency names. These declarations
are not proof of executable formula/generator validity or permission to retain
source data.

For `derive`, review parses the existing bounded arithmetic syntax (1024
characters, 128 AST nodes) without evaluation. Referenced column names must
exactly match the declared dependencies; missing, extra, dropped or cyclic
dependencies reject. Aggregate calls, attribute access and unsupported syntax
are not row-local formulas and reject. Columns literally named `sum` or
`count` still count as ordinary dependencies when used without a function call.
This preflight does not establish result types, null handling or DECIMAL rounding.

Substitution/replacement asks for mapping JSON using the policy's existing
schema. For example, a local exact-text CSV table uses:

```json
{"kind":"csv","path":"status.csv","source_columns":["old"],"replacement_columns":["new"]}
```

`substitute` also accepts inline entries or a reference to an existing shared
domain. For `replace_text`, JSON `null` selects only the policy's existing
file-wide table; a CSV mapping adds column rules. Existing top-level domains
and file-wide declarations are not silently removed or edited. The wizard
then asks for unmatched behavior: `reject`, `preserve`, or `synthesize`.

Private configuration prompts disable terminal echo on POSIX terminals and
accept a bounded single line (less than 4096 UTF-8 bytes, also subject to the
terminal's line-length limit). Use local CSV tables for larger dictionaries.
No private configuration is included in the displayed review or JSON result.
Newly referenced files are read under the same restricted policy directory
and byte budgets, validated, and checked again before saving. Changed or
invalid references abort without replacing the policy. `--edit-actions`
without `--decide` is rejected.

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
