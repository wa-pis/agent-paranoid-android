# Change Proposal: pypi-trusted-publishing

## Summary

Publish verified GitHub Release distributions to PyPI through a dedicated
Trusted Publishing workflow using short-lived GitHub OIDC credentials.

## Motivation

Release wheels currently exist only as GitHub assets. Users cannot install the
package from the standard Python package index, and maintainers would otherwise
need to manage a long-lived PyPI API token.

## Scope

In scope:

- release-triggered and manual recovery publication;
- explicit invocation after GitHub Release creation;
- exact published-release wheel and sdist download;
- tag-bound release provenance verification;
- distribution identity validation before upload;
- a scoped GitHub `pypi` environment and job-level OIDC permission;
- PyPI setup and release documentation.

Out of scope:

- TestPyPI;
- password or token-based uploads;
- rebuilding distributions in the privileged publish job;
- tolerating duplicate uploads.

## Safety Impact

The preparation job has only `contents: read` and `attestations: read`; the
publishing job has only `actions: read` and `id-token: write`. It consumes
verified artifacts from the unprivileged preparation job and uses
immutable-pinned official artifact and PyPA actions. It executes no repository
code or shell commands. No long-lived PyPI credential is stored in GitHub.

## Compatibility

Runtime behavior and package contents are unchanged. Existing GitHub Releases
remain available, while PyPI becomes an additional distribution channel.
