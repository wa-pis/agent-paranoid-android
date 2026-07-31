# Change Proposal: agent-json-contract

## Why

Automation and AI clients can read status as JSON, but planning and approval
still emit human-only text and failures do not have stable machine-readable
codes.

## What Changes

- Add `--json` to `agent-plan` and `agent-approve`.
- Version persisted and emitted `AgentResult` payloads.
- Return structured JSON for argument, input, and path errors when an agent
  command requests JSON.
- Document stable exit-code meanings.

## Safety

JSON results preserve the existing row-free agent contract. Error payloads
contain concise messages and command guidance, not exception traces or input
payloads.
