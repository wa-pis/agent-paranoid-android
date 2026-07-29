# Design: advisor-json-handoff

`build_agent_advisor_request` loads an awaiting-approval workspace and returns
the same typed `AdvisorRequest` used by in-process adapters. It is read-only
and refuses to start a second exchange when `advisor_review.json` already
exists.

`apply_agent_advisor_proposal` treats the external proposal as untrusted. It
validates the complete Pydantic contract, request fingerprints, schema
identity, safety settings, sensitive classifications, and generation limits
before persisting the review artifact. It then uses the existing atomic,
conflict-safe spec handoff.

If persistence stops after `advisor_review.json`, retrying the same proposal
validates it against the persisted request and completes the spec update.
Different proposal content or a spec that matches neither the request baseline
nor the persisted proposal fails closed.

The CLI prints the request as one JSON document. Proposal input is a bounded
regular JSON file. Applying a proposal returns pending workspace status and
still requires `agent-approve` with the exact reviewed spec fingerprint.
