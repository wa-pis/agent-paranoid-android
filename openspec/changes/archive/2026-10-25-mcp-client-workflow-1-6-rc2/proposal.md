# Change Proposal: mcp-client-workflow-1-6-rc2

## Status

Planning requested on 2026-10-08. Target: `1.6.0rc2`, not stable.
This proposal does not authorize tagging, publication, live database access,
external provider calls, or a safety-policy amendment. Implementation and
release acceptance are separate steps; no completed evidence is claimed here.

## Why

The project already exposes separate generator and Trino MCP servers. The
remaining product gap is a clear, tested assistant workflow from connection to
reviewed synthetic artifacts, including error handling and interrupted approval.
Existing real-stdio coverage exercises transport redaction but not the complete
planning, review, approval, inspection, and recovery sequence.

## What Changes

- Make local generator MCP the recommended assistant entry point, while retaining
  Python and CLI interfaces and optional, separately configured Trino profiling.
- Document minimal installation, an absolute executable path, a dedicated
  workspace, generator-only client configuration, and a fictional end-to-end
  example with exact tool arguments and expected summary fields.
- Improve descriptions of existing planning, inspection, approval, and recovery
  tools so assistants can choose the next operation without inventing a flow.
- Explain human review, fingerprint freshness, retry/recovery decisions, missing
  extras, workspace rejection, and bounded transport errors.
- Exercise the documented workflow through the actual MCP client and stdio
  server using fictional fixtures and explicit seeds.
- Detach unexpected native exception causes in MCP 1 as in MCP 2, after real-client
  interruption testing exposed reflected exception text; retain curated cleanup
  and budget diagnostics and add executable cross-major regression coverage.
- Prepare documentation and exact-commit acceptance criteria for `1.6.0rc2`.

## Scope And Compatibility

Reuse existing application services and tool names. Preserve input/output
schemas, explicit approval, deterministic generation, resource limits,
workspace restrictions, redaction, and summary-only generator responses.
Update frozen description fixtures deliberately when descriptions change.
No new transport, dependency, universal orchestration tool, remote hosting,
automatic approval, or source-row-returning capability is required.

The `selective-source-transformation` proposal targets `1.6.0rc1` and remains
an independent workstream with its own policy and acceptance gates. Resolve the
actual reviewed RC1 baseline before cutting RC2; do not imply that RC1 has
shipped or inherit approval for a different commit. This MCP workflow covers
fresh synthetic generation only and must not expose source-preserving execution.

## Safety Impact

Default Trino tools remain read-only, allowlisted, and aggregate-only. Generator
responses contain metadata and artifact paths, not source or generated rows.
Human approval must bind to the exact reviewed specification fingerprint.
Acceptance uses fictional local files without production data, credentials,
live Trino, or external AI calls. Tool descriptions guide assistants; deterministic
application code remains responsible for enforcement.

## Impact

Affected areas: `docs/how-to/mcp.md`, MCP examples and onboarding links,
`mcp_generator_server.py` tool descriptions, frozen tool-description contracts,
real-SDK workflow tests, roadmap, changelog, and release acceptance documentation.
Update user-facing release notes only for delivered capabilities. Version bumps
and release artifacts follow the existing release process after acceptance.
