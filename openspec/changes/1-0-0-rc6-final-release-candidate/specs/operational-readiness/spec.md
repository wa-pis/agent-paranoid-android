# RC6 Operational Readiness Delta

## ADDED Requirements

### Requirement: Pull Request Classification Cannot Suppress Required Checks

CI SHALL NOT trust change-classification code supplied by the pull request to
decide whether security, dependency, quality, or container checks run. The
classifier SHALL come from a trusted base revision or equivalent trusted path
filter, and changes to classifier/workflow/dependency/build/release/configuration
paths SHALL force the heavy checks.

#### Scenario: Pull request changes the classifier

- **GIVEN** a pull request modifies the change classifier or a CI control path
- **WHEN** CI determines the required checks
- **THEN** all security, dependency, quality, packaging, and container checks run
- **AND** the pull request cannot make them appear green by returning a
  documentation-only result

### Requirement: Release Publication Is Bound To Accepted Source

Release and container publication SHALL require a signed immutable tag that
resolves to the reviewed commit digest and a machine-readable RC acceptance
manifest whose release identity, findings disposition, approvals, artifact
digests, and gate results match the tag. Public profile verification SHALL use
hash-pinned installation for the verified wheel.

#### Scenario: Tag points to an unaccepted commit

- **GIVEN** a version-matching tag does not resolve to the reviewed accepted
  commit or has no valid signature
- **WHEN** release publication starts
- **THEN** the workflow fails before build, attestation, signing, PyPI, or
  container publication

#### Scenario: RC acceptance is incomplete

- **GIVEN** an RC acceptance manifest contains an unchecked release-blocking
  item, stale commit identity, missing approval, or mismatched artifact digest
- **WHEN** stable or prerelease publication is requested
- **THEN** the workflow fails closed
- **AND** public install verification uses `--require-hashes` against the
  reviewed artifact set

### Requirement: Filesystem Publication And Diagnostic Output Are Hardened

Artifact publication and overwrite-capable CLI paths SHALL use one centralized
path policy, reject symlink components, and revalidate the destination with
no-follow descriptor or inode checks before publication and cleanup. CLI and
log presenters SHALL escape and bound untrusted metadata, paths, and error
text so control characters cannot forge terminal or log records.

#### Scenario: Destination is swapped during publication

- **GIVEN** a local attacker replaces a validated path component with a
  symlink after validation
- **WHEN** publication, hashing, overwrite, or cleanup proceeds
- **THEN** the operation fails closed without reading or writing outside the
  approved root
- **AND** the failure is bounded and does not expose the attacker-controlled
  path or error text

### Requirement: Deployed Release Controls Have Evidence

RC6 acceptance SHALL record evidence for the deployed branch and tag rulesets,
required checks, and PyPI Trusted Publisher approvals. Repository workflow
source and local simulations alone SHALL NOT be treated as proof that the
external release controls are active.

#### Scenario: External release control evidence is missing

- **GIVEN** a release candidate has no verifiable external settings evidence
- **WHEN** the acceptance manifest is evaluated
- **THEN** the manifest remains incomplete and publication or stable promotion
  fails closed
