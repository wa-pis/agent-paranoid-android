# 1.3.0 Published Release Evidence

This document records the immutable public-artifact evidence for stable
release `v1.3.0`. It is release-engineering evidence for maintainers, not an
additional product or privacy guarantee.

## Immutable Release Identity

The protected signed tag `v1.3.0` resolves to exact release commit
`99148f6b4ec2f910af5c3fa83dab8c43c46edd90`. Stable 1.3.0 promotes the
accepted `v1.3.0rc1` runtime at
`26ce1ccb54a3a5f336153454ab82e4af5d67b89b` without changes to application
behavior, public APIs, dependencies, workflows, containers, or security
boundaries. The promotion changes only version identity, release
documentation, roadmap status, release evidence, and generated documentation
assertions.

The promotion diff received an
[AI-assisted independent review](https://github.com/wa-pis/agent-paranoid-android/issues/467)
using OpenCode with Nemotron 3 Ultra Free. This is not a human-review claim or
a waiver. The review approved target commit
`99148f6b4ec2f910af5c3fa83dab8c43c46edd90` with no unresolved Critical, High,
or Medium finding.

| Gate | Evidence | Result |
| --- | --- | --- |
| Stable release preparation | [PR #466](https://github.com/wa-pis/agent-paranoid-android/pull/466) | Merged with required checks green |
| Exact-commit CI | [CI run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/32431998885) | Passed |
| Exact-commit containers | [Containers run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/32431998892) | Passed |
| Exact-commit documentation | [Documentation run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/32431998943) | Passed |
| Exact-commit security | [Security run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/32431998922) | Passed |
| Exact-commit OpenSSF checks | [OpenSSF run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/32431998887) | Passed |
| Full release gate, GitHub Release, SBOM, and attestations | [Release run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/32432854513) | Passed |
| Multi-platform GHCR images, provenance, and signatures | [Containers run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/32432854514) | Passed |
| PyPI Trusted Publishing and public-index verification | [Publish PyPI run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/32433053417) | Passed |
| Independent public-artifact acceptance | [Verify Published Release run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/32433304639) | Passed on attempt 2 |

The resulting [stable GitHub Release](https://github.com/wa-pis/agent-paranoid-android/releases/tag/v1.3.0)
and [PyPI release](https://pypi.org/project/agent-paranoid-android/1.3.0/)
were published on 2026-08-21 and remain bound to the signed tag above.

## Package And Evidence Digests

The release and post-publish workflows verified `SHA256SUMS`, GitHub
attestations, the portable Sigstore bundle, and equality between GitHub Release
and public PyPI distribution hashes. The downloaded public assets independently
matched these SHA-256 values:

| Artifact | SHA-256 |
| --- | --- |
| `agent_paranoid_android-1.3.0-py3-none-any.whl` | `65381f8b7f87e4cdab432db97ce403ead57bc5825a187ad333d60dbe9bc7c81f` |
| `agent_paranoid_android-1.3.0.tar.gz` | `85413ac926d2f1e179771b61803c4b0103be64d6215053877c821349b29e2541` |
| `agent-paranoid-android-1.3.0.sigstore.json` | `7dc687082008e3fa80096ba36817ca7f86cf3f4bd5c9f8ebf22bbcafe176b2be` |
| `sbom.cdx.json` | `b2cbd9abd7f4e8f180670b535b3c9a8a0b53f120f8a40175e300ad96f70364cf` |
| `SHA256SUMS` | `d4fd42ced2c6d63c1ec095a233cd559ce5dbf65c9aa4a1fea451dd9a52e2f64f` |

## Container Digests

| Image | Multi-platform digest |
| --- | --- |
| `ghcr.io/wa-pis/agent-paranoid-android-cli:1.3.0` | `sha256:272dfe30643831a8666134bf619e9d1488626c136e1d6c8a5299e203fb701b37` |
| `ghcr.io/wa-pis/agent-paranoid-android-generator-mcp:1.3.0` | `sha256:ae9f7f90e68afbb35d5783b819a5d33e91e763ed603280bc150a15eb7a04f964` |
| `ghcr.io/wa-pis/agent-paranoid-android-trino-mcp:1.3.0` | `sha256:4912b1eae16d7c20c6c2d439c24749bbaa89bccf04760e98e1d7e2b169ba2dc6` |

For each image, verification required `linux/amd64` and `linux/arm64`, checked
its provenance and keyless Cosign signature, and pulled and ran the published
digest under its hardened health-check configuration.

## Public Acceptance Result

The post-publish workflow verified release assets, public PyPI hashes, public
documentation, package upgrade, deterministic quickstarts, agent approval,
audit verification, and all three signed containers. It installed the exact
public package in separate clean environments for base, `parquet`, `mcp`,
`trino`, `mcp,trino`, `openai`, and `all`.

The first attempt started before the release had reached every PyPI index edge:
the isolated `parquet` job could see versions only through `1.3.0rc1`, while
the other public checks passed. After propagation, the complete workflow was
rerun and every job passed, including `parquet`. This was an external index
timing condition, not a package or dependency defect. The first attempt is
retained as [timing evidence](https://github.com/wa-pis/agent-paranoid-android/actions/runs/32433198515).
