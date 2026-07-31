# Change Proposal: advisor-provider-adapter

## Why

The project exposes a safe self-describing exchange, but every in-process
integration must still recreate the adapter from that exchange to the
`DatasetAdvisor` protocol. Repeated custom glue risks mixing trusted
instructions with untrusted metadata or skipping proposal validation.

## What Changes

- Add an `AdvisorExchangeClient` protocol for application-owned
  structured-output clients.
- Add `ExchangeDatasetAdvisor` to build the exchange, call the client once,
  and validate its response.
- Document the complete in-process handoff without adding a provider SDK.

## Safety

The client receives a defensive copy of safe metadata, trusted instructions,
and response schema. Its output remains untrusted and is validated against the
original fingerprint-bound request. The adapter has no filesystem, approval,
generation, credential, or network behavior.
