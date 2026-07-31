# Design: agent-orchestration

## Approach

Add `test_data_agent.agent` as a small state-machine layer:

- `plan_agent_request` normalizes the request, profiles the source, infers a
  `DatasetSpec`, writes review artifacts, and stops.
- `approve_agent_workspace` reloads the request and reviewed spec, generates
  synthetic rows, validates them, and writes a generated bundle.

## Data And Contracts

The planning workspace contains:

- `agent_request.json`
- `agent_plan.json`
- `profile.json`
- `dataset_spec.yaml`

The approved workspace also contains:

- `agent_result.json`
- `generated/`

## Failure Modes

Planning rejects non-empty workspaces, missing sources, invalid source types,
unsafe profiles, and workspace placement inside a CSV source folder.

Approval rejects incomplete workspaces, non-empty generated output folders,
invalid specs, unsafe profiles, source-row reuse, and failed deterministic
validation.

## Alternatives

Embedding an LLM runtime was not chosen because it would add credentials,
network behavior, and non-determinism to the package. MCP and external clients
can provide LLM planning while this package owns deterministic safety.
