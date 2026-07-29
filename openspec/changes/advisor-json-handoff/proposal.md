# Change Proposal: advisor-json-handoff

## Why

The advisor workspace API currently requires an in-process provider adapter.
Users and AI clients need a provider-neutral file/CLI boundary that does not
add a model SDK to the package or weaken the existing review gate.

## What Changes

- Export the safe, fingerprint-bound advisor request for a pending workspace.
- Apply a bounded structured proposal from an external model client.
- Reuse the existing validated `advisor_review.json` persistence and approval
  flow.
- Add CLI commands for the request and proposal sides of the exchange.

## Safety

The request contains safe metadata and a baseline spec, never source rows,
credentials, or generated rows. Proposal application rejects links, oversized
or malformed input, stale fingerprints, unsafe changes, completed workspaces,
and conflicting edits. It never generates data or approves a spec.
