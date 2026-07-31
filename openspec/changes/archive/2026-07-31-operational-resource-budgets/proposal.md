# Change: operational-resource-budgets

## Why

Operational readiness needs a repeatable signal when representative local
workloads become unexpectedly slow or allocation-heavy.

## What Changes

- Add bounded profiling, multi-entity generation, and validation workloads.
- Enforce generous wall-time and peak traced-allocation release ceilings.
- Run the check as part of the existing release gate and document its scope.

## Impact

This adds a development and release check. It does not change package runtime
behavior, public contracts, dependencies, or versions.
