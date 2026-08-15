# Tasks: 1-2-0-portable-release-provenance

- [x] Record the focused proposal, design, and release-supply-chain contract.
- [x] Export the existing signed provenance output under a deterministic
  `*.sigstore.json` release-asset name.
- [x] Verify the local bundle against both distributions, the tag, and the
  signer workflow before creating a release.
- [x] Include the portable bundle in checksums and release uploads.
- [x] Require exactly one public bundle and repeat bundle-backed verification
  from downloaded release assets.
- [x] Add focused workflow contract tests.
- [x] Update the roadmap, changelog, release guide, and public checklist.
- [x] Run focused lint, tests, YAML parsing, and strict documentation build.
- [x] Merge through a normal pull request with required CI green.
- [x] Exercise the contract on the next release candidate; do not mutate
  historical releases.
