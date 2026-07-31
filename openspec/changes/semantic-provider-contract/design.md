# Design: semantic-provider-contract

## Approach

Define a small `SemanticValueProvider` protocol that accepts an immutable,
versioned `SemanticValueRequest`. The request contains only entity and field
names, semantic and data types, row index, and seed.

Call the provider only for non-sensitive, non-identifier semantic fields.
`None` preserves built-in generation. Validate every candidate inside the core
before returning it to the generator.

## Safety Decisions

- Do not pass source values, profile samples, distributions, or generated rows.
- Do not call providers for fields conservatively classified as sensitive.
- Reject recognizable PII, secrets, invalid types, non-finite numbers, invalid
  dates, and oversized strings.
- Redact provider exception text at the contract boundary.

## Alternatives

Dynamic provider loading was deferred because it expands the CLI and MCP trust
surface. Allowing providers to generate sensitive fields was rejected because
the core cannot prove that organization-specific names or addresses are fake.
