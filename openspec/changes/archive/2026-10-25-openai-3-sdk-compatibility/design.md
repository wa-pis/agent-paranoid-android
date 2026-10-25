# Design: openai-3-sdk-compatibility

## Approach

Keep the current `<3.0.0` upper bound until a stable 3.x release can be pinned
in an isolated evaluation. Run the existing OpenAI provider and doctor
contracts against that candidate, add focused regression coverage for any SDK
call-shape or exception changes, and then run the complete locked test matrix.

Treat `.github/dependency-compatibility.toml` as the reviewed machine-readable
decision. Update it in the same implementation change as `pyproject.toml` and
`uv.lock`; the existing compatibility checker must continue to reject a range,
lock, policy, CI, or documentation change that lands alone.

PR #483 should be rebased and completed with this evidence only if its branch
is still suitable. Otherwise close it as superseded and use a new focused
implementation PR. Do not bypass the compatibility gate or use administrator
merge privileges for the range-only diff.

## Data And Contracts

Affected files and checks:

- `pyproject.toml`: matching `openai` and `all` extra ranges.
- `.github/dependency-compatibility.toml`: reviewed upper bound and latest
  tested OpenAI version.
- `uv.lock`: resolved 3.x candidate and its transitive dependency graph.
- `tests/test_openai_provider.py`: provider request, structured response,
  bounded failure, timeout, and redaction behavior.
- provider doctor tests: local SDK client construction and structured parsing
  with no external request.
- `docs/reference/dependency-compatibility.md`: tested versions, support rule,
  and upper-bound decision.
- changelog: user-facing optional-integration compatibility note.

The provider-neutral advisor exchange, `DatasetSpec`, CLI/MCP contracts, review
gate, and generated artifact formats remain unchanged.

## Failure Modes

- The SDK changes request or structured-response APIs: add a focused failing
  regression test and adapt only the provider-specific boundary.
- The SDK exposes request, response, credential, or nested exception content:
  fail the evaluation and retain `<3.0.0` until redaction is restored.
- A supported Python version cannot install or run the candidate: retain the
  current range or make a separately reviewed support-policy change.
- Lock, declared range, policy, documentation, or CI evidence drift apart: the
  dependency compatibility check fails before merge.
- Live credentials or network access appear necessary for normal tests: reject
  that test design and use a fake transport with synthetic metadata.

## Alternatives

### Merge PR #483 as metadata-only maintenance

Rejected. `<4.0.0` would claim compatibility with all OpenAI 3.x releases
without selecting or testing one, and the release gate correctly blocks it.

### Keep `<3.0.0` permanently

Deferred. Retaining the bound is correct today, but an evidence-backed 3.x
evaluation avoids leaving a supported optional integration unnecessarily
stale.

### Remove the upper bound before 3.x exists

Rejected. The OpenAI adapter depends on provider-specific SDK behavior, so an
unbounded future major is not an evidence-based support policy.
