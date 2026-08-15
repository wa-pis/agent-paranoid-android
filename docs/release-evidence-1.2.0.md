# 1.2.0 Published Release Evidence

This document records the immutable public-artifact evidence for stable
release `v1.2.0`. It is release-engineering evidence for maintainers, not an
additional product or privacy guarantee.

## Immutable Release Identity

The protected signed tag `v1.2.0` resolves to exact release commit
`d56f625f88f27292443cad50cd7b338fd042436f`. Stable 1.2.0 promotes the
accepted `v1.2.0rc2` runtime without changes to application behavior, public
APIs, dependencies, workflows, containers, or security boundaries. The
promotion changes only version identity, release documentation, roadmap
status, and generated release assertions.

The promotion diff received an
[AI-assisted independent review](https://github.com/wa-pis/agent-paranoid-android/issues/444)
using OpenCode with Nemotron 3 Ultra Free. This is not a human-review claim or
a waiver. The review approved target commit
`d56f625f88f27292443cad50cd7b338fd042436f` and immutable patch SHA-256
`3533c044b77b91beb6c089bbf942a25972dfe59dd78b5260b0ec3cd50d7452b0`
with no unresolved Critical, High, or Medium finding.

| Gate | Evidence | Result |
| --- | --- | --- |
| Stable release preparation | [PR #443](https://github.com/wa-pis/agent-paranoid-android/pull/443) | Merged with required checks green |
| Exact-commit CI | [CI run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/31877567031) | Passed |
| Exact-commit containers | [Containers run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/31877567007) | Passed |
| Exact-commit documentation | [Documentation run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/31877567014) | Passed |
| Exact-commit security | [Security run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/31877567010) | Passed |
| Exact-commit OpenSSF checks | [OpenSSF run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/31877567012) | Passed |
| Full release gate, GitHub Release, SBOM, and attestations | [Release run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/31877937457) | Passed |
| Multi-platform GHCR images, provenance, and signatures | [Containers run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/31877937456) | Passed |
| PyPI Trusted Publishing and public-index verification | [Publish PyPI run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/31878045117) | Passed |
| Independent public-artifact acceptance | [Verify Published Release run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/31878175108) | Passed on attempt 2 |

The resulting [stable GitHub Release](https://github.com/wa-pis/agent-paranoid-android/releases/tag/v1.2.0)
and [PyPI release](https://pypi.org/project/agent-paranoid-android/1.2.0/)
were published on 2026-08-15 and remain bound to the signed tag above.

## Package And Evidence Digests

The release and post-publish workflows verified `SHA256SUMS`, GitHub
attestations, the portable Sigstore bundle, and equality between GitHub Release
and public PyPI distribution hashes. The downloaded bundle covered both the
wheel and source distribution at the expected tag and signer workflow.

| Artifact | SHA-256 |
| --- | --- |
| `agent_paranoid_android-1.2.0-py3-none-any.whl` | `2fc7499b50a8bda9f0b3151c62259c380bed48e1e963d1cbab6566b8f30bdf37` |
| `agent_paranoid_android-1.2.0.tar.gz` | `dccb979e5261bf18be0c75013589b1c10273db3598dbf9d9b62465fdef8d0247` |
| `agent-paranoid-android-1.2.0.sigstore.json` | `4c2b515bf611c9061d7764fa5e5e1403e2970f0ff3b2fdb6bd47bccc91af8b25` |
| `sbom.cdx.json` | `3e6f0b8c205981f465b6ad9addaa843ab593ddc6f6a651a780f74cd048434913` |
| `SHA256SUMS` | `ca401f6d7c6a903508e0ae5329824b1ddc6c674e301205e412dc3b3da8ef4427` |

## Container Digests

| Image | Multi-platform digest |
| --- | --- |
| `ghcr.io/wa-pis/agent-paranoid-android-cli:1.2.0` | `sha256:08f18ce0b253e0710d3c27f3e1b32a037f300a17cdc37880acb01a9a396fbfc8` |
| `ghcr.io/wa-pis/agent-paranoid-android-generator-mcp:1.2.0` | `sha256:ed0f406aaf44d8df5d445fdd720e3a973dbfebf59ef96d66a504f1aa5d7e7f5d` |
| `ghcr.io/wa-pis/agent-paranoid-android-trino-mcp:1.2.0` | `sha256:11f056c3f661903542b810526b3acd9844aa3d64e66a4f4edd40aab708d9a63b` |

For each image, verification required `linux/amd64` and `linux/arm64`, checked
its provenance and keyless Cosign signature, and pulled and ran the published
digest under its hardened health-check configuration.

## Public Acceptance Result

The post-publish workflow verified release assets, public PyPI hashes, public
documentation, package upgrade, deterministic quickstarts, agent approval,
audit verification, and all three signed containers. It installed the exact
public package in separate clean environments for base, `parquet`, `mcp`,
`trino`, `mcp,trino`, `openai`, and `all`.

The first attempt began while PyPI propagation was incomplete: the isolated
`parquet` job could see versions only through `1.2.0rc2`, while the later
`all` job installed `1.2.0` successfully. The complete workflow was rerun after
propagation and every job passed, including `parquet`. This was an external
index timing condition, not a package or dependency defect.
