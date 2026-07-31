# Change Proposal: agent-workspace-status

## Why

The review-first agent flow can plan and approve work, but users and automation
cannot inspect a workspace without opening persisted JSON files manually.

## What Changes

- Add a read-only `agent-status` CLI command.
- Add a typed, versioned Python status contract.
- Report the current phase, next action, artifact paths, and existing summary.
- Reject incomplete or contradictory workspace state.

## Safety

Status inspection does not generate data, modify the workspace, or return
source or generated rows.
