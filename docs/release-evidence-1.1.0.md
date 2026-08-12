# 1.1.0 Published Release Evidence

This document records the immutable public-artifact evidence for stable
`v1.1.0`. It is release-engineering evidence for maintainers, not an
additional product or privacy guarantee.

## Immutable Release Identity

The protected signed tag `v1.1.0` resolves to release commit
`a536629c209878754c4250ef21a47f69e4c01cae`. Stable `1.1.0` promotes the
accepted `v1.1.0rc2` runtime at
`9ff776b8fc59ed8037f7dc5aa23d124a61eb6a90` through the allowed version- and
documentation-only path. The promotion changed no runtime behavior, public
API, dependency graph, workflow, container, or security boundary.

The exact stable commit received an
[AI-assisted independent review](https://github.com/wa-pis/agent-paranoid-android/issues/415)
using OpenCode with Nemotron 3 Ultra Free. This is not a human-review claim or
a waiver. The review approved the exact commit with no Critical, High, Medium,
or Low finding.

| Gate | Evidence | Result |
| --- | --- | --- |
| Stable promotion | [PR #414](https://github.com/wa-pis/agent-paranoid-android/pull/414) | Merged with required checks green |
| Exact-commit CI | [CI run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/31592700898) | Passed |
| Exact-commit containers | [Containers run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/31592700878) | Passed |
| Exact-commit documentation | [Documentation run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/31592700902) | Passed |
| Exact-commit security | [Security run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/31592700920) | Passed |
| Exact-commit OpenSSF checks | [OpenSSF run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/31592700942) | Passed |
| Full release gate, GitHub Release, package SBOM, and attestations | [Release run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/31594102145) | Passed |
| Multi-platform GHCR images, provenance, and signatures | [Containers run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/31594102180) | Passed |
| PyPI Trusted Publishing and public-index verification | [Publish PyPI run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/31594282182) | Passed |
| Independent public-artifact acceptance | [Verify Published Release run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/31594529752) | Passed on attempt 2 |

The resulting [GitHub release](https://github.com/wa-pis/agent-paranoid-android/releases/tag/v1.1.0)
and [PyPI release](https://pypi.org/project/agent-paranoid-android/1.1.0/)
were published on 2026-08-12 and remain bound to the tag above.

## Package Digests

The release and post-publish workflows verified `SHA256SUMS`, GitHub
attestations, and equality between the GitHub Release and public PyPI wheel and
source-distribution hashes. Two clean Linux builds outside the source tree
were byte-identical.

| Artifact | SHA-256 |
| --- | --- |
| `agent_paranoid_android-1.1.0-py3-none-any.whl` | `db467dcf4222b78834c967f6f36894c97487fa1d69c84bc6398936be1746ec06` |
| `agent_paranoid_android-1.1.0.tar.gz` | `ca996481ffa799dfea639c6dc815ff8dd5d6b80c13e0763a2c800e4e67703968` |
| `sbom.cdx.json` | `f2dc703b50d3ad36890f03bb410e91a02dd3f8e0db751a2791727d0fc936bea4` |
| `SHA256SUMS` | `a36e3b01eb6014a0f0ccb8e6b9514b4300bd1e3ee9c29760c2c02f5d6cac3917` |

## Container Digests

| Image | Multi-platform digest |
| --- | --- |
| `ghcr.io/wa-pis/agent-paranoid-android-cli:1.1.0` | `sha256:6b79f96bfd8ec0cd610e86d06711f1d4703a06be2d3e908c51f1692b052b2bc3` |
| `ghcr.io/wa-pis/agent-paranoid-android-generator-mcp:1.1.0` | `sha256:bf051374fd4adc27dbc0686bf75639e33439a8833f509b67d7c0f4c11cb71e9e` |
| `ghcr.io/wa-pis/agent-paranoid-android-trino-mcp:1.1.0` | `sha256:cce3fc3d40950d7af70bd04f79b2fa83dbd1e77e13dac83d511fcfbc30c0a6ac` |

For each image, verification required `linux/amd64` and `linux/arm64`, checked
its provenance and keyless Cosign signature, and pulled and ran the published
digest under its hardened health-check configuration.

## Public Acceptance Result

The post-publish workflow installed the exact public package in separate clean
environments for the base, `parquet`, `mcp`, `trino`, `mcp,trino`, `openai`,
and `all` profiles. It verified package identity, dependencies, the README
quickstart, deterministic synthetic generation, agent approval, audit
verification, public documentation, upgrade from public `0.12.0`, and all
three published containers.

The first attempt began the `parquet` and `mcp,trino` installs while two PyPI
index endpoints still listed only through `1.1.0rc1`. Both jobs failed with
only `No matching distribution`; all other public checks passed. The unchanged
workflow was rerun after index propagation, and attempt 2 passed every job
without changing source, tag, or artifacts.

Together with the signed tag, exact-commit approval, verified public packages,
and signed containers, these checks complete stable `1.1.0` publication and
public-artifact acceptance.
