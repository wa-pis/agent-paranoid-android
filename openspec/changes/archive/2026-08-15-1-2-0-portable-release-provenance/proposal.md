# Change Proposal: 1-2-0-portable-release-provenance

## Summary

Publish the signed build-provenance bundle already produced for Python
distributions as a portable GitHub Release asset. Verify the local bundle
before release creation and verify the downloaded bundle again during public
release acceptance.

## Motivation

GitHub artifact attestations currently exist only behind the GitHub attestation
API. Consumers cannot retain the release evidence with the wheel or source
distribution, and OpenSSF Scorecard cannot observe the existing provenance on
the release page. Portable Sigstore evidence makes the current control usable
outside that API without adding another signer or long-lived key.

## Scope

In scope:

- Export the `actions/attest` build-provenance output as one versioned
  `*.sigstore.json` asset covering the wheel and source distribution.
- Verify both artifact digests, the tag ref, and signer workflow from that
  local bundle before release creation.
- Include the bundle in `SHA256SUMS` and the GitHub Release.
- Require exactly one downloaded bundle and repeat bundle-backed verification
  in the public-release workflow.

Out of scope:

- Changing runtime code, dependencies, Python/CLI/MCP contracts, or containers.
- Replacing GitHub artifact attestations or keyless signing.
- Mutating historical releases or their recorded checksums.
- Adding an external fuzzing service, artificial reviewers, or controls that a
  single maintainer cannot operate safely solely to raise a score.

## Safety Impact

The change affects only release metadata generated from built distributions.
It does not read source datasets or alter PII, SQL, filesystem export, MCP,
provider, generation, or determinism boundaries. Verification fails before
publication when the bundle is absent or does not bind both package digests to
the expected tag and signer workflow.

## Compatibility

Existing wheel, sdist, SBOM, checksum, PyPI, container, CLI, Python, MCP, and
dataset contracts remain compatible. The additive release asset uses the
standard Sigstore JSON bundle produced by `actions/attest` and can be ignored
by consumers that continue to verify through the GitHub API.

## Release Impact

This changes published artifact integrity and therefore requires the next
release candidate under the release policy. The implementation does not create
a tag, mutate an existing release, or publish a package.

## Completion

Completed and publicly exercised by `v1.2.0rc2` on 2026-08-15. The immutable
release evidence is recorded in `docs/release-evidence-1.2.0rc2.md`.
