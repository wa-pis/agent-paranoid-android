# RC5 Independent Security Review Evidence

Date: 2026-08-08
Baseline: `3fa4bc040094f0f278f5aab03b63c4edfe8a6677` (PR #322)

The review independently inspected advisor rare-category sanitization, OpenAI
preflight metadata, JSON-RPC request-ID lifecycle, writer failure cleanup, and
normal-versus-terminal transport-response accounting. It used synthetic inputs
only and did not access source rows, credentials, prompts, or production data.

## Finding and resolution

The MCP SDK accepts JSON values such as booleans, null, fractional numbers,
`NaN`, and infinities as extra notification IDs even though its request and
response models support only string and integer IDs. The active-request
registry previously used raw Python keys, where values such as `true` and `1`
can alias and non-finite numbers cannot be matched reliably.

The transport now rejects every ID outside the supported string-or-integer
contract before dispatch and keys active requests by the exact serialized ID.
Adversarial tests cover unsupported IDs, distinct string/integer identities,
duplicate active IDs, bounded reflection, notification charging, writer and
flush failures, cancellation, and terminal-error fallback failure.

## Result

No unresolved finding remains in the reviewed scope. Focused advisor,
transport, and budget tests passed together (`131 passed`), with Ruff and mypy
clean. The repository release gate and required pull-request pipeline remain
mandatory before this evidence is accepted on `main`.
