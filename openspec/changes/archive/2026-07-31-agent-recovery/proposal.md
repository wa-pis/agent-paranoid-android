# Change Proposal: agent-recovery

## Why

Generation publishes the dataset folder before root-level result and approval
metadata. A process failure in that narrow window leaves a valid generated
bundle that status rejects and approval cannot safely resume.

## What Changes

- Write a typed completion checkpoint inside the temporary generated bundle
  before its atomic publication.
- Report an explicit `recovery_required` workspace phase.
- Add CLI, Python, and MCP recovery operations that revalidate the checkpoint,
  fingerprints, manifest, effective spec, generated rows, and source-row safety
  before publishing completion metadata.
- Make repeated approval of an already completed plan idempotently return the
  existing result when the reviewed fingerprint matches.

## Safety

Recovery never trusts the presence of a generated folder alone. Missing,
malformed, mismatched, or unsafe artifacts fail closed without rewriting the
dataset. Recovery does not regenerate rows and does not expose them.
