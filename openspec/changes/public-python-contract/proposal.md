# Change Proposal: public-python-contract

## Summary

Freeze the supported top-level Python exports with a checked-in golden
contract before 1.0.

## Motivation

The package exposes a useful typed API through `test_data_agent.__all__`, but
contract fixtures currently cover CLI, MCP, models, and artifacts only.
Accidental export removal or rename should fail CI visibly.

## Scope

In scope:

- record the existing top-level export names;
- verify every recorded name resolves from `test_data_agent`;
- require explicit fixture review for future API changes.

Out of scope:

- adding, removing, renaming, or deprecating exports;
- changing function signatures, models, or runtime behavior.

## Safety Impact

None. The change adds contract evidence and does not alter data handling.

## Compatibility

The current public Python API remains unchanged.
