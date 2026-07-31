# Change: interrupted-commit-rollback

## Why

Staging cleanup is insufficient if an interruption occurs after an atomic
folder rename or partway through a multi-file single-entity commit.

## What Changes

- Remove folder and review destinations when interruption follows rename.
- Make single-entity publication transactional with temporary backups.
- Restore replaced files, remove partial new files, and preserve unrelated files.

## Impact

Failed publication becomes fail-closed. Successful artifact names and content
remain unchanged.
