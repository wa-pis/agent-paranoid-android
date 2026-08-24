# Change Proposal: stable-release-classifier

## Summary

Correct the package maturity classifier in the next ordinary release and make
stable release validation reject wheel or source-distribution metadata that
still declares the project as Beta.

## Motivation

The `1.3.1rc1` preparation correctly changed the classifier to
`Development Status :: 4 - Beta`, but the stable `1.3.1` promotion changed only
the version. The current stable source tree therefore still declares Beta even
though the project documents a stable public contract.

Published artifacts are immutable, so this is follow-up work for the next
normal patch or feature release rather than a reason to replace `1.3.1` or
create an otherwise empty urgent release candidate.

## Scope

In scope:

- Restore `Development Status :: 5 - Production/Stable` for the next stable
  release.
- Keep `Development Status :: 4 - Beta` for release candidates.
- Validate the classifier in built wheel and source-distribution metadata so a
  stable promotion cannot retain the prerelease value.
- Record the metadata correction in the changelog for the release that ships
  it.

Out of scope:

- Rebuilding, replacing, or mutating published `1.3.1` artifacts.
- Creating a release solely for this metadata correction.
- Changing runtime behavior, public APIs, dependencies, safety boundaries, or
  documentation information architecture.

## Safety Impact

None. This change affects package discovery metadata and release validation
only. It does not change source-row handling, PII boundaries, SQL access,
determinism, validation, or generated artifacts.

## Compatibility

CLI, Python, MCP, `DatasetSpec`, and artifact contracts remain unchanged. The
classifier correction aligns package metadata with the existing stable
compatibility policy.
