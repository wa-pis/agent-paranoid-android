# Design: advisor-provider-adapter

`AdvisorExchangeClient.complete` is the narrow application boundary. A
provider-specific implementation maps:

1. `trusted_instructions` to its privileged instruction channel.
2. `request` to structured untrusted input.
3. `response_json_schema` to its structured-output constraint.

`ExchangeDatasetAdvisor.propose` first revalidates and copies the incoming
request, builds an `AdvisorExchange`, and passes a deep copy to the client. It
then validates the returned mapping or `AdvisorProposal` against the unchanged
request. This prevents client-side object mutation from changing the trust
source.

The adapter deliberately performs no provider selection, network call,
credential loading, persistence, approval, or generation. Those concerns stay
with the consuming application and the existing review-first workflow.
