# Design: 1-2-0-portable-release-provenance

## Approach

Give the existing build-provenance `actions/attest` step an identifier and copy
its `bundle-path` output into `dist/` under a deterministic versioned
`*.sigstore.json` name. Use `gh attestation verify --bundle` for both Python
distributions before checksums and release creation. Upload that verified
bundle with the existing release assets.

The public-release workflow downloads all assets, requires exactly one
portable bundle, validates `SHA256SUMS`, and repeats `gh attestation verify`
with the local bundle for the wheel and source distribution. Existing API-backed
attestation checks in the PyPI publication path remain unchanged as an
independent verification route.

## Data And Contracts

- New release asset:
  `agent-paranoid-android-<version>.sigstore.json`.
- The bundle is the unmodified JSON-serialized Sigstore bundle emitted by
  `actions/attest` for the wheel and source distribution.
- `SHA256SUMS` gains the bundle digest.
- The release-supply-chain capability requires bundle-backed pre-publication
  and post-publication verification.
- No package, runtime, CLI, MCP, schema, provider, or dataset contract changes.

## Failure Modes

- A missing action output or non-file bundle stops the build.
- A digest, signer workflow, source ref, certificate, or transparency-log
  mismatch stops the build before release creation.
- Missing or multiple public bundles, checksum mismatch, malformed JSON, or a
  bundle that does not cover either distribution fails post-publish acceptance.
- Historical releases remain immutable; the improved evidence begins with the
  next release built by this workflow.

## Alternatives

- Publishing only a detached `.sig` would be visible to Scorecard but would
  discard the existing SLSA provenance and require a separate signing design.
- Downloading the bundle from the API after publication would make the release
  dependent on mutable external availability and would not fail before release
  creation.
- Backfilling old releases would change their accepted asset sets and
  checksums, so it is deliberately excluded.
