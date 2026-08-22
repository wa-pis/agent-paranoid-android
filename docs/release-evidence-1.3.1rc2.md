# 1.3.1rc2 Published Release Evidence

This document records immutable public-artifact evidence for release candidate
`v1.3.1rc2`. It is release-engineering evidence for maintainers, not an
additional product or privacy guarantee.

## Immutable Release Identity

The protected signed tag `v1.3.1rc2` resolves to exact release commit
`78948516451591fd9774ddfacaf788cb67a9426e`. The candidate supersedes failed
`v1.3.1rc1` with an Ubuntu no-publish artifact preflight while retaining the
same application runtime, public APIs, dependencies, packaging, containers,
and security boundaries.

The exact candidate received an
[AI-assisted independent review](https://github.com/wa-pis/agent-paranoid-android/issues/477)
using OpenCode with Nemotron 3 Ultra Free. This is not a human-review claim or
a waiver. The corrected review concluded `APPROVED` with no unresolved
Critical, High, or Medium finding.

| Gate | Evidence | Result |
| --- | --- | --- |
| RC preparation | [PR #474](https://github.com/wa-pis/agent-paranoid-android/pull/474) | Merged with required checks green |
| Preflight hardening | [PR #475](https://github.com/wa-pis/agent-paranoid-android/pull/475) | Merged with required checks green |
| Exact-gate dispatch | [PR #476](https://github.com/wa-pis/agent-paranoid-android/pull/476) | Merged with required checks green |
| Exact-commit CI | [CI run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/32540741117) | Passed |
| Exact-commit containers | [Containers run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/32540741923) | Passed |
| Exact-commit documentation | [Documentation run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/32540744321) | Passed |
| Exact-commit security | [Security run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/32540742054) | Passed |
| Exact-commit OpenSSF checks | [OpenSSF run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/32540720428) | Passed |
| No-publish Ubuntu artifact preflight | [Preflight run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/32540742325) | Passed |
| Full release gate, GitHub Release, SBOM, and attestations | [Release run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/32541306733) | Passed |
| Multi-platform GHCR images, provenance, and signatures | [Containers run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/32541306704) | Passed |
| PyPI Trusted Publishing and public-index verification | [Publish PyPI run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/32541448260) | Passed |
| Independent public-artifact acceptance | [Verify Published Release run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/32541659661) | Passed |

The resulting [GitHub prerelease](https://github.com/wa-pis/agent-paranoid-android/releases/tag/v1.3.1rc2)
and [PyPI release](https://pypi.org/project/agent-paranoid-android/1.3.1rc2/)
were published on 2026-08-22 and remain bound to the signed tag above.

## Package And Evidence Digests

The release and post-publish workflows verified `SHA256SUMS`, GitHub
attestations, the portable Sigstore bundle, and equality between GitHub Release
and public PyPI distribution hashes.

| Artifact | SHA-256 |
| --- | --- |
| `agent_paranoid_android-1.3.1rc2-py3-none-any.whl` | `238cca7424af53cf3af13ebce2df1d71c7598ab3b4b0d2f6afaa702563467fc9` |
| `agent_paranoid_android-1.3.1rc2.tar.gz` | `1fb40aae5e086d602099269e47c27834651b10c8a59d902871c9e62df20e04da` |
| `agent-paranoid-android-1.3.1rc2.sigstore.json` | `f217907bd4737906508b202cf6ad28f062855e41b613a1b630feb2ddf2188cac` |
| `sbom.cdx.json` | `ab13489ff50f512bd288b6c7125fdfeb229d513ad2f0b75873fb7e502e8db72a` |
| `SHA256SUMS` | `a462c72a3454accbe2cd005b936b01df02b8032f7eaba2d1b6ec1ddbea2330e2` |

## Container Digests

| Image | Multi-platform digest |
| --- | --- |
| `ghcr.io/wa-pis/agent-paranoid-android-cli:1.3.1rc2` | `sha256:439ba7b6ae1ca11315b1cc21930ed80868ed038659b775c984c17430a5846aed` |
| `ghcr.io/wa-pis/agent-paranoid-android-generator-mcp:1.3.1rc2` | `sha256:6f266e6a999de5def9dc45f74634280f12fe7906583486e8286beaeb08e26a96` |
| `ghcr.io/wa-pis/agent-paranoid-android-trino-mcp:1.3.1rc2` | `sha256:843800ff1e9a3fc868b9bf2fed66fd07e9468890aa0462ee8159db81277a762b` |

Each image was verified for `linux/amd64` and `linux/arm64`, provenance,
keyless Cosign signature, pullability, and its hardened health check.

## Public Acceptance Result

The post-publish workflow verified release assets, public PyPI hashes, public
documentation, deterministic quickstarts, agent approval, audit verification,
and all three signed containers. It installed the exact public package in clean
base, `parquet`, `mcp`, `trino`, `mcp,trino`, `openai`, and `all` environments.
The candidate is therefore the accepted tree for a version- and
documentation-only stable `1.3.1` promotion.
