# Tasks: 1-1-0-cli-ux

Do not tag or publish `1.1.0rc2` or stable `1.1.0` without a new explicit
release command.

## Contract

- [x] Record proposal, design, compatibility, failure, and release impact.
- [x] Add public-contract, artifact-contract, and operational-readiness deltas.
- [x] Extend golden CLI command, JSON, error, and exit-code contracts.

## Artifact Integrity

- [x] Reject single-file format/suffix mismatch before generation.
- [x] Bind overwrite to the same manifest-owned primary data file.
- [x] Preserve atomic cleanup and rollback for failure and cancellation.
- [x] Add synthetic regressions for suffixes, stale files, unrelated sidecars,
  same-file retry, and interrupted publication.

## Errors And Automation

- [x] Render malformed YAML/JSON without a traceback.
- [x] Render Ctrl+C as bounded cancellation with code 130.
- [x] Render optional MCP/provider/database failures with copy-ready guidance.
- [x] Add typed dependency, configuration, I/O, external, internal, and
  cancellation error categories and process codes.
- [x] Add versioned core and doctor JSON output with clean stdout/stderr.
- [x] Add non-TTY regressions for every error category and isolated-wheel
  subprocess smoke coverage.

## Help And Discoverability

- [x] Lead root and examples help with the checkout-free demo.
- [x] Remove or label checkout-only fixture paths in installed help.
- [x] Keep root and every command help readable at 80 and 120 columns.
- [x] Show significant defaults, units, output/overwrite behavior, and optional
  extras in command help.
- [x] Correct unknown-flag recovery to point at command help.
- [x] Add parser-derived bash, zsh, fish, and PowerShell completion output.

## Documentation And Release Gates

- [x] Update README, CLI, installation, troubleshooting, configuration,
  stability, changelog, roadmap, and release checklist.
- [x] Run focused CLI/artifact/docs tests.
- [x] Run ruff, mypy, compileall, full pytest, strict docs, package build, and
  isolated base-wheel CLI smoke.
- [x] Open a signed focused PR and require clean mergeability plus green CI.
- [x] Prepare, but do not publish, a separately reviewed `1.1.0rc2` decision.
