# Design: gigachat-advisor-provider

## Approach

Keep GigaChat behind the existing provider-neutral advisor port:

```text
safe DatasetProfile + deterministic baseline DatasetSpec
                         |
                         v
                 AdvisorExchange
          (rows and source literals absent)
                         |
                         v
              GigaChatAdvisorClient
          (one bounded structured request)
                         |
                         v
             untrusted AdvisorProposal
                         |
                         v
      existing validation + fingerprint review
                         |
                         v
             explicit human approval
                         |
                         v
        deterministic generation + validation
```

`GigaChatAdvisorClient` lives under `test_data_agent.providers` and implements
the same narrow `complete(exchange)` behavior consumed by
`ExchangeDatasetAdvisor`. It does not receive an application service,
workspace path, source client, generator, validator, approval callback, or
filesystem handle.

The optional implementation uses the official `gigachat` Python SDK behind an
injected internal protocol so tests do not make network calls. Before adding a
dependency range, implementation must verify its license and compatibility on
every supported Python version from 3.11 through 3.14. If it cannot satisfy the
project matrix, implementation stops and this design is revised; it must not
silently drop a supported Python version or hand-roll an OAuth client.

## Upstream Contract

This design is based on official documentation checked on 2026-08-12:

- [GigaChat API guides](https://developers.sber.ru/docs/ru/gigachat/guides/main)
- [Authorization and service URL](https://developers.sber.ru/docs/ru/gigachat/api/reference/rest/gigachat-api)
- [Structured output](https://developers.sber.ru/docs/ru/gigachat/guides/structured-output)
- [OpenAI compatibility](https://developers.sber.ru/docs/ru/gigachat/guides/compatible-openai)
- [Quotas and limits](https://developers.sber.ru/docs/ru/gigachat/limitations)
- [Models](https://developers.sber.ru/docs/ru/gigachat/models/main)
- [Official Python SDK](https://developers.sber.ru/docs/ru/gigachat/guides/using-sdks)
- [API errors](https://developers.sber.ru/docs/ru/gigachat/api/errors-description)

The target service URL is `https://api.giga.chat`, and the first adapter uses
the non-streaming `/v1/chat/completions` structured-output contract. GigaChat's
OpenAI compatibility is partial, while the current OpenAI provider uses the
Responses API, so sharing the OpenAI transport would hide incompatible request
and response semantics.

The model is a bounded explicit setting with a documented provider default.
The resolved provider model may be retained only as bounded run metadata; it
must not change the provider-neutral exchange or be trusted as model output.

## Authentication And TLS

Authentication has exactly one of two runtime modes:

1. `GIGACHAT_CREDENTIALS` plus one typed scope:
   `GIGACHAT_API_PERS`, `GIGACHAT_API_B2B`, or `GIGACHAT_API_CORP`.
2. A pre-obtained `GIGACHAT_ACCESS_TOKEN`.

The authorization key, access token, and any SDK token cache are secret
runtime inputs. They are never accepted as CLI values, serialized into
settings or artifacts, included in `repr`, or copied into logs and errors.
When authorization-key mode is used, token acquisition and refresh are
delegated to the official SDK; tokens remain in memory and are not persisted.

The API and OAuth hosts are fixed to the official HTTPS endpoints for the
first integration. The adapter does not expose arbitrary base-URL or auth-URL
configuration. TLS certificate verification is always enabled. An optional
`GIGACHAT_CA_BUNDLE_FILE` may identify a local trust bundle, but its path is
validated before network work and omitted from public errors and artifacts.
Configuration that attempts to disable certificate verification fails before
client creation. Examples using `verify_ssl_certs=False` or `-k` are not copied
from upstream documentation.

## Request Mapping

The adapter validates a defensive copy of `AdvisorExchange` and serializes the
complete provider request canonically before network work. The request fails
locally if it exceeds `max_input_bytes`.

Messages are separated by trust level:

- one package-owned system message contains the immutable trusted
  instructions;
- one user message labels the following JSON as untrusted profile metadata and
  contains only the serialized safe advisor request;
- no prior conversation, provider output, file, tool, or source sample is
  attached.

The request sets streaming off and requests exactly one completion. It uses
`response_format.type=json_schema`, the package-generated
`AdvisorProposal` JSON Schema, and strict mode. Output-token, timeout, retry,
and total-work ceilings are passed explicitly. One `agent-advise` invocation
makes no parallel provider calls.

The existing provider-bound sanitization remains authoritative. Tests must
inspect the fully serialized outbound request and prove that source rows,
credentials, sensitive sentinels, exact preserved category values, and their
categorical predicate literals are absent. Field-scoped synthetic labels may
be present; their reverse mapping remains local.

## Response Validation

The adapter accepts exactly one choice only when its finish reason indicates a
normal completed response. It rejects empty or multiple choices, truncation,
content-filter or `blacklist` completion, missing content, unexpected content
types, and unknown finish reasons.

The UTF-8 byte length of the returned content is checked before JSON parsing.
The content must be one JSON object with no Markdown or trailing data. Pydantic
then validates it as `AdvisorProposal` with extra fields forbidden. The result
is passed to `ExchangeDatasetAdvisor`, which validates it again against the
original request fingerprints, entity and field identities, and core safety
rules.

GigaChat structured output is currently beta and can materialize schema
defaults instead of copying nested baseline-owned values. If the first
Pydantic pass fails only at known baseline entity or constraint model
validators, and entity plus constraint identity still matches the validated
request, the adapter may replace the malformed `dataset_spec` with the exact
local baseline. No provider-proposed dataset change survives this fallback.
The adapter then repeats full Pydantic, fingerprint, profile, privacy, and
advisor-contract validation. Other validation locations, invented identity,
or provider-added invalid constraints fail closed. A normally valid response
never uses this fallback, so valid unauthorized changes remain visible to and
rejected by the existing core contract.

No raw provider response is stored. A successful run may persist only the
existing validated `advisor_review.json`, whose safe request remains labelled
and whose proposal is bound to the current profile and baseline-spec
fingerprints. Provider failure leaves the planned workspace unchanged and
retryable.

## Budgets And Retries

Provider settings use frozen typed models and explicit upper bounds for:

- request bytes and response-content bytes;
- output tokens and accepted usage counters;
- per-attempt timeout and total invocation deadline;
- retry count and total attempts;
- model and metadata string lengths.

Defaults are conservative: non-streaming, one completion, no application-level
retry, and one active request. Retries may be enabled only within the bounded
setting and only for transient rate-limit or service failures. Authentication,
permission, request validation, structured-output, filtering, and local budget
failures are not retried. OAuth and completion work share the total invocation
deadline.

The adapter does not call model-list or token-count endpoints. Usage counters
from a successful response are optional untrusted metadata and are retained
only when all values pass local bounds.

## Errors And Diagnostics

Provider exceptions and non-success responses are mapped to a small set of
stable local failures such as initialization, authentication, rate limit,
timeout, filtered response, invalid response, and unavailable service. The
remote response body, exception text, headers, request identifier, prompt,
completion, credentials, token, and CA path are never copied into a public
error or log.

Per-call metadata may contain only bounded local values: configured model,
safe setting values, request and response byte counts, elapsed time,
normalized status, normalized finish category, and validated usage counters.
It contains neither the request nor the response. Concurrent or failed calls
cannot overwrite metadata belonging to another call.

## CLI, Packaging, And Doctor

The public additions are:

```text
pip install "agent-paranoid-android[gigachat]"
test-data-agent agent-advise WORKSPACE --provider gigachat [--model MODEL]
test-data-agent doctor --require-extra gigachat
```

The base package does not import the SDK. The `all` profile includes GigaChat
only after dependency, license, and full Python-matrix gates pass. Missing-extra
and missing-credential failures use exact local guidance and no traceback.

Doctor is entirely local: it checks package metadata, constructs the adapter
through an injected fake client, validates strict structured response parsing,
and closes resources. It does not resolve real credentials, obtain a token, or
contact GigaChat.

## Test Strategy

Normal tests use synthetic profiles and a fake SDK protocol. Focused coverage
includes:

- base installation without an SDK import;
- isolated `gigachat` and `all` wheel installation on Python 3.11-3.14;
- minimum and latest accepted SDK versions plus dependency-license checks;
- exact request roles, strict schema, no streaming, and bounded options;
- authorization modes, scope validation, mandatory TLS, and CA-bundle errors;
- request, response, token, timeout, retry, and total-work ceilings;
- normal, empty, multiple, truncated, filtered, oversized, malformed, and
  schema-invalid responses;
- stable redaction for every provider/SDK error category;
- source-row, credential, PII, preserved-literal, and categorical-predicate
  egress sentinels in the final outbound payload;
- unchanged fingerprints, human approval, and deterministic generation after
  a validated proposal;
- local-only doctor behavior with network access disabled.

An opt-in manual smoke may call GigaChat with a synthetic profile and an
explicit test credential. It is not a normal test or release gate, must not use
production data, and must not print or retain the request or response.

## Failure Modes

- Missing extra, credentials, scope, model, or CA bundle: fail before network
  work with fixed local guidance.
- Conflicting credential modes or unsupported scope: fail before SDK client
  creation.
- Insecure TLS or non-official endpoint configuration: reject locally.
- Request budget exceeded: make no provider call.
- OAuth, timeout, rate-limit, or provider outage: close resources, preserve no
  response, and leave the workspace pending.
- Filtered, incomplete, oversized, malformed, or schema-invalid response:
  discard it before persistence or generation.
- Fingerprint or safety mismatch after parsing: reject through the existing
  core contract; do not apply a partial proposal.
- Beta structured output fails only known baseline model validators: substitute
  the exact fingerprint-bound local baseline and rerun every normal validation;
  reject all other invalid response shapes.
- Cancellation: close client resources and propagate a fixed cancellation
  outcome without logging provider text.

## Alternatives

- **Configure the OpenAI adapter with a GigaChat URL:** rejected because
  compatibility is partial and the current adapter uses a different API.
- **Implement OAuth and HTTP directly:** rejected for the first integration;
  the official SDK is smaller to maintain if it passes project gates.
- **Use GigaChain or LangChain:** rejected because one bounded structured
  advisor request needs no chain, graph, memory, tool, or framework dependency.
- **Allow arbitrary endpoint overrides:** rejected because it expands the
  credential and data-egress boundary without a current user requirement.
- **Disable TLS verification like some upstream examples:** rejected because
  it exposes credentials and metadata to interception; a CA bundle is the safe
  compatibility path.
- **Add GigaChat to MCP:** rejected because the existing advisor CLI/Python
  boundary is sufficient and default MCP must not gain external egress.
- **Let GigaChat generate rows:** rejected because provider output is
  non-deterministic and untrusted; deterministic local code remains the only
  generator and validator.
