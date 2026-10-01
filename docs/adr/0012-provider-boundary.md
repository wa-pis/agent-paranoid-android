# ADR-0012: Keep providers optional, untrusted and advisory

- Status: Accepted — retrospective baseline.
- Recorded: 2026-09-29. This is the recording date, not an invented original approval date.
- Authority and implementation boundaries: see Evidence below and the [register conventions](index.md#status-and-authority).

## Context

Models can help propose specifications, but provider SDKs, responses and source-derived metadata create trust and disclosure risks.

## Decision

Use a provider-neutral typed exchange with immutable trusted instructions, explicitly untrusted metadata, schema and original-request fingerprints. Validate bounded proposals before application; proposals cannot approve, generate, mutate safety policy or access sources.

Send safe metadata only. Even allowed local categories and matching categorical predicates become field-scoped labels outside the local boundary. Provider request/response/token/time/retry budgets cover the full request. SDKs remain optional; normal tests use fictional transports.

Optional semantic-value providers are a distinct narrow hook: bounded deterministic replay and synthetic namespace/privacy checks still apply. They are not authority for model-authored datasets.

## Alternatives and consequences

Provider-specific logic in the core couples safety to SDK behavior. Passing raw examples or trusting model-declared safety is rejected. Custom application-owned adapters can use the contract without gaining filesystem/database authority.

## Evidence

Sources: [advisor guide](../agent-guides/advisors.md), [advisor API](../reference/advisor.md), [semantic provider guide](../how-to/custom-semantic-provider.md), [support policy](../reference/support-policy.md).
Executable anchors: [advisor](https://github.com/wa-pis/agent-paranoid-android/blob/637065966c12584e11c9b437c1e8b8f8d708c0df/tests/test_advisor.py), [OpenAI](https://github.com/wa-pis/agent-paranoid-android/blob/637065966c12584e11c9b437c1e8b8f8d708c0df/tests/test_openai_provider.py), [GigaChat](https://github.com/wa-pis/agent-paranoid-android/blob/637065966c12584e11c9b437c1e8b8f8d708c0df/tests/test_gigachat_provider.py), [semantic provider](https://github.com/wa-pis/agent-paranoid-android/blob/637065966c12584e11c9b437c1e8b8f8d708c0df/tests/test_semantic_provider.py).

## Revisit when

A provider transport or SDK update needs bounded/redacted contract evidence; new model capabilities do not confer product authority.

