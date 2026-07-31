# Change Proposal: advisor-workspace-handoff

## Why

The provider-neutral advisor contract validates an in-memory proposal, but
applications still need to connect it to the review-first agent workspace.
Without a standard handoff, each integration would invent persistence,
interruption handling, and approval behavior.

## What Changes

- Add `advise_agent_workspace` to apply one validated proposal to a pending
  agent workspace.
- Persist the complete safe exchange as `advisor_review.json`.
- Atomically replace `dataset_spec.yaml` only after the review artifact exists.
- Reuse the existing status fingerprint and approval gate.

## Safety

The handoff never generates rows. It rejects completed or recovery workspaces,
unsafe proposals, profile mismatches, conflicting spec edits, links, and
invalid artifacts. Interrupted persistence resumes from the validated review
artifact without calling the provider again.
