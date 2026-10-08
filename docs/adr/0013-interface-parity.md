# ADR-0013: Share application policy across CLI, Python and MCP

- Status: Accepted — retrospective baseline; transformation execution remains gated.
- Recorded: 2026-09-29. This is the recording date, not an invented original approval date.
- Implementation update, 2026-10-02: PR #601 registered the reviewed candidate
  CLI/MCP execution paths. The original status records its historical checkpoint;
  local preservation authority remains receipt-gated, and final RC release gates
  are separate. See ADR-0029 and the current CLI reference.
- Authority and implementation boundaries: see Evidence below and the [register conventions](index.md#status-and-authority).

## Context

Interactive users and agents need different presentation, not different safety or transformation semantics.

## Decision

Keep parsing/presentation and SDK registration outside shared application policy. Preserve versioned CLI JSON/error codes and documented exit codes. Machine clients branch on stable codes, not English text. Doctor distinguishes local availability/smoke from remote reachability.

Default generator MCP and default aggregate-only Trino MCP return metadata, counts and artifact references, not dataset rows. The explicit opt-in run_safe_select is bounded and masked, not source-free or an input to generation. Reject malformed/untrusted MCP arguments before they reach SDK logs. Bound serialized responses as well as database results.

The transformation wizard and noninteractive/agent target share one policy core, but cannot mint local preservation approval.

The closed common-profile candidate now shares a typed review/validate/execute
consumer across isolated CLI and MCP adapters. Installed SDK1/SDK2 stdio checks
cover this consumer, including fixed errors for unknown arguments. This is scoped
fictional evidence, not registration or public activation. Default temporary
output is removed before metadata returns; the closed execution candidate also
supports explicit retained publication below its trusted root with the same
validation/receipt gates. Neither adapter issues approval receipts or returns rows.

## Alternatives and consequences

Independent interface implementations drift. Transport-only checks are bypassable. Exposing rows for agent convenience changes the disclosure contract; successful local doctor checks cannot certify remote infrastructure.

## Evidence

Sources: [application boundaries](../reference/application-boundaries.md), [CLI errors](../reference/cli-errors.md), [safe MCP specification](https://github.com/wa-pis/agent-paranoid-android/blob/637065966c12584e11c9b437c1e8b8f8d708c0df/openspec/specs/safe-mcp-workflow/spec.md).
Executable anchors: [CLI presenter](https://github.com/wa-pis/agent-paranoid-android/blob/637065966c12584e11c9b437c1e8b8f8d708c0df/tests/test_cli_presenter.py), [MCP roundtrip](https://github.com/wa-pis/agent-paranoid-android/blob/637065966c12584e11c9b437c1e8b8f8d708c0df/tests/test_mcp_sdk_roundtrip.py), [Trino source-literal tests](https://github.com/wa-pis/agent-paranoid-android/blob/637065966c12584e11c9b437c1e8b8f8d708c0df/tests/test_trino_source_literals.py).

## Revisit when

Changes to tool schemas, JSON/exit meanings or row-returning surfaces require public-contract review, not only an adapter update.
