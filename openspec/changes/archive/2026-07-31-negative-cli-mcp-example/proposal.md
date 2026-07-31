# Change: negative-cli-mcp-example

## Why

Users need one executable reference proving that CLI and MCP generation
reproduce the same controlled invalid dataset from the same reviewed inputs.

## What Changes

- Add a synthetic spec and business-rule file.
- Document equivalent CLI and generator MCP invocations.
- Contract-test identical row files and violation summaries.

## Safety

The example contains synthetic configuration only. It does not include source
rows, PII, credentials, or external system access.
