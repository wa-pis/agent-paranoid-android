# 1.0.0rc5 Published Release Evidence

This document records the immutable public-artifact evidence for
`v1.0.0rc5`. It is release-engineering evidence for maintainers, not an
additional product or privacy guarantee.

## Immutable Release Identity

The annotated tag `v1.0.0rc5` resolves to release commit
`9e6e55fa6eeceab925e4432dcbb147de9c88f201`. The independent post-publish
verification checked out that tag and resolved the same commit.

| Gate | Run | Result |
| --- | --- | --- |
| Full release gate, GitHub Release, package SBOM, and attestations | [Release #17](https://github.com/wa-pis/agent-paranoid-android/actions/runs/31274057391) | Passed |
| PyPI trusted publication and public-index verification | [Publish PyPI #16](https://github.com/wa-pis/agent-paranoid-android/actions/runs/31274142268) | Passed |
| Multi-platform GHCR images, SBOM, provenance, and signatures | [Containers #715](https://github.com/wa-pis/agent-paranoid-android/actions/runs/31274057394) | Passed |
| Independent public-artifact acceptance | [Verify Published Release #10](https://github.com/wa-pis/agent-paranoid-android/actions/runs/31274217410) | Passed |

The resulting [GitHub prerelease](https://github.com/wa-pis/agent-paranoid-android/releases/tag/v1.0.0rc5)
was published on 2026-08-08 and remains bound to the tag above.

## Package Digests

The successful post-publish workflow verified `SHA256SUMS`, GitHub
attestations, and equality between the GitHub Release and public PyPI wheel and
source-distribution hashes.

| Artifact | SHA-256 |
| --- | --- |
| `agent_paranoid_android-1.0.0rc5-py3-none-any.whl` | `f4f04d23b70f9d9d7997f5f4ecfdac1207007f07ff30ec7f1e9155c4be841cbc` |
| `agent_paranoid_android-1.0.0rc5.tar.gz` | `4001fea17f4d6312cec635152072e731c0b9df2b76a97b9b1ef94a4010309a79` |
| `sbom.cdx.json` | `5beda390044a660ee0adadd33efd5c1217aea8f0634a1694bb9c342ed6dbfb91` |
| `SHA256SUMS` | `10bdc159d12c8c067826edf0efa14942f3e54bbf8e09635f143bd6a919b7b620` |

## Container Digests

| Image | Multi-platform digest |
| --- | --- |
| `ghcr.io/wa-pis/agent-paranoid-android-cli:1.0.0rc5` | `sha256:3ff31a229a7b0e0ecbd125e667a21346e9d1f0256c8d2f693439e04d170c46ac` |
| `ghcr.io/wa-pis/agent-paranoid-android-generator-mcp:1.0.0rc5` | `sha256:0cdeb0f3ab68ec488898d8cffc8999d2cebfaadfb57d3e8f7f68a60a0c494989` |
| `ghcr.io/wa-pis/agent-paranoid-android-trino-mcp:1.0.0rc5` | `sha256:3c46fe8168fafb40d9142cde8e5f39350c890b2722ae40f297528202659d60c6` |

For each image, verification resolved the version tag to the recorded digest,
required `linux/amd64` and `linux/arm64`, inspected the embedded SBOM, verified
the GitHub attestation and keyless Cosign signature, and pulled and ran the
published image under the hardened health-check configuration.

## Public Acceptance Result

Verification run #10 installed the exact public package in separate clean
environments for the base, `parquet`, `trino`, `mcp`, `all`, `openai`, and
`mcp,trino` profiles. It checked the installed version and dependencies and
ran the applicable public CLI contract for every profile.

The package job independently matched public PyPI hashes to the GitHub Release,
installed the hash-pinned wheel, upgraded from public version `0.12.0`, and ran
the literal README quickstart. It also completed the public agent approval and
signed audit verification using only bundled synthetic inputs, then confirmed
that the published documentation names version `1.0.0rc5`.

Together with the exact-tag full release gate, advisor benchmark, and
independent security review, this closes the RC5 acceptance gates. Stable
promotion must use this immutable RC5 source tree and the allowlisted
release-only diff in the release process.
