# Change Proposal: gigachat-advisor-provider

## Summary

Add GigaChat as an optional external advisor for the existing review-gated
agent workflow. The adapter will send only the current safe, provider-neutral
`AdvisorExchange`, request a strict structured `AdvisorProposal`, and return
the proposal to the existing deterministic validation and approval boundary.

The integration is explicit and off by default. It adds a `gigachat` optional
dependency profile and a `gigachat` choice while preserving `openai` as the
existing CLI default; it does not add a generator, an MCP tool, or a new
artifact format.

## Motivation

Users who operate in the GigaChat ecosystem should not need to build a custom
adapter or route partially compatible GigaChat requests through the OpenAI
provider module. GigaChat has its own authorization flow, scopes, endpoint,
structured-output details, quotas, finish reasons, and TLS configuration.
Those differences belong in a narrow provider adapter behind the existing
provider-neutral contract.

## Scope

In scope:

- An optional `gigachat` package extra using the official Python SDK, subject
  to license and Python 3.11-3.14 compatibility gates.
- A `GigaChatAdvisorClient` implementing the existing structured-output client
  boundary and accepting only a validated `AdvisorExchange`.
- Explicit `--provider gigachat` selection for the existing `agent-advise`
  workflow, with the existing OpenAI CLI default unchanged.
- Typed, bounded provider settings for model, scope, request bytes, response
  bytes, output tokens, timeout, retries, and total invocation work.
- Runtime-only authentication from either an authorization key plus an
  allowlisted API scope or a pre-obtained access token.
- Non-streaming `/v1/chat/completions` requests using `json_schema` structured
  output with strict validation.
- Mandatory TLS verification against the official GigaChat endpoint, with an
  optional explicit local CA bundle and no insecure-disable option.
- Fixed, redacted provider errors and bounded metadata that exclude prompts,
  responses, credentials, tokens, and source literals.
- Fake-transport tests, a local-only `doctor --require-extra gigachat` smoke,
  isolated-wheel checks, and synthetic documentation examples.

Out of scope:

- GigaChat generation, validation, profiling, SQL, database, or filesystem
  authority.
- A new MCP tool or any default MCP path that invokes GigaChat.
- Sending source rows, generated rows, database credentials, exact locally
  preserved values, or free text from source data to GigaChat.
- Embeddings, images, files, function calling, model discovery, batch jobs,
  streaming, or conversation history.
- Arbitrary API or OAuth endpoint overrides, disabled TLS verification, or
  caller-provided HTTP requests.
- Reusing the OpenAI Responses API adapter through GigaChat's partially
  compatible OpenAI surface.
- Live or paid provider calls in normal tests or release gates.
- Automatic application, approval, persistence, or generation from model
  output.

## Safety Impact

GigaChat is an external destination. Before the adapter is called, the current
advisor boundary must remove rows, credentials, secrets, sensitive literals,
and exact values from locally preserved category fields. Preserved category
values and matching categorical predicates remain represented by field-scoped
synthetic labels for the complete provider exchange. Their local mapping is
never sent to the provider.

The adapter receives a defensive copy of the safe exchange and has no access
to source adapters, databases, workspaces, approval, generation, validation,
or filesystem publication. Package-owned instructions use a trusted system
message; the serialized exchange is a separate user message explicitly marked
as untrusted data. Request and response work is bounded before proposal
validation, and invalid, incomplete, filtered, oversized, or malformed output
fails before any review artifact is written.

Authorization material and access tokens are resolved only at invocation time,
kept out of typed artifacts, and never included in logs or errors. The adapter
uses the official HTTPS service with certificate verification enabled. Remote
error bodies are not propagated because they may reflect request fragments or
credentials.

A successful provider response is still untrusted. The existing core validates
the proposal against the original fingerprints and safety rules, restores any
local field labels only inside the fingerprint-bound review flow, and requires
explicit human approval before deterministic generation.

## Compatibility

- The base installation remains free of the GigaChat SDK and does not import
  the provider module.
- Existing deterministic, OpenAI, CSV, PostgreSQL, Trino, MCP, Python, CLI,
  `DatasetSpec`, and artifact contracts remain unchanged.
- `gigachat` is an additive provider choice and optional extra, documented as
  experimental under the provider-adapter support policy.
- Existing workspaces and advisor exchange versions remain valid; no new
  serialized credential or provider-response field is introduced.
- Selecting `gigachat` without its extra returns stable installation guidance
  without a traceback or secret-bearing provider error.

## Release Impact

This OpenSpec alone changes no runtime behavior and requires no release
candidate. Its implementation changes dependencies, a public CLI choice, and
an external security boundary, so the implementation must enter a new release
candidate under the current release policy. As an additive provider feature it
is expected to target the next minor release; the exact version is a separate
release decision.
