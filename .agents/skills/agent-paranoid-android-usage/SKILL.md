---
name: agent-paranoid-android-usage
description: Choose the supported CLI, Python, or MCP workflow for profiling, synthetic generation, validation, or export in Agent Paranoid Android.
---

# Use the project

Use this skill when an agent must choose how to operate this repository or guide
another agent through a supported workflow. Treat `AGENTS.md` as the safety
authority. Check the installed version and `test-data-agent COMMAND --help`
before suggesting exact flags; the installed package may lag the checkout.
Without a checkout, use the published documentation at
https://wa-pis.github.io/agent-paranoid-android/ for the references below.

| Goal | Entry point | Read only as needed |
| --- | --- | --- |
| Learn with fictional data | `test-data-agent demo` | `README.md`, `docs/reference/cli-workflows.md` |
| Profile one CSV or related CSV folder | `profile-csv` / `profile-example` | `docs/reference/cli.md`, `docs/agent-guides/profiling.md` |
| Produce reviewed synthetic data | `infer-spec` then `generate` and `validate`; or `generate-from-csv` / `generate-from-example` | `docs/reference/cli-workflows.md`, `docs/agent-guides/generation-and-rules.md` |
| Run an agent-managed local workflow | `agent-plan`, `agent-review`, human review, `agent-approve`; use `agent-status` for progress | `docs/reference/cli-automation.md`, `docs/reference/cli-workflows.md` |
| Use a database source | `profile-postgres` or `profile-query` only with configured read-only allowlists and limits | `docs/how-to/postgresql.md`, `docs/how-to/trino.md`, `docs/agent-guides/trino-security.md` |
| Integrate through MCP | Generator server for workspace-scoped synthetic workflows; Trino server for aggregate-only profiling | `docs/how-to/mcp.md`, `docs/mcp_examples.md` |
| Extend Python code | Find the owning module and boundary, then use its typed API | `docs/implementation_map.md`, `docs/reference/application-boundaries.md` |
| Prepare a release | Follow the release gates; do not infer publication authority from a skill | `CONTRIBUTING.md`, `docs/release.md` |

For automated callers, prefer documented JSON output and summaries. Do not
return source rows, generated rows, raw PII, credentials, or mapping literals in
agent messages. The default profiling and generation path is source-free.
Explicit row-returning diagnostics, if enabled, are a separate opt-in surface;
they are not input to generated output.

Selective one-to-one source transformation is an active proposal, not an
alternative name for synthetic generation. For that work, use the
`agent-paranoid-android-transformation` skill and inspect its OpenSpec status
before claiming any executable capability.
