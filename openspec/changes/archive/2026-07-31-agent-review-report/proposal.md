# Change Proposal: agent-review-report

## Why

`agent-status` provides phase and a concise plan summary, but a reviewer still
has to parse the full YAML to find nullability, semantic types, distribution
kinds, primary keys, and privacy defaults. This makes the approval step harder
to understand than planning or generation.

## What Changes

- Add a typed metadata-only `AgentReviewReport` and read-only Python API.
- Add `agent-review` with bounded human output and versioned JSON.
- Show field generation metadata, relationships, privacy settings, warnings,
  and the exact current approval fingerprint.
- Keep `agent-status` focused on phase, next action, and recovery.

## Safety

The report excludes distribution values, source values, and dataset rows. It
revalidates the current workspace, checks that the spec did not change during
report construction, escapes untrusted names, and performs no writes or
generation.
