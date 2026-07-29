# Design: advisor-exchange-bundle

`AdvisorExchange` is a provider-neutral transport helper with four boundaries:

1. `trusted_instructions` is static package-owned text.
2. `request` is the existing fingerprint-bound object whose metadata is
   explicitly marked untrusted.
3. `response_model` identifies `AdvisorProposal`.
4. `response_json_schema` is generated directly from that Pydantic model.

The model validator compares the instructions and schema to freshly generated
package values. A serialized bundle therefore cannot be loaded as trusted
after either section is changed.

`agent-advisor-request --exchange` writes one bundle JSON document to stdout.
Without the flag, the command retains its existing `AdvisorRequest` output.
Clients should place trusted instructions in their provider's system or
developer channel, send `request` as structured untrusted input, and constrain
the response with `response_json_schema`.
