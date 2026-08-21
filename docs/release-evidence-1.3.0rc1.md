# 1.3.0rc1 Published Release Evidence

This document records immutable public-artifact evidence for release candidate
`v1.3.0rc1`. It is release-engineering evidence for maintainers, not an
additional product or privacy guarantee.

## Immutable Release Identity

The protected signed tag `v1.3.0rc1` resolves to exact release commit
`26ce1ccb54a3a5f336153454ab82e4af5d67b89b`. The candidate contains the
reviewed JDBC-style endpoint, qualified column wildcard, and aggregate-only SQL
query-source changes planned for the `1.3.0` feature line.

The exact candidate received an
[AI-assisted independent review](https://github.com/wa-pis/agent-paranoid-android/issues/465)
using OpenCode with Nemotron 3 Ultra Free. This is not a human-review claim or
a waiver. The review concluded `APPROVED` with no unresolved Critical, High, or
Medium finding.

| Gate | Evidence | Result |
| --- | --- | --- |
| RC preparation | [PR #464](https://github.com/wa-pis/agent-paranoid-android/pull/464) | Merged with required checks green |
| Exact-commit CI | [CI run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/32287050451) | Passed |
| Exact-commit containers | [Containers run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/32287050419) | Passed |
| Exact-commit documentation | [Documentation run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/32287050396) | Passed |
| Exact-commit security | [Security run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/32287050208) | Passed |
| Exact-commit OpenSSF checks | [OpenSSF run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/32287050352) | Passed |
| Full release gate, GitHub Release, SBOM, and attestations | [Release run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/32413664083) | Passed |
| Multi-platform GHCR images, provenance, and signatures | [Containers run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/32413664081) | Passed |
| PyPI Trusted Publishing and public-index verification | [Publish PyPI run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/32413920659) | Passed |
| Independent public-artifact acceptance | [Verify Published Release run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/32416745861) | Passed |

The resulting [GitHub Release](https://github.com/wa-pis/agent-paranoid-android/releases/tag/v1.3.0rc1)
and [PyPI release](https://pypi.org/project/agent-paranoid-android/1.3.0rc1/)
were published on 2026-08-21 and remain bound to the signed tag above.

## Package And Evidence Digests

The release and post-publish workflows verified `SHA256SUMS`, GitHub
attestations, the portable Sigstore bundle, and equality between GitHub Release
and public PyPI distribution hashes.

| Artifact | SHA-256 |
| --- | --- |
| `agent_paranoid_android-1.3.0rc1-py3-none-any.whl` | `60b7fdabe785fc25b9fadc4edaba431e1c42c212cbc9ce6beb102baa2d9a1124` |
| `agent_paranoid_android-1.3.0rc1.tar.gz` | `c59d5eae2de902487bccf2d38ae2c3651957e6d5ef5b36000d8176f8e2d456ea` |
| `agent-paranoid-android-1.3.0rc1.sigstore.json` | `2e48bf7449888aa90b41afbaa692a95cfae159e53051a81bbfa07cde94310ea0` |
| `sbom.cdx.json` | `a5bd5fa54cc1e91aa4fcb5b3ae87be724cb38e0b4af4025436dadc546c1fdf73` |
| `SHA256SUMS` | `e4850ca48671b36d74157d8d35bda1bbce96da8adc18cb8316aaeadb39dd34fd` |

## Public Acceptance Result

The post-publish workflow verified release assets, public PyPI hashes, public
documentation, package installation profiles, deterministic smoke workflows,
and the published signed containers. The candidate is therefore the accepted
runtime baseline for a version- and documentation-only stable `1.3.0`
promotion.
