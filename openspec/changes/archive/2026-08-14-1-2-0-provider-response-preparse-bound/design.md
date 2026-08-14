# Design: 1-2-0-provider-response-preparse-bound

## Approach

Mirror the existing GigaChat response-byte boundary in
`OpenAIAdvisorSettings`. After the official SDK returns a completed response,
require non-empty string output, measure its UTF-8 byte length, and reject an
oversized value before calling `model_validate_json`.

## Data And Contracts

- `max_response_bytes` defaults to 1 MiB and is capped at 4 MiB.
- Per-call metadata records the measured byte count, bounded by the existing
  metadata model.
- Both oversized and malformed responses use fixed local messages without
  provider text or nested exception chains.
- Successful metadata records raw structured-output text bytes rather than a
  reserialized model estimate.

## Failure Modes

- Missing or non-string output remains an invalid structured response.
- Oversized output fails with `invalid_response` metadata before JSON parsing.
- Malformed output within budget follows the existing structured-validation
  failure path.

## Alternatives

Output-token hints are provider-side guidance rather than a local byte bound.
A custom streaming transport could cap the entire HTTP response before SDK
materialization, but replacing the official SDK is disproportionate to the
accepted local finding and remains a documented multi-tenant revisit trigger.
