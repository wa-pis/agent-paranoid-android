# Change Proposal: mcp-agent-workflow

## Why

An AI client currently has to assemble several low-level generator MCP calls
to plan from a workspace CSV or safe profile. The review-first agent workflow
already owns this orchestration and should be available as one bounded tool.

## What Changes

- Add a high-level `plan_dataset` generator MCP tool for workspace CSV files,
  CSV folders, and safe profile JSON.
- Reuse source detection, safe profiling, DatasetSpec inference, and the
  existing approval/status/recovery state machine.
- Return only review metadata, fingerprints, and artifact paths.

## Safety

Source and workspace paths remain below `TEST_DATA_AGENT_WORKSPACE_ROOT`.
Planning stops before generation, DatasetSpec inputs are rejected, and no
source or generated rows are returned.
