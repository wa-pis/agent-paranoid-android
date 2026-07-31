# Change Proposal: advisor-exchange-bundle

## Why

External AI clients can export an `AdvisorRequest`, but each integration must
still recreate the trusted instructions and discover the exact structured
response schema. That encourages prompt drift and incomplete proposal objects.

## What Changes

- Add a versioned `AdvisorExchange` bundle around an existing safe request.
- Include immutable trusted instructions and the generated
  `AdvisorProposal` JSON Schema.
- Add `agent-advisor-request --exchange` without changing the existing default
  request output.
- Document how provider adapters keep trusted instructions separate from
  untrusted profile metadata.

## Safety

The bundle performs no provider call, persistence, approval, or generation.
It contains the same safe metadata as `AdvisorRequest`. Validation rejects
modified instructions or a response schema that differs from the package's
current `AdvisorProposal` contract.
