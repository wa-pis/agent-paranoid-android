# OpenSpec Changes

Create one folder per proposed behavior change:

```text
openspec/changes/<change-id>/
  proposal.md
  design.md
  tasks.md
  specs/<capability>/spec.md
```

Use this area for changes that alter product behavior, safety guarantees, MCP
contracts, supported formats, or the `DatasetSpec` contract. Keep routine
documentation edits and small bug fixes in normal commits unless a separate
reviewable proposal would reduce risk.

Start from the files in `_template/` when a change needs a proposal.

Keep only ongoing work in this directory. Move a completed change to
`archive/YYYY-MM-DD-<change-id>/` after its required checks and merge are
recorded. A cancelled or superseded change may also be archived, but its
proposal and task list must state what shipped, what did not ship, and whether
future work requires a new proposal. Do not mark deferred tasks as completed.
