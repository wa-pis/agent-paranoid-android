# Security Review: 1.0.0rc2

This review records the final security and supply-chain disposition for
annotated tag `v1.0.0rc2`, which resolves to commit
`e5030b6ae3a06885296d530a4a99f86b760118dd`. It supersedes the pre-RC review
for the candidate decision while retaining that document as historical
evidence.

## Exact-Commit Evidence

| Area | Evidence | Result |
| --- | --- | --- |
| Full CI, dependencies, licenses, typing, tests, and wheel | [CI run 30684756448](https://github.com/wa-pis/agent-paranoid-android/actions/runs/30684756448) | Passed on the exact RC commit |
| CodeQL and full-history secret scan | [Security run 30684756459](https://github.com/wa-pis/agent-paranoid-android/actions/runs/30684756459) | Passed; no open CodeQL or secret finding |
| OpenSSF Scorecard | [Scorecard run 30684756454](https://github.com/wa-pis/agent-paranoid-android/actions/runs/30684756454) | Passed; one Medium maturity finding dispositioned below |
| Native multi-platform container scans and publication | [Containers run 30684853166](https://github.com/wa-pis/agent-paranoid-android/actions/runs/30684853166) | Passed; no unresolved fixable High or Critical finding |
| Package build, release gate, SBOM, provenance, and attestations | [Release run 30684853180](https://github.com/wa-pis/agent-paranoid-android/actions/runs/30684853180) | Passed for the exact tag |
| Public PyPI publication and installation | [PyPI run 30684911066](https://github.com/wa-pis/agent-paranoid-android/actions/runs/30684911066) | Passed |
| Independent public package, docs, and GHCR verification | [Published-release run 30689390871](https://github.com/wa-pis/agent-paranoid-android/actions/runs/30689390871) | Passed |

The Scorecard artifact digest is
`sha256:9abd8a54143398b7064dbf330a3ab89ad6e0cd686444c8002f3931b4dd281525`.
The immutable package and container digests are recorded in the
[RC2 published-release evidence](release-evidence-1.0.0rc2.md).

GitHub dependency, CodeQL, and secret-scanning dashboards were reviewed after
the exact-commit runs. Dependabot had no open alert, CodeQL had no open alert,
and secret scanning reported no secret. The only open code-scanning item was
the Scorecard finding below.

## Finding Inventory

| Severity | Open findings | Release disposition |
| --- | ---: | --- |
| Critical | 0 | None |
| High | 0 | None |
| Medium | 1 | Accepted with owner, mitigation, and revisit date |
| Low | 0 | None |

## Accepted Medium Finding

### Scorecard SAST coverage

[Scorecard alert 10](https://github.com/wa-pis/agent-paranoid-android/security/code-scanning/10)
reports a SAST score of 8 because 14 of 30 sampled commits had a recognized
SAST run.

- **Disposition:** accepted as a non-release-blocking CI coverage and maturity
  risk. It does not report a vulnerable code path in the candidate.
- **Rationale:** documentation-only changes intentionally skip heavy CodeQL
  execution. Code-affecting paths remain classified fail closed and run
  CodeQL; the exact RC commit passed the `security-extended` query suite.
- **Mitigation:** keep the path classifier and no-op required check covered by
  tests, retain CodeQL for code-affecting changes, and keep scheduled Scorecard
  scans enabled.
- **Owner:** repository maintainer (`@wa-pis`).
- **Revisit date:** 2026-11-01.
- **Revisit triggers:** review immediately if a code-affecting change can merge
  without CodeQL, path classification is broadened, the Scorecard SAST score
  falls below 8, or repository governance gains another maintainer.

The earlier Maintained, Code-Review, Branch-Protection, Fuzzing, and CII
Scorecard observations are retained in the
[pre-RC review](security-review-2026-07-31.md). They are not open findings in
the exact-RC2 scanner result and are therefore not carried forward as current
candidate findings.

## Release Decision

No unresolved Critical or High code, dependency, secret, license, container,
or supply-chain finding remains for `v1.0.0rc2`. The one current Medium
maturity risk has an explicit owner, rationale, mitigation, revisit date, and
revisit triggers. The candidate passes the security-hardening gate; stable
release still requires the remaining public end-to-end acceptance work and a
separate verified release stage.
