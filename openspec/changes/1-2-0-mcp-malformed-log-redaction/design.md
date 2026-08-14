# Design: 1-2-0-mcp-malformed-log-redaction

## Approach

After generic JSON-RPC parsing and existing structural budgets, validate each
request or notification against the MCP SDK's typed client-message union. On a
Pydantic validation failure, retain only the validated request ID, response
requirement, and request budget in a private sentinel. The stdio reader handles
that sentinel directly instead of sending the invalid message or exception to
the SDK.

Malformed requests receive one fixed JSON-RPC invalid-parameters response,
charged against the reserved terminal-response budget. Malformed notifications
are discarded without a response, as required by JSON-RPC.

## Data And Contracts

No models, tools, CLI contracts, or artifacts change. The observable contract
is a fixed `-32602` response for malformed typed requests and the absence of
caller values from local SDK logs.

## Failure Modes

Structural and byte budgets still run before typed validation. A fixed error
that cannot fit the terminal budget fails closed through the existing budget
exception. Unexpected non-validation errors retain their existing behavior and
are not rewritten.

## Alternatives

Logging filters would depend on SDK message wording and mutate process-global
logging behavior. Redacting rendered Pydantic text would still materialize and
retain the rejected value. Pre-dispatch typed validation keeps the value out of
the SDK and preserves ordinary diagnostics.
