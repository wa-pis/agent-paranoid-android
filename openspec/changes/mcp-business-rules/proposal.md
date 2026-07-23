# Change Proposal: mcp-business-rules

## Summary

Expose the existing deterministic business-rule engine through the generator
MCP server. Generation and export tools accept either a workspace-bounded rule
file or an inline structured payload, apply the rules, and publish a compact
business-validation summary in the generation manifest.

## Motivation

Business rules are currently available through the CLI but not through the MCP
generation boundary. An AI client cannot request executable validation without
falling back to free-form reasoning, and generated manifests do not identify
the rule contract used for a run.

## Scope

In scope:

- strict structured business-rule parsing and resource limits;
- DatasetSpec reference and sensitive-literal validation;
- optional rule input for MCP generation and export;
- business-rule fingerprints and validation summaries in manifests;
- bounded MCP summaries with full reports written as artifacts.

Out of scope:

- arbitrary Python expressions or plugins;
- rule inference by the LLM;
- unrestricted filesystem paths;
- embedding generated rows in MCP responses;
- changing the DatasetSpec schema version.

## Safety Impact

Rule inputs remain inside the generator workspace or the bounded MCP payload.
Unknown fields, dangling table or field references, unsafe expressions, and
raw-looking PII or secrets are rejected before generation. Output remains
synthetic and deterministic by seed. MCP responses contain summaries and
artifact paths, not rows.

## Compatibility

The MCP inputs are additive. Existing calls without business rules preserve
their behavior. Existing CLI rule files remain supported, while malformed
files with ignored unknown keys now fail closed. The manifest gains an optional
`business_validation` object and remains compatible with older bundles.
