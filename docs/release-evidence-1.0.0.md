# 1.0.0 Published Release Evidence

This document records the immutable public-artifact evidence for `v1.0.0`.
It is release-engineering evidence for maintainers, not an additional product
or privacy guarantee.

## Immutable Release Identity

The signed annotated tag `v1.0.0` resolves to stable release commit
`eb4ef2a5d111ef31390f0a204068369e3f934a3b`. Its acceptance manifest binds
that commit to the closed RC6 findings, exact gate URLs, approval record, and
wheel and source-distribution hashes. The accepted runtime baseline remains
RC6 commit `2b65515313281aaeb180bb95328785ef46be0202`.

The complete promotion diff received an
[AI-assisted independent review](https://github.com/wa-pis/agent-paranoid-android/issues/401)
using OpenCode with Nemotron 3 Ultra Free. The review is bound to patch
SHA-256 `9d8d9e25f00b662b845a387efd16124ca8f585ebba067cd76c0320e23f4bc686`
and confirms that the promotion changed only version/status metadata,
documentation, changelog and acceptance evidence, and generated release
metadata. This is not a human-review claim or a waiver. The reviewed changes
were merged in [PR #400](https://github.com/wa-pis/agent-paranoid-android/pull/400).

| Gate | Evidence | Result |
| --- | --- | --- |
| Exact-commit CI | [CI run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/31532608562) | Passed |
| Exact-commit containers | [Containers run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/31532608639) | Passed |
| Exact-commit documentation | [Documentation run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/31532608610) | Passed |
| Exact-commit security | [Security run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/31532608585) | Passed |
| GitHub Release, package SBOM, and attestations | [Release run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/31535172632) | Passed |
| Multi-platform GHCR images, SBOM, provenance, and signatures | [Containers run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/31535172612) | Passed |
| PyPI trusted publication and public-index verification | [Publish PyPI run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/31535349523) | Passed |
| Independent public-artifact acceptance | [Verify Published Release run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/31535631328) | Passed |

The resulting [GitHub release](https://github.com/wa-pis/agent-paranoid-android/releases/tag/v1.0.0)
and [PyPI release](https://pypi.org/project/agent-paranoid-android/1.0.0/)
were published on 2026-08-11 and remain bound to the tag above.

## Package Digests

The successful post-publish workflow verified `SHA256SUMS`, GitHub
attestations, and equality between the GitHub Release and public PyPI wheel and
source-distribution hashes. Two clean local builds from the tagged commit were
also byte-identical to these public distributions.

| Artifact | SHA-256 |
| --- | --- |
| `agent_paranoid_android-1.0.0-py3-none-any.whl` | `88644f9f266b9e146cb8d813737d4799b970ab654c7bcd3b1b0a3ad40f76ab6a` |
| `agent_paranoid_android-1.0.0.tar.gz` | `187d7a5c6e4ea34ce4fc9b08bbcd6091bcbacfb781989dde861fa979f8b809c6` |
| `sbom.cdx.json` | `07d28681809e435964cfa8c29ed2bd3b47d323ff85bf86a8731023afbe77573d` |
| `SHA256SUMS` | `e15d429e1892608656ef938aac67315872cb05c11d0534227954e8b5cd5d778f` |

## Container Digests

| Image | Multi-platform digest |
| --- | --- |
| `ghcr.io/wa-pis/agent-paranoid-android-cli:1.0.0` | `sha256:1635b23a0bfa44e3e0becb5aac33bc76d2cabd08bcecb6cfe34c457fda6692da` |
| `ghcr.io/wa-pis/agent-paranoid-android-generator-mcp:1.0.0` | `sha256:6289583e594c73cc7fd8a4567a46443fbf12d3db36714a60414c1e6fd5c7fab7` |
| `ghcr.io/wa-pis/agent-paranoid-android-trino-mcp:1.0.0` | `sha256:f4464d836f3e531a0cc780de288f36af1772338e1279203d452e2997a3acedc7` |

For each image, verification required `linux/amd64` and `linux/arm64`,
inspected the embedded SBOM, verified the GitHub provenance attestation and
keyless Cosign signature, and pulled and ran the published image under its
hardened health-check configuration.

## Public Acceptance Result

The post-publish workflow installed the exact public package in separate clean
environments for the base, `parquet`, `mcp`, `trino`, `mcp,trino`, `openai`,
and `all` profiles. It verified package identity, dependencies, public CLI
contracts, the literal README quickstart, deterministic synthetic generation,
agent approval, audit verification, public documentation, upgrade from public
`0.12.0`, and all three published containers.

The first verification attempt reached the public index before every mirror
exposed `1.0.0`, so only the `all` install reported a transient propagation
failure. The failed jobs were rerun without changing source, tag, or artifacts;
the linked latest attempt is fully green.

On 2026-08-12, a separate clean public-index smoke installed
`agent-paranoid-android[postgres]==1.0.0`, verified the package and dependency
budget, discovered the PostgreSQL profiling command, and produced two
byte-identical SQL transactions without opening a database connection. The
stable runtime is unchanged from RC6, whose independently recorded
[PostgreSQL evidence](https://github.com/wa-pis/agent-paranoid-android/issues/398)
covers the same public profile. The stable `all` job also verified the
PostgreSQL dependency in the hash-pinned public installation, and exact-commit
release gates reran the synthetic PostgreSQL and SQL regression suite without a
production database.

Together with the signed tag, exact-commit approval, and accepted Low-risk
ledger in [Known Issues](known-issues.md), these checks complete stable
`1.0.0` publication and public-artifact acceptance.
