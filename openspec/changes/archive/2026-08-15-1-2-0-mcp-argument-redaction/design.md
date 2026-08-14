# Design: 1-2-0-mcp-argument-redaction

## Approach

Construct both MCP servers through one transport helper that subclasses the
configured FastMCP type. The override catches only `ToolError` instances whose
direct cause is a Pydantic `ValidationError`, raises a fixed detached
`ToolError`, and lets every other result or exception follow the existing path.

## Data And Contracts

No models, tool schemas, CLI contracts, or artifacts change. The observable
change is the fixed error text for rejected typed MCP arguments.

## Failure Modes

Validation still fails before the tool and audit wrapper execute. The fixed
error has no exception cause and contains no rejected value. Non-validation
tool failures retain their existing behavior.

## Alternatives

Rewriting every MCP error result in the final writer would also suppress safe
application diagnostics. Pattern-matching rendered Pydantic text would depend
on unstable SDK wording. Catching the typed cause at FastMCP dispatch is
narrower and deterministic.
