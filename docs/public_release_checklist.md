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

## GitHub Settings

Enable or verify these repository settings after publishing:

- Secret scanning and push protection.
- Dependabot alerts.
- Dependabot security updates.
- GitHub private vulnerability reporting.
- Branch protection for `main`.
- Required CI status checks before merge.
- Require linear history if the project will avoid merge commits.
- Require signed commits if all maintainers have signing keys configured.
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
- Avoid publishing exploit details before fixes are available.
- Sign the version tag and verify it locally before pushing.
- Confirm the tag-triggered release workflow publishes wheel, source
  distribution, CycloneDX SBOM, SHA-256 checksums, provenance, and SBOM
  attestations.
- Confirm the release workflow invokes the PyPI workflow after creating the
  GitHub Release and uploads the same wheel and source distribution with
  verified tag-bound provenance, Trusted Publishing, and publish attestations.
