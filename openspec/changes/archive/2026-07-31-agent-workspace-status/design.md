# Design: agent-workspace-status

`inspect_agent_workspace` validates the required planning artifacts and loads
persisted `AgentResult` models through the existing bounded text reader.

An awaiting-approval workspace has a valid plan and no generated output. A
completed workspace has a valid completed result, generated folder, validation
report, and generation manifest. Contradictory or partial state fails clearly.

The CLI prints a concise human summary by default. `--json` serializes the
versioned `AgentWorkspaceStatus` model for automation and AI clients.
