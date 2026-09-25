---
name: agent-paranoid-android-usage
description: Help users safely profile input and create, validate, or export synthetic test data with Agent Paranoid Android.
---

# Synthetic test data

Use this skill when a user wants synthetic test data. It works offline with an
installed package: inspect `test-data-agent --version`, `test-data-agent --help`,
and `test-data-agent COMMAND --help` for exact options. Do not guess
commands missing from that installation.

| User's input | Supported starting point |
| --- | --- |
| No input; wants to try it | `test-data-agent demo` with fictional data |
| One CSV | `profile-csv`, review safe metadata, then `infer-spec`, `generate`, `validate` |
| Folder of related CSVs | `profile-example`, review relationships, then `infer-spec`, `generate`, `validate` |
| Already reviewed spec | `generate`, then `validate` |
| Wants a guided review | `agent-plan`, `agent-review`, human review of the exact spec, then `agent-approve`; `agent-status` reports progress |
| Allowlisted database | `profile-postgres` or `profile-query` only with read-only credentials, allowlists and limits; plan from aggregate metadata, not source rows |
| MCP client | Discover installed generator tools and use workspace-scoped planning, inspection and approval; default Trino tools are aggregate-only |
| Wants to extend the product | Require a source checkout; read `AGENTS.md`, `docs/implementation_map.md` and the relevant task guide before changing modules. An installed wheel alone is not a development workspace |

Ask for an output location, row count and seed when needed. Keep input and
output inside the configured workspace; do not overwrite existing output
without the user's explicit choice. Prefer review before generation and
value-free JSON/status summaries for automated callers. Never put source rows,
raw PII, secrets, or credentials into an agent message, external model request,
log, fixture, or generated output. Synthetic generation does not preserve
source rows. Optional row-returning diagnostics are a separate surface and
must not feed generation.

If the user instead wants some original field values unchanged, use the
`agent-paranoid-android-transformation` skill. Do not emulate that request with
synthetic generation.
