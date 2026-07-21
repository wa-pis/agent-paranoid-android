# Change Proposal: agent-orchestration

## Summary

Add a lightweight agent orchestration layer that turns the current safe
profiling and generation pipeline into a review-first agent workflow.

## Motivation

The project already has deterministic generation, safety checks, CLI commands,
and MCP tools. An AI agent needs a safe orchestration boundary that can plan the
workflow without gaining raw SQL, raw row access, or direct generation powers.

## Scope

In scope:

- `agent-plan` for safe profile and `DatasetSpec` creation.
- `agent-approve` for explicit generation after review.
- Python API models for agent requests, steps, artifacts, and results.
- Documentation and OpenSpec requirements.

Out of scope:

- Calling an LLM API from this package.
- Autonomous approval.
- Arbitrary SQL, shell access, or raw row returns.

## Safety Impact

The change keeps the LLM as a planner only. Existing Python safety checks still
enforce profile safety, deterministic generation, source-row reuse rejection,
validation reports, and generation manifests.

## Compatibility

Existing CLI, MCP, and `DatasetSpec` flows are unchanged. The new agent commands
are additive.
