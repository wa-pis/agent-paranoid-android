# Design: provider-neutral-advisor

`AdvisorRequest` carries a validated safe profile, a deterministic baseline
`DatasetSpec`, SHA-256 fingerprints, and an explicit untrusted-metadata policy.
The request is provider-neutral JSON-compatible data.

`DatasetAdvisor` has one synchronous `propose` method. Provider adapters may
call any model SDK outside the base package, but must return an
`AdvisorProposal`-compatible mapping.

The core validates provider output with Pydantic and then enforces invariant
checks against the original request. Entity and field identity, primary keys,
privacy rules, privacy settings, generation settings, and validation settings
remain core-owned. Sensitive and identifier classifications cannot be
weakened, and sensitive distributions pass the existing profile safety guard.

A validated proposal is still only a proposal. It reports
`approval_required: true` and `generation_performed: false`; later increments
will connect it to persisted review artifacts and provider examples.
