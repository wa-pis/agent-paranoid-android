# Agent Orchestration Delta

## ADDED Requirements

### Requirement: Local Planning Reuses Bounded Metadata Safely

Review-first folder planning SHALL use an `auto` metadata-only profile-cache
policy by default, SHALL provide an explicit fresh-profile escape hatch, and
SHALL enforce a local profile deadline and bounded row-level sample. A cached
profile MUST be invalidated by the source fingerprint and MUST NOT contain
source rows or raw sensitive values.

#### Scenario: Repeated folder planning uses the cache

- **GIVEN** the source fingerprint and sampling settings match a valid cached
  safe profile
- **WHEN** `agent-plan` is run again without a refresh override
- **THEN** it reuses the cached metadata without rereading the source rows
- **AND** `agent-plan --no-cache` forces a fresh profile

#### Scenario: Local profiling reaches its budget

- **GIVEN** profiling would exceed its configured deadline or bounded sample
  budget
- **WHEN** the next profile operation starts
- **THEN** the operation fails closed with a structured limit error
- **AND** no partial profile is published as trusted cache metadata

### Requirement: Advisor Calls Have Typed Performance Budgets

The optional advisor integration SHALL expose typed settings for model,
reasoning effort, complete prompt/input size, output token budget, timeout, and
retry count. The complete provider request budget SHALL include trusted
instructions and transport/schema overhead, not only the serialized
`AdvisorRequest`. Fast/normal/quality defaults SHALL be benchmark-backed.

#### Scenario: Advisor request is bounded and observable

- **GIVEN** a safe advisor exchange and a selected preset
- **WHEN** the provider call is made
- **THEN** the request and response stay within the configured budgets
- **AND** timeout and retries are bounded
- **AND** recorded metadata contains model, settings, sizes, latency, status,
  and usage without source values, prompts, secrets, or rows

#### Scenario: Oversized advisor input fails before network

- **GIVEN** the complete provider request exceeds its configured input budget
- **WHEN** the advisor starts
- **THEN** it rejects the request before network I/O
- **AND** the error does not echo profile values or credentials

### Requirement: Relationship Ranking Is Candidate-Bound And Review-Gated

An optional provider adapter MAY rank deterministic
`RelationshipDiscoveryCandidate` objects, but SHALL NOT invent candidates,
receive source rows or raw values, mutate a `DatasetSpec`, approve a proposal,
or authorize generation. Candidate identity and field references MUST be
validated deterministically before any human review artifact is written.

#### Scenario: Advisor ranks safe relationship candidates

- **GIVEN** deterministic candidates with normalized evidence and opaque IDs
- **WHEN** an optional relationship advisor returns rankings
- **THEN** the response is accepted only when candidate IDs, kinds, and fields
  match the input candidates
- **AND** the result remains `requires_human_review`
- **AND** no DatasetSpec or generated output is changed
