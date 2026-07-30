# Design: openai-advisor-example

The provider module is optional and is not imported by the package root.
Installing the base package therefore does not install or import the OpenAI
SDK.

`OpenAIAdvisorClient.complete` validates a defensive `AdvisorExchange`, checks
the serialized request size, and calls the synchronous Responses API without
streaming. Package-owned instructions use the developer role; the serialized
`AdvisorRequest` uses the user role and is explicitly labelled untrusted.
Structured output is parsed as `AdvisorProposal`.

The adapter accepts output only when the response status is `completed` and a
parsed proposal exists. It returns the proposal to `ExchangeDatasetAdvisor`,
which validates it again against the original fingerprints and safety rules.
Provider exceptions are converted to a stable contract error without copying
remote error text that may contain credentials or request fragments.

The reference agent keeps the deterministic baseline advisor as its default.
Selecting OpenAI affects only the proposal step; status, review, approval,
generation, validation, and recovery continue through the existing core.
