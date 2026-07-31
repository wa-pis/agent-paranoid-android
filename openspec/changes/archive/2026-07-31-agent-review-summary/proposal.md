# Change Proposal: agent-review-summary

## Why

`agent-plan` currently reports only artifact paths. Reviewers must open several
files before they can see the inferred shape, sensitive fields, relationships,
confidence, assumptions, or warnings.

## What Changes

- Add typed field, sensitive-field, relationship, confidence, assumption, and
  warning details to `AgentPlanSummary`.
- Print a concise multi-line review summary after planning and from pending
  workspace status.
- Mark names as untrusted metadata and escape them for terminal output.

## Safety

The summary contains metadata only. It never includes source values, generated
rows, distributions, credentials, or raw PII.
