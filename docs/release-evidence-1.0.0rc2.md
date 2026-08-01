# 1.0.0rc2 Published Release Evidence

This document records the immutable public-artifact evidence for
`v1.0.0rc2`. It is release-engineering evidence for maintainers, not an
additional product or privacy guarantee.

## Immutable Release Identity

The annotated tag `v1.0.0rc2` resolves to release commit
`e5030b6ae3a06885296d530a4a99f86b760118dd`. The successful post-publish
verification checked out that tag and independently resolved the same commit.
The verification workflow itself ran from `main` commit
`ac413e3e51dc6ee52a7e9230ac2f53f01ced7576`, after its checksum-path fix, and
did not create or mutate release artifacts.

| Gate | Run | Result |
| --- | --- | --- |
| GitHub Release artifacts and attestations | [Release #14](https://github.com/wa-pis/agent-paranoid-android/actions/runs/30684853180) | Passed |
| Multi-platform GHCR images | [Containers #379](https://github.com/wa-pis/agent-paranoid-android/actions/runs/30684853166) | Passed |
| PyPI trusted publication and public-index smoke | [Publish PyPI](https://github.com/wa-pis/agent-paranoid-android/actions/runs/30684911066) | Passed |
| Independent public-artifact verification | [Verify Published Release #2](https://github.com/wa-pis/agent-paranoid-android/actions/runs/30689390871) | Passed |

## Package Digests

The successful post-publish workflow verified `SHA256SUMS`, GitHub
attestations, and equality between the GitHub Release and public PyPI wheel and
source-distribution hashes.

| Artifact | SHA-256 |
| --- | --- |
| `agent_paranoid_android-1.0.0rc2-py3-none-any.whl` | `8982b0fe05dc380ac948c1b3d37eda1bd5f2211a0299549be0b77952847c9297` |
| `agent_paranoid_android-1.0.0rc2.tar.gz` | `e6b2cd8ebbc5120fa426429977f0490f3e0a9665839d755f02750d9ddd992fab` |
| `sbom.cdx.json` | `374a84c2bdc5dbd89bdc43d44a70df6667d0ec86bd4457725816b91890b4660e` |

## Container Digests

| Image | Multi-platform digest |
| --- | --- |
| `ghcr.io/wa-pis/agent-paranoid-android-cli:1.0.0rc2` | `sha256:7f2b93ce9570e2dc702d34bc098b0756ee64b13588f4eb73ede950694d5de73b` |
| `ghcr.io/wa-pis/agent-paranoid-android-generator-mcp:1.0.0rc2` | `sha256:5fa30138b86fc4d9ce9eb80742ca4e9652da6507ea523508ac5fe7f0a9fa3d02` |
| `ghcr.io/wa-pis/agent-paranoid-android-trino-mcp:1.0.0rc2` | `sha256:d53df07ea4bab935ec95592f9aa0e1f64e0a84825cf3241a62ef1d393060574c` |

For each image, the verification gate resolved the version tag to the recorded
digest, required both `linux/amd64` and `linux/arm64`, inspected the embedded
SBOM, verified the GitHub attestation and keyless Cosign signature, and ran the
published image with the hardened non-root, read-only, network-disabled health
configuration.

## Public Smoke Result

The independent verification installed the exact public PyPI wheel with hashes
in a clean environment, ran the installed-package contract check, `doctor`, and
the bundled deterministic demo, and confirmed that its manifest reports
synthetic output, no copied source rows, and successful validation. It also
confirmed that the public documentation serves both the quickstart success
marker and version `1.0.0rc2`.

The changes after `v1.0.0rc1` were limited to the RC2 container-tag correction,
the post-publish verification gate, and the checksum-layout correction required
by its first run. No feature work entered the candidate. The exact-commit full
security review and dispositions remain a separate open gate.
