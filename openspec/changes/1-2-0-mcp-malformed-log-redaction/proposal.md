# Change Proposal: 1-2-0-mcp-malformed-log-redaction

## Summary

Reject malformed typed MCP requests and notifications in the shared bounded
stdio transport before the MCP SDK can log their caller-controlled values.

## Motivation

The SDK performs a second typed validation after generic JSON-RPC parsing. Its
warning and debug diagnostics include Pydantic input values, so a bounded
malformed value can persist in local operator logs even though the client error
is fixed.

## Scope

In scope:

- Apply typed MCP client-message validation in the shared generator/Trino
  transport before SDK dispatch.
- Return a fixed bounded invalid-parameters response for malformed requests.
- Drop malformed notifications without logging their values.
- Add real-SDK, synthetic, no-network regression coverage and update the public
  safety contract.

Out of scope:

- New MCP tools, transports, authentication, or deployment modes.
- Changes to valid requests, tool argument schemas, or application errors.
- General suppression or replacement of Python or SDK logging.

## Safety Impact

Caller-controlled malformed MCP values no longer cross into SDK validation,
logs, errors, or exception graphs. The change does not alter source access, SQL
policy, filesystem access, generated artifacts, or deterministic generation.

## Compatibility

Valid requests and notifications are unchanged. A malformed request retains
its valid JSON-RPC request ID and receives code `-32602` with fixed
`Invalid request parameters` text. Malformed notifications remain response-free.
