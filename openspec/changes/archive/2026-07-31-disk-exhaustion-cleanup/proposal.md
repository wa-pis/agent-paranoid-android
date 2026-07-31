# Change: disk-exhaustion-cleanup

## Why

Preflight capacity checks cannot prevent another process from consuming free
space while a bundle is being written. Mid-write exhaustion needs explicit
regression coverage.

## What Changes

- Simulate `ENOSPC` after a partial staged file is created.
- Cover folder, review, and single-entity generation paths.
- Verify no destination, staging directory, or success metadata survives.

## Impact

This verifies existing fail-closed behavior without changing successful output
or public command behavior.
