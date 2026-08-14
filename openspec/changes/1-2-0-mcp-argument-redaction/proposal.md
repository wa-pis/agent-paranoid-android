# Change Proposal: 1-2-0-mcp-argument-redaction

## Summary

Replace FastMCP/Pydantic argument-validation failures with one fixed local
error before they become MCP tool results. Apply the same transport behavior
to the generator and Trino servers.

## Motivation

FastMCP currently includes a rejected argument in the text of its validation
exception. Although that value returns only to the caller that supplied it,
the MCP boundary should not reflect caller-controlled literals in errors.

## Scope

In scope:

- Redact typed argument-validation failures in both MCP server factories.
- Preserve non-validation tool errors and existing MCP tool schemas.
- Add fake/local regression coverage and update the public safety contract.

Out of scope:

- Malformed JSON-RPC logging tracked separately as MT-03.
- New MCP tools, transports, authentication, or deployment modes.

## Safety Impact

Rejected MCP values no longer appear in tool error text. The change does not
alter source access, SQL policy, filesystem access, generated artifacts, or
deterministic generation.

## Compatibility

Tool names and input/output schemas are unchanged. Calls rejected by typed
argument validation now receive `Tool arguments failed validation` instead of
the SDK's detailed Pydantic exception. Other application errors are unchanged.
