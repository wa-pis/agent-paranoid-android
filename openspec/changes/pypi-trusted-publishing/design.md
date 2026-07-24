# Design: pypi-trusted-publishing

## Approach

Use a reusable workflow called explicitly after the GitHub Release job, plus a
manual recovery trigger. The workflow retrieves the wheel and sdist from that
release, verifies their tag-bound build provenance, validates the embedded
project name and version with a standard-library helper, and invokes the
official PyPA publish action with Trusted Publishing.

## Trust Boundaries

- GitHub Release tags and assets are maintainer-controlled inputs.
- Both distributions must have provenance from `release.yml` at the selected
  tag and a GitHub-hosted runner.
- The publish job receives a short-lived OIDC identity, not a stored secret.
- Artifact download and validation run in a separate job without OIDC access.
- The OIDC-enabled job executes no repository scripts or shell commands.
- The `pypi` environment and PyPI publisher configuration bind the identity to
  this repository and workflow filename.
- The release workflow calls the publication workflow explicitly after the
  GitHub Release job succeeds, avoiding event suppression for releases created
  with the repository `GITHUB_TOKEN`.
- Only one wheel and one sdist with matching metadata are accepted.

## Failure Modes

Missing or draft releases, malformed tags, extra files, symlinks, oversized
archives, malformed package metadata, identity mismatches, and duplicate PyPI
versions fail before or during publication. Duplicate uploads are not ignored.

## First Publication

Because `v0.5.0` predates this workflow, a manual dispatch can publish its
existing GitHub Release assets after the pending Trusted Publisher is created.
Future release runs invoke publication automatically.
