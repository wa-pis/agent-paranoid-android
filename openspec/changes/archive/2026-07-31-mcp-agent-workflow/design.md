# Design: mcp-agent-workflow

`plan_dataset` is a thin MCP adapter over `plan_agent_request`.

It:

1. resolves source and destination below the configured workspace root;
2. detects a CSV file, CSV folder, or safe profile unless an explicit source
   type is supplied;
3. validates generation settings through `AgentRequest`;
4. writes the existing review-first workspace;
5. returns the same compact metadata contract as `plan_trino_dataset`.

The tool does not accept inline rows or DatasetSpec files. Subsequent calls use
the existing `inspect_dataset_plan`, `approve_dataset_plan`, and
`recover_dataset_plan` tools.
