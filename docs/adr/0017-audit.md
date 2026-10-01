# ADR-0017: Audit operations without recording their sensitive contents

- Status: Accepted — retrospective baseline.
- Recorded: 2026-09-29. This is the recording date, not an invented original approval date.
- Authority and implementation boundaries: see Evidence below and the [register conventions](index.md#status-and-authority).

## Context

Shared MCP operators need integrity evidence without creating a second store of SQL, rows, credentials or provider payloads.

## Decision

Use optional append-only JSONL records authenticated with an HMAC-SHA256 chain. Record bounded invocation identity, operation, time and status, not arguments, results or error messages. Configured-but-invalid audit fails closed.

Before admitting work reserve capacity for started and terminal records; do not silently drop terminal events. Protect key/log paths, support one selected secret source, and verify the chain during rotation.

## Alternatives and consequences

Plain logs permit undetected editing; full request logs leak restricted data. HMAC does not resist a key holder, and a local chain cannot prove a valid suffix was removed. Stronger retention needs independently stored final-MAC/log evidence; it is not claimed by this feature.

## Evidence

Sources: [audit operations](../operations/audit-logging.md), [safe MCP specification](https://github.com/wa-pis/agent-paranoid-android/blob/637065966c12584e11c9b437c1e8b8f8d708c0df/openspec/specs/safe-mcp-workflow/spec.md).
Executable anchor: [audit tests](https://github.com/wa-pis/agent-paranoid-android/blob/637065966c12584e11c9b437c1e8b8f8d708c0df/tests/test_audit.py).

## Revisit when

A stronger adversary or retention requirement needs a separate design; do not describe local HMAC as non-repudiation or human approval.

