# Change: timeout-cleanup-coverage

## Why

Generation deadlines were covered for one folder workflow only. Every staged
output shape needs evidence that timeout cannot publish a partial bundle.

## What Changes

- Exercise timeout after staged data exists for folder and review bundles.
- Exercise timeout after staged metadata exists for single-entity output.
- Verify destinations, staging directories, and success metadata are absent.

## Impact

This expands regression coverage and recovery documentation without changing
successful runtime behavior or public contracts.
