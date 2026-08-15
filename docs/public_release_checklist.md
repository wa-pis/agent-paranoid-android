# Public Release Checklist

Use this checklist before making the repository public or cutting the first
public release.

## Repository Content

- Confirm `LICENSE`, `SECURITY.md`, `CONTRIBUTING.md`, README, changelog, and
  architecture diagrams are present.
- Confirm checked-in fixtures are synthetic and use reserved/example domains,
  phone ranges, and hostnames.
- Run a secret scan over the working tree and reachable Git history.
- Confirm author and committer emails are public-safe.
- Confirm no local paths, private hostnames, production table names, or company
  identifiers remain in docs, examples, or tests.

## Quality Gates

Run:

```bash
scripts/check_release.sh
python3 -m pip wheel --no-deps . -w /tmp/agent-paranoid-android-wheel
```

The release gate must pass before publishing. The wheel build confirms package
metadata and entry points are valid.

For a release containing GigaChat, also install isolated base, `gigachat`, and
`all` wheels on every supported Python version. Run
`doctor --require-extra gigachat` and the fake-SDK provider suite with network
access and credentials absent. Any live GigaChat smoke is separate, manual,
synthetic-only, and never a required release gate.

Review the latest [RC2 security review](security-review-2026-08-01-rc2.md) and
repeat its automated evidence collection against the release commit.

## GitHub Settings

Enable or verify these repository settings after publishing:

- Secret scanning and push protection.
- Dependabot alerts.
- Dependabot security updates.
- GitHub private vulnerability reporting.
- Branch protection for `main`.
- Required CI status checks before merge.
- Require linear history if the project will avoid merge commits.
- Require verified signed commits on protected branches and reject unsigned
  commits at the merge gate.
- Disallow force-pushes to protected branches after the initial history cleanup.
- Create a `pypi` environment for the tokenless publish job.
- Configure a matching PyPI Trusted Publisher for
  `wa-pis/agent-paranoid-android`, workflow `publish-pypi.yml`, environment
  `pypi`.

## Maintainer Identity

- Upload the public SSH signing key to GitHub as an SSH signing key.
- Verify that new local commits show the GitHub `Verified` badge.
- Use `onepis2word@gmail.com` for author and committer identity unless a more
  suitable public noreply address is configured.

## Release Notes

Before creating a tag:

- Move relevant `CHANGELOG.md` entries from `Unreleased` to the release version.
- Mention safety guarantees and known limitations.
- Include upgrade or migration notes when CLI, MCP, schema, or artifact formats
  change.
- Use `1.1.0rc1` as the new minor release candidate for the GigaChat addition
  because it changes dependencies, packaging, public CLI behavior, and an
  external security boundary; documentation alone does not require another
  candidate.
- Use `1.1.0rc2` for the reviewed CLI automation and artifact-integrity change
  because it adds a public command and JSON contract and changes runtime error,
  exit-code, and overwrite behavior. Re-run base/optional entrypoint, JSON,
  cancellation, help-width, completion, and isolated-wheel gates. Do not tag
  or publish it from the implementation PR.
- Promote stable `1.1.0` only from the accepted RC2 runtime with the documented
  version- and documentation-only diff. Derive wheel and sdist hashes in Linux
  before creating the protected stable tag.
- Use `1.2.0rc2` to supersede the published RC1 whose post-publish checksum
  verification exposed a portable-bundle staging mismatch. Require exact-commit
  approval and verify the public `*.sigstore.json` bundle against both Python
  distributions before considering stable `1.2.0`.
- Promote stable `1.2.0` only through a version- and documentation-only diff
  from the publicly accepted RC2 runtime.
- Avoid publishing exploit details before fixes are available.
- Sign the version tag and verify it locally before pushing.
- Confirm the tag-triggered release workflow publishes wheel, source
  distribution, CycloneDX SBOM, SHA-256 checksums, provenance, and SBOM
  attestations.
- Confirm the GitHub Release includes exactly one `*.sigstore.json` build
  provenance bundle, that its checksum is recorded, and that the downloaded
  bundle verifies both distributions against the tag and `release.yml`.
- Confirm the release workflow invokes the PyPI workflow after creating the
  GitHub Release and uploads the same wheel and source distribution with
  verified tag-bound provenance, Trusted Publishing, and publish attestations.
- Confirm the container workflow publishes separate amd64/arm64 CLI, generator
  MCP, and Trino MCP manifests to GHCR.
- Verify each image digest has BuildKit SBOM/provenance, a GitHub attestation,
  and a valid keyless Cosign signature from `containers.yml`.
- Run `python scripts/check_dependency_licenses.py` in the locked all-extras and
  documentation environments. Investigate every unknown or unapproved license;
  do not bypass the allowlist for a release.
- Confirm all GHCR packages intended for public use are public and inherit
  repository access.
- Dispatch `Verify Published Release` for the immutable release tag and retain
  the successful run URL, exact commit, package hashes, and three image digests
  in the release evidence. Confirm its public-wheel agent approval and audit
  verification steps also pass without repository fixtures.
