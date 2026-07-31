# Change Proposal: agent-approval-receipt

## Why

The review-first workflow records that approval occurred, but it does not prove
which exact `DatasetSpec` the reviewer approved. A spec can change between
review and generation without a machine-verifiable binding.

## What Changes

- Assign every new agent plan a random plan identifier.
- Fingerprint the safe profile and inferred `DatasetSpec`.
- Require approval to confirm the SHA-256 fingerprint of the currently
  reviewed effective `DatasetSpec`.
- Persist a typed approval receipt tied to the plan, profile, and reviewed
  spec fingerprints.
- Expose the same contract through the CLI, Python API, and generator MCP.

## Safety

Approval fails before generation when the profile changed, the supplied
fingerprint does not match the effective spec, or the workspace predates the
receipt contract. Receipts contain identifiers, hashes, and artifact paths,
not rows or source values.
