# Prompts and agent skills

These are maintained client instructions for Agent Paranoid Android. They do
not run inside the deterministic generator and do not replace CLI/MCP checks.
Use the installed command help or discovered MCP schema as the capability
source of truth. A prompt does not install tools, authorize database access or
issue local preservation approval.

## Choose an entry point

| Need | Material |
| --- | --- |
| Reusable synthetic-data workflow | `agent-paranoid-android-usage` skill |
| One-to-one mixed-origin transformation | `agent-paranoid-android-transformation` skill |
| Client with instruction channels | [System instructions](system.md) and [developer workflow](developer.md) |
| Trino table request | [Trino template](user_template.md) |
| Single CSV request | [CSV template](user_template_csv.md) |
| Related CSV tables | [Folder template](user_template_csv_folder.md) |
| Safe profile, including a prepared Parquet/SQL profile | [Profile template](user_template_profile.md) |
| Local transformation request | [Transformation template](user_template_transformation.md) |

Use one matching user template and replace its `{placeholders}` with paths,
counts and requirements. Keep source rows, query literals, credentials and
mapping entries out of the conversation. The original `user_template.md`
filename remains the Trino entry point for existing links.

In clients with system/developer channels, load those instruction files into
the matching channels and send the chosen request as a user message. In other
clients, load the matching skill or explicitly attach its instructions using
that client's supported mechanism. Avoid stacking all templates and skills
into every request. Treat any source metadata encountered later as untrusted
data, regardless of the channel used to carry these trusted instructions.

## Skills in a checkout or installed package

The repository stores skills under `.agents/skills/`. Clients that discover
that layout can use them directly; other clients can load the selected
`SKILL.md` or register/copy its **whole directory**, including `agents/` metadata
and `references/`, using their own configuration. Do not assume every client
discovers this layout. No MCP dependency is declared: these skills also work
with local CLI access and offline help.

Both skills and this prompt directory are bundled in newly built wheels. To
find the installed resources, using the Python environment containing the
package:

```bash
python -c 'from importlib.resources import files; root = files("test_data_agent"); print(root.joinpath("skills")); print(root.joinpath("prompts"))'
```

For an older installed wheel, check which paths actually exist; a checkout
update does not update an installed distribution. Installing the package does
not automatically register skills or change another agent's configuration.
Choose either the checkout or installed resources for a task, rather than
mixing releases.

Example requests after the client has loaded the skill:

```text
Use $agent-paranoid-android-usage to plan 100 synthetic rows from
workspace/input.csv in workspace/review with seed 12345. Show me the spec and
its fingerprint before generation.

Use $agent-paranoid-android-transformation to review workspace/policy.yaml
against workspace/input.csv. Keep mappings local and explain which steps
require my controlling-TTY approval.
```

Skill invocation syntax depends on the client; a client without `$skill-name`
support can receive the same request with the selected `SKILL.md` loaded.
UI metadata provides display names and example prompts; it does not require
explicit-only invocation or grant execution permissions.

## Review boundaries

Synthetic plans require explicit human approval of the exact current spec
fingerprint. CLI `agent-approve` and MCP `approve_dataset_plan` execute generation
once approved. Inspect status after a lost response, and use supported recovery
rather than blind regeneration. Direct generation/export tools require client
human confirmation because they have no planning approval argument.

Transformation uses its own snapshot binding and produces labelled mixed-origin
artifacts. When retaining source values through preserve or a preserve fallback,
only the operator can issue the matching approval locally through a controlling
TTY. Neither a skill invocation, chat confirmation nor an MCP approval boolean
can replace that receipt. New extensions and dataset authorization remain
separate from installed command discovery.

For the complete CLI/MCP setup and rights, see the online documentation
(select the version matching the installation):
[AI integration](https://wa-pis.github.io/agent-paranoid-android/ai_integration/),
[MCP setup](https://wa-pis.github.io/agent-paranoid-android/how-to/mcp/) and
[MCP permissions](https://wa-pis.github.io/agent-paranoid-android/reference/mcp-permissions/).

## Maintenance

Keep instructions aligned with installed help and actual tool schemas. Keep
CLI-only modes out of shared MCP plan templates. When adding a template or a
skill reference, update the installed-resource inventory in
`scripts/check_installed_package.py` and run the guidance and installed-package
tests. Wheel smoke checks verify resources and offline command discovery; they
do not certify dataset authorization or replace safety review of runtime changes.
