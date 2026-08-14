# Change Proposal: 1-2-0-provider-response-preparse-bound

## Summary

Add a typed local byte budget for OpenAI advisor response text and enforce it
before application JSON/Pydantic parsing.

## Motivation

The GigaChat adapter already rejects oversized response text before structured
parsing. The OpenAI adapter limits request bytes and output tokens, but does not
apply an independent local byte limit to `response.output_text` before parsing.
This leaves accepted Low finding AG-04 open.

## Scope

In scope:

- Add a bounded `max_response_bytes` OpenAI advisor setting.
- Measure UTF-8 output bytes before local structured parsing.
- Fail with fixed redacted diagnostics and bounded per-call metadata.
- Cover the boundary with fake-provider tests and update public documentation.

Out of scope:

- Live or paid provider calls.
- Replacing the official SDK or implementing a streaming HTTP transport.
- Changing provider prompts, advisor schemas, generation, MCP, or database
  behavior.
- Resolving the separate JSON-depth and MCP SDK findings.

## Safety Impact

Oversized provider text fails closed before application JSON/Pydantic parsing.
The failure does not retain provider output, credentials, prompts, source
literals, or exception details. No proposal is returned or applied.

## Compatibility

The new setting is additive and defaults to 1 MiB. Existing provider-neutral
contracts and callers using default settings remain compatible.

## Release Impact

This changes a provider security boundary and therefore requires the next
release candidate. This change does not create a tag or publish artifacts.
