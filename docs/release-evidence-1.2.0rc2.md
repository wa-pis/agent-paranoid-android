# 1.2.0rc2 Published Release Evidence

This document records the immutable public-artifact evidence for preview
release `v1.2.0rc2`. It is release-engineering evidence for maintainers, not an
additional product or privacy guarantee.

## Immutable Release Identity

The protected signed tag `v1.2.0rc2` resolves to exact release commit
`4473774ebb9dad7e53b25401021757c2863f877c`. RC2 supersedes the published but
unaccepted `v1.2.0rc1`: application runtime, public APIs, dependencies,
packaging, containers, and security boundaries are unchanged. The RC2 delta
only corrects the post-publish portable-bundle checksum layout and updates
release identity and documentation.

The exact commit received an
[AI-assisted independent review](https://github.com/wa-pis/agent-paranoid-android/issues/441)
using OpenCode with Nemotron 3 Ultra Free. This is not a human-review claim or
a waiver. The review approved target commit
`4473774ebb9dad7e53b25401021757c2863f877c` and immutable patch SHA-256
`8897c082bad9c6d99dd28ccbb32ea8311335aa9d97b120662dbbd0ca1d911bc1`
with no unresolved Critical, High, or Medium finding.

| Gate | Evidence | Result |
| --- | --- | --- |
| Portable-bundle verifier fix | [PR #439](https://github.com/wa-pis/agent-paranoid-android/pull/439) | Merged with required checks green |
| RC2 release preparation | [PR #440](https://github.com/wa-pis/agent-paranoid-android/pull/440) | Merged with required checks green |
| Exact-commit CI | [CI run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/31872694228) | Passed |
| Exact-commit containers | [Containers run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/31872694235) | Passed |
| Exact-commit documentation | [Documentation run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/31872694227) | Passed |
| Exact-commit security | [Security run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/31872694214) | Passed |
| Exact-commit OpenSSF checks | [OpenSSF run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/31872694230) | Passed |
| Full release gate, GitHub Release, SBOM, and attestations | [Release run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/31872986712) | Passed |
| Multi-platform GHCR images, provenance, and signatures | [Containers run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/31872986706) | Passed |
| PyPI Trusted Publishing and public-index verification | [Publish PyPI run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/31873093279) | Passed |
| Independent public-artifact acceptance | [Verify Published Release run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/31873544030) | Passed |

The resulting [GitHub prerelease](https://github.com/wa-pis/agent-paranoid-android/releases/tag/v1.2.0rc2)
and [PyPI release](https://pypi.org/project/agent-paranoid-android/1.2.0rc2/)
were published on 2026-08-15 and remain bound to the signed tag above.

## Package And Evidence Digests

The release and post-publish workflows verified `SHA256SUMS`, GitHub
attestations, the portable Sigstore bundle, and equality between GitHub Release
and public PyPI distribution hashes. The downloaded bundle covered both the
wheel and source distribution at the expected tag and signer workflow.

| Artifact | SHA-256 |
| --- | --- |
| `agent_paranoid_android-1.2.0rc2-py3-none-any.whl` | `324b589e1c455b2950e70458c984727c9effc75edbb036b30744cd84f729f983` |
| `agent_paranoid_android-1.2.0rc2.tar.gz` | `e45edbeaaacbb884a86a97622ed3d77c11eb3400199e1ff7d851600bbea9c3fa` |
| `agent-paranoid-android-1.2.0rc2.sigstore.json` | `175a5e855a66fa019995713a33742bca05b3eb03cbc1a85ea2cf35ef65b3d984` |
| `sbom.cdx.json` | `34d46c7936f767c8f6054f91accb3338564a16b2b80d6a2b12f2dff8a9f5db52` |
| `SHA256SUMS` | `131fb6e92f005c0d8df368c44767740f5ffeeaced5491913c01e95f2d52cf90e` |

## Container Digests

| Image | Multi-platform digest |
| --- | --- |
| `ghcr.io/wa-pis/agent-paranoid-android-cli:1.2.0rc2` | `sha256:f3cfca41f79eb856b0b506ebbdccd196bd71a5385fb64c2e05f85702c379aaa8` |
| `ghcr.io/wa-pis/agent-paranoid-android-generator-mcp:1.2.0rc2` | `sha256:d7ec3bbc488c2ab7bde147fde799af30801222d69e633212a14433d94deca98e` |
| `ghcr.io/wa-pis/agent-paranoid-android-trino-mcp:1.2.0rc2` | `sha256:e7078aea452e33b66cac5d7b55839bf8b6f34851ef644358965b2acd7e4fade5` |

For each image, verification required `linux/amd64` and `linux/arm64`, checked
its provenance and keyless Cosign signature, and pulled and ran the published
digest under its hardened health-check configuration.

## Public Acceptance Result

The post-publish workflow verified the downloaded checksum layout, the single
portable bundle, both package attestations, public PyPI hashes, and public
documentation. It installed the exact public package in separate clean
environments for base, `parquet`, `mcp`, `trino`, `mcp,trino`, `openai`, and
`all`; exercised upgrade from public `0.12.0`, deterministic quickstarts,
agent approval, and audit verification; and verified all three signed
containers.

Every job passed on the first RC2 post-publish attempt. This completes RC2
publication, portable-provenance acceptance, and the remaining OpenSpec task.
