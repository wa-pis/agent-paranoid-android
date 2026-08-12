# Release Supply Chain Specification Delta

## Added Requirements

### Requirement: Portable Distribution Provenance

The project SHALL publish cryptographically signed, portable provenance for
each wheel and source distribution alongside the corresponding GitHub Release.

#### Scenario: Distribution provenance is published

- **GIVEN** a tag-triggered build produced exactly one wheel and one source
  distribution
- **WHEN** the release workflow generates their GitHub build attestation
- **THEN** the same signed Sigstore bundle is exported as a `*.sigstore.json`
  release asset
- **AND** local bundle verification binds both distributions to their SHA-256
  digests, the release tag, and `release.yml` before publication
- **AND** the bundle digest is included in `SHA256SUMS`

#### Scenario: Published provenance is incomplete or mismatched

- **GIVEN** a public release with missing, multiple, malformed, or mismatched
  portable provenance
- **WHEN** post-publish acceptance runs
- **THEN** it fails before accepting the release
- **AND** verification uses the downloaded bundle rather than relying only on
  the GitHub attestation API
