# Change Proposal: openai-advisor-example

## Why

The provider-neutral advisor contract is implemented, but users still have to
write the first real structured-output client themselves. A small optional
OpenAI adapter proves the boundary against a production SDK without adding a
model dependency to the base installation.

## What Changes

- Add an optional `openai` packaging extra.
- Add an OpenAI Responses API adapter for `AdvisorExchange`.
- Let the reference agent select the baseline or OpenAI advisor.
- Test trust-boundary separation, request limits, incomplete responses, and
  provider-error redaction without making live API calls.
- Document installation, credentials, model selection, and review-gated use.

## Safety

The adapter sends static trusted instructions and untrusted profile metadata
in separate roles, requests a structured `AdvisorProposal`, disables response
storage, and bounds request and output size. Core validation, exact-fingerprint
human approval, deterministic generation, and source-row protections remain
authoritative.
