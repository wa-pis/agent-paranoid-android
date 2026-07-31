# Change Proposal: mcp-schema-contract

## Summary

Freeze generator and Trino MCP tool names and JSON schemas before 1.0.

## Motivation

MCP response fixtures exist, but clients also depend on tool discovery schemas.
Accidental parameter or result-schema drift should fail CI.

## Scope

In scope:

- record generator and default Trino tool names;
- record each tool input and output JSON Schema;
- keep raw safe SELECT absent from the default Trino surface.

Out of scope:

- changing tools, parameters, results, or opt-in behavior.

## Safety Impact

The contract confirms that unrestricted raw SQL remains absent by default.

## Compatibility

The current MCP discovery surface remains unchanged.
