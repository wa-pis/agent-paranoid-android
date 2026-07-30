# Change Proposal: cli-mcp-boundaries

## Summary

Separate public CLI and MCP transport concerns from application dispatch,
presentation, and safety policy without changing user-visible behavior.

## Motivation

The CLI and both MCP server modules currently combine interface construction,
request handling, application orchestration, output formatting, and error
translation. Their size makes contract and safety changes harder to review.
Small explicit boundaries reduce regression risk before the public interfaces
are declared stable for 1.0.

## Scope

In scope:

- extract CLI parser construction, command dispatch, and presentation in small
  behavior-preserving steps;
- extract MCP tool registration and transport adapters from application
  services;
- keep safety validation in deterministic core or application services;
- protect every extraction with existing and expanded golden contract tests.

Out of scope:

- new commands, tools, provider integrations, or data-generation behavior;
- command renames or removals;
- a new CLI or MCP framework;
- changes to `DatasetSpec`, artifacts, or approval policy.

## Safety Impact

The refactor SHALL preserve PII handling, source-row reuse checks, SQL
allowlists, filesystem boundaries, resource limits, deterministic generation,
human approval, validation, and row-free interface responses. Thin transport
adapters SHALL NOT duplicate or bypass these checks.

## Compatibility

Command names, options, help behavior, exit codes, JSON contracts, MCP tool
names and schemas, artifact formats, and Python entry points remain compatible.
Golden fixtures fail the change if a public contract drifts unintentionally.
