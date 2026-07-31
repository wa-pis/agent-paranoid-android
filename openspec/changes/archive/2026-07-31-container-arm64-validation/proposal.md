# Change: container-arm64-validation

## Why

Release tags publish AMD64 and ARM64 images, but pull requests execute the
hardened runtime health contract only on the native AMD64 target.

## What Changes

- Build each CLI, generator MCP, and Trino MCP target for Linux ARM64.
- Load and execute each ARM64 image through QEMU in pull-request CI.
- Verify architecture, non-root identity, health check, and hardened runtime.
- Require ARM64 validation before tagged multi-platform publication.

## Impact

Container CI gains three emulated ARM64 jobs. Image contents, entrypoints,
runtime policy, and published platform list remain unchanged.
