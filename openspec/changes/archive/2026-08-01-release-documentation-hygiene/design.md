# Design: release-documentation-hygiene

## Approach

Define a short changelog policy, classify the current `Unreleased` entries,
and move only internal implementation evidence out of the user-facing file.
Each moved group retains a canonical link to the OpenSpec change, security
review, release evidence, or other maintained document that explains it.

Keep the top of `CHANGELOG.md` readable without removing the detail needed by
maintainers, auditors, or release reviewers.

## Data And Contracts

- `CHANGELOG.md`: user-facing categories and migration guidance.
- `docs/roadmap.md`: planned work and release gates.
- `openspec/changes/` and `openspec/specs/`: requirements, design, and archived
  implementation evidence.
- Security review and release evidence documents: scanner, owner, disposition,
  run-ID, and artifact details.

## Failure Modes

- An entry with user-visible compatibility or security impact must remain in
  the changelog even if its detailed evidence moves elsewhere.
- A moved entry without a maintained destination is a documentation failure.
- Changelog categories must not imply a feature is complete when only its plan
  or OpenSpec proposal exists.

## Alternatives

### Keep every engineering detail in CHANGELOG.md

Rejected. It obscures user impact and makes release review harder.

### Delete internal entries

Rejected. The evidence remains valuable for maintainers and security review.

### Create a second changelog for every internal subsystem

Rejected. Use the existing OpenSpec and release-evidence structure instead of
creating parallel histories.
