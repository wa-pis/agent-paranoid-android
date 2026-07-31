# Security Review: 2026-07-31

This review records the pre-release security and supply-chain baseline after
commit `5ed9af4`. It is a point-in-time disposition, not a replacement for the
release-candidate audit or continuous CI gates.

## Automated Evidence

| Area | Evidence | Result |
|---|---|---|
| Python dependencies | Locked, hash-verified `pip-audit`; GitHub Dependabot | No open vulnerability alerts |
| Dependency licenses | All-extras/dev environment (96 packages); docs-only environment (16 packages) | All declarations approved by the fail-closed policy |
| Source code | CodeQL `security-extended` | No open CodeQL findings |
| Secrets | GitHub secret scanning and full-history Gitleaks | No unresolved secrets |
| Containers | Trivy scan of native CLI and MCP targets | No fixable High or Critical finding |
| Supply chain | OpenSSF Scorecard | Five configuration/maturity findings reviewed below |

The release workflow also produces CycloneDX and BuildKit SBOMs, provenance,
GitHub attestations, and keyless Cosign signatures. These artifacts must be
verified again against the release-candidate digest.

## Scorecard Dispositions

### Maintained (High)

Scorecard assigns zero because the repository is less than 90 days old. This is
an age heuristic, not evidence of an unmaintained dependency or vulnerable code.

- **Disposition:** accepted, not release-blocking.
- **Mitigation:** scheduled Scorecard runs remain enabled; active releases,
  merged changes, and required CI provide current maintenance evidence.
- **Owner:** repository maintainer.
- **Revisit:** after the repository is 90 days old; reopen if the score does not
  recover automatically.

### Code-Review (High)

Scorecard found no independently approved changesets. The repository currently
has one maintainer, so requiring an independent approval would prevent that
maintainer from merging any change.

- **Disposition:** accepted single-maintainer governance risk, not
  release-blocking for 1.0.
- **Mitigation:** changes use pull requests, required status checks, immutable
  action pins, dependency review, CodeQL, secret scanning, and focused commits.
- **Owner:** repository maintainer.
- **Revisit:** immediately when a second trusted maintainer is available; then
  require one approval and dismiss stale approvals.

### Branch-Protection (High)

`main` blocks merges until required checks pass and rejects conflicting pull
requests, but it does not require an independent approver, Code Owner review,
stale-review dismissal, or last-push approval. Those controls depend on a
second reviewer and have the same one-maintainer constraint.

- **Disposition:** accepted single-maintainer governance risk, not
  release-blocking for 1.0.
- **Mitigation:** direct development uses pull requests; release, dependency,
  security, documentation, wheel, and container gates run before merge.
- **Owner:** repository maintainer.
- **Revisit:** with the first additional maintainer; enable Code Owners, one
  required approval, stale-review dismissal, and last-push approval together.

### Fuzzing (Medium)

Scorecard recognizes no external continuous fuzzing service. The project has
property-based safety tests and controlled negative scenarios, but these do not
meet Scorecard's fuzzing signal.

- **Disposition:** deferred; no unbounded binary parser or network protocol
  implementation currently justifies an external fuzzing service.
- **Owner:** repository maintainer.
- **Revisit:** before adding a custom parser, archive reader, or network-facing
  protocol implementation, or in the first post-1.0 hardening cycle.

### CII Best Practices (Low)

The project is not registered for an OpenSSF Best Practices badge. This is a
public assurance gap rather than a direct vulnerability.

- **Disposition:** deferred until after the release candidate.
- **Owner:** repository maintainer.
- **Revisit:** register the project and publish the badge during post-1.0
  governance work.

## Release Decision

No Critical or High code, dependency, secret, license, or fixable container
finding remains unresolved. The two governance findings and repository-age
heuristic are explicitly accepted with owners, mitigations, and review triggers.
Medium and Low maturity work is deferred and does not weaken runtime safety
boundaries.

Run the full audit again for `1.0.0rc1`; any new Critical or High runtime or
supply-chain finding is release-blocking until fixed or separately reviewed.
