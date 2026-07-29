# Change Proposal: reference-agent-flow

## Why

The provider-neutral advisor pieces are implemented, but users still need a
single executable example showing how planning, model advice, human review,
approval, generation, and validation fit together. Documentation fragments do
not prove that the whole path remains runnable and review gated.

## What Changes

- Add a public-API-only reference agent with `plan`, `status`, and `approve`
  commands.
- Use a deterministic baseline client so the example needs no provider SDK,
  credentials, or network access.
- Add an end-to-end test for the review stop, fingerprint rejection, and
  successful synthetic generation.
- Publish a task-oriented guide for replacing the stand-in client.

## Safety

Planning sends only safe metadata through the advisor boundary and writes no
generated output. Approval requires the exact current DatasetSpec fingerprint.
The example never auto-approves, returns rows, or owns provider credentials.
