# Change: cancellation-cleanup

## Why

Interactive cancellation can interrupt bundle writing outside the ordinary
`Exception` hierarchy. Staging output must not remain after a cancelled run.

## What Changes

- Clean staged folder, review, and single-entity outputs on cancellation.
- Re-raise cancellation without publishing a destination or success metadata.
- Document the boundary between cooperative cancellation and hard termination.

## Impact

This strengthens failure cleanup without changing successful output or public
command behavior.
