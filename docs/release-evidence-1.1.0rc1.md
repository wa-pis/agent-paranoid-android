# 1.1.0rc1 Published Release Evidence

This document records the immutable public-artifact evidence for
`v1.1.0rc1`. It is release-engineering evidence for maintainers, not an
additional product or privacy guarantee.

## Immutable Release Identity

The signed annotated tag `v1.1.0rc1` resolves to release commit
`5f95ccfd3774a6d16a4a5c77d1460a8cebf5eca1`. Its acceptance manifest binds
that commit to the inherited closed RC6 findings, exact gate URLs, independent
approval record, and wheel and source-distribution hashes.

The exact commit received an
[AI-assisted independent review](https://github.com/wa-pis/agent-paranoid-android/issues/408)
under stable pseudonym `opencode-nemotron-3-ultra-free-1.1.0rc1`, using
OpenCode with Nemotron 3 Ultra Free. This is not a human-review claim or a
waiver. The review found no Critical, High, or Medium defect; its Low
observations were accepted as non-blocking for this candidate.

| Gate | Evidence | Result |
| --- | --- | --- |
| Exact-commit CI | [CI run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/31577893901) | Passed |
| Exact-commit containers | [Containers run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/31577894011) | Passed |
| Exact-commit documentation | [Documentation run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/31577893895) | Passed |
| Exact-commit security | [Security run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/31577893979) | Passed |
| Full release gate, GitHub Release, package SBOM, and attestations | [Release run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/31579203133) | Passed |
| Multi-platform GHCR images, SBOM, provenance, and signatures | [Containers run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/31579203160) | Passed |
| PyPI trusted publication and public-index verification | [Publish PyPI run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/31579370353) | Passed |
| Independent public-artifact acceptance | [Verify Published Release run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/31579591912) | Passed |

The resulting [GitHub prerelease](https://github.com/wa-pis/agent-paranoid-android/releases/tag/v1.1.0rc1)
and [PyPI release](https://pypi.org/project/agent-paranoid-android/1.1.0rc1/)
were published on 2026-08-12 and remain bound to the tag above.

## Package Digests

The successful post-publish workflow verified `SHA256SUMS`, GitHub
attestations, and equality between the GitHub Release and public PyPI wheel and
source-distribution hashes. Two local builds using the release workflow's
`SOURCE_DATE_EPOCH` were also byte-identical.

| Artifact | SHA-256 |
| --- | --- |
| `agent_paranoid_android-1.1.0rc1-py3-none-any.whl` | `b06b75cf5075506711d54876adcff4ce6a1ded56409d2f9646b471a7b9a5c245` |
| `agent_paranoid_android-1.1.0rc1.tar.gz` | `394ba45f756c0cb555bf987c7f21f1b5df5ed0d1872ac323ced0e8310463af45` |
| `sbom.cdx.json` | `e77b1aa9da617958af01315be6e0052af7eaec2f5bfa78a037cd6f4cb68252e6` |
| `SHA256SUMS` | `5985cadc426a862f6ff6af09dcb6887f26e1396801fa695faa0eee78f9c122ea` |

## Container Digests

| Image | Multi-platform digest |
| --- | --- |
| `ghcr.io/wa-pis/agent-paranoid-android-cli:1.1.0rc1` | `sha256:07bb5fe192a97ec228c4b2480d2d13934a96be5dd348070aae13057e80ce6236` |
| `ghcr.io/wa-pis/agent-paranoid-android-generator-mcp:1.1.0rc1` | `sha256:a94dc6f2976ac10d80a629e79db0669abea2a83e6a7404ead83136bfd3a3a737` |
| `ghcr.io/wa-pis/agent-paranoid-android-trino-mcp:1.1.0rc1` | `sha256:c9ef73eff974a44640f30961d56cec7b8605602213cd5eb84cefbd8db1a6f15f` |

For each image, verification required `linux/amd64` and `linux/arm64`,
inspected its SBOM, verified the GitHub provenance attestation and keyless
Cosign signature, and pulled and ran the published digest under its hardened
health-check configuration.

## Public Acceptance Result

The post-publish workflow installed the exact public package in separate clean
environments for the base, `parquet`, `mcp`, `trino`, `mcp,trino`, `openai`,
and `all` profiles. It verified package identity, dependencies, the README
quickstart, deterministic synthetic generation, agent approval, audit
verification, public documentation, upgrade from public `0.12.0`, and all
three published containers.

The first verification attempt started two MCP profile installs before every
PyPI mirror exposed the new prerelease. Those jobs reported only a transient
`No matching distribution` response. They were rerun after propagation without
changing source, tag, or artifacts; the linked latest attempt is fully green.

A separate clean public-index smoke installed
`agent-paranoid-android[gigachat]==1.1.0rc1`, verified package version and base
import, and passed `doctor --require-extra gigachat` using the local fake
capability check. It resolved no credential and made no live GigaChat call.
The exact-commit release matrix separately covered base, `gigachat`, and `all`
isolated wheels on Python 3.11 through 3.14 and the fake-SDK provider suite.

Together with the signed tag and exact-commit approval, these checks complete
`1.1.0rc1` publication and public-artifact acceptance. Promotion to stable
`1.1.0` remains a separate release decision.
