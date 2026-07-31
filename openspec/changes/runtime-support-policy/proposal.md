# Change: runtime-support-policy

## Why

Users need one authoritative statement of which runtimes and optional
integrations are release-gated before the 1.0 compatibility baseline.

## What Changes

- Define the supported CPython matrix and notice rules for changing it.
- Define compatibility and release gates for each optional extra.
- Distinguish versioned provider-neutral contracts from experimental adapters.

## Impact

This is a documentation contract. It changes no runtime behavior, dependency,
or package version.
