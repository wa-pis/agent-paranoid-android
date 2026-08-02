# 1.0.0rc4 Published Release Evidence

This document records the immutable public-artifact evidence for
`v1.0.0rc4`. It is release-engineering evidence for maintainers, not an
additional product or privacy guarantee.

## Immutable Release Identity

The annotated tag `v1.0.0rc4` resolves to release commit
`33073c0abde75fa7cb200bc1d7e4748ab7b2f3ec`. The independent post-publish
verification checked out that tag and resolved the same commit.

| Gate | Run | Result |
| --- | --- | --- |
| GitHub Release artifacts and attestations | [Release #16](https://github.com/wa-pis/agent-paranoid-android/actions/runs/30734941005) | Passed |
| Multi-platform GHCR images | [Containers #528](https://github.com/wa-pis/agent-paranoid-android/actions/runs/30734941011) | Passed |
| PyPI trusted publication and public-index smoke | [Publish PyPI #15](https://github.com/wa-pis/agent-paranoid-android/actions/runs/30735001368) | Passed |
| Independent public-artifact, agent, and audit verification | [Verify Published Release #5](https://github.com/wa-pis/agent-paranoid-android/actions/runs/30735097985) | Passed |
| Clean public-index profile installs and literal README smoke | [Verify Published Release #7](https://github.com/wa-pis/agent-paranoid-android/actions/runs/30736848757) | Passed |
| Seven-profile CLI and install-metadata verification | [Verify Published Release #8](https://github.com/wa-pis/agent-paranoid-android/actions/runs/30737685272) | Passed |

## Package Digests

The successful post-publish workflow verified `SHA256SUMS`, GitHub
attestations, and equality between the GitHub Release and public PyPI wheel and
source-distribution hashes.

| Artifact | SHA-256 |
| --- | --- |
| `agent_paranoid_android-1.0.0rc4-py3-none-any.whl` | `f38ac6cadacec56229ffe25ae12170aaf388fad842ae8ed14d0675b24bd8fde4` |
| `agent_paranoid_android-1.0.0rc4.tar.gz` | `7dc6b7511ed1cc66e8e45eefe9a860b98a5f903c5748337dd2a6275b9d8afd82` |
| `sbom.cdx.json` | `fc2e32556f0dda4c4a55019584c4b8f2d486f5f7d60375893b29aaec033b469a` |

## Container Digests

| Image | Multi-platform digest |
| --- | --- |
| `ghcr.io/wa-pis/agent-paranoid-android-cli:1.0.0rc4` | `sha256:8a3765dfc16e28cfa24f4a8ff42f37de6a509bd418a962ef6b5f203072924a6a` |
| `ghcr.io/wa-pis/agent-paranoid-android-generator-mcp:1.0.0rc4` | `sha256:8ff6648f9be8e58880b71b9361762900946770f7f17fcd4402323cd66db7ba81` |
| `ghcr.io/wa-pis/agent-paranoid-android-trino-mcp:1.0.0rc4` | `sha256:ea20f26f75bf18f924aaab5d4d53c023149a1af829ad96cd8d30765dc88aaf40` |

For each image, the verification gate resolved the version tag to the recorded
digest, required both `linux/amd64` and `linux/arm64`, inspected the embedded
SBOM, verified the GitHub attestation and keyless Cosign signature, and ran the
published image with the hardened health-check configuration.

## Public Smoke Result

The independent verification installed the exact public PyPI wheel with
hashes in a clean environment, ran the installed-package contract check,
`doctor`, and the bundled deterministic demo, and confirmed synthetic output,
no copied source rows, and successful validation. It also confirmed that the
public documentation names version `1.0.0rc4`.

Using only the installed public wheel and its bundled synthetic fixture, the
same run completed `agent-plan`, metadata-only `agent-review`, and
exact-fingerprint `agent-approve`. It then verified the generated bundle and a
two-record HMAC-authenticated MCP audit chain. No checkout fixture or release
artifact was changed by the verification run.

Verification run #7 executed from workflow commit `fd6dec9` against immutable
tag `v1.0.0rc4` and release commit `33073c0`. Its checkout-free profile matrix
installed the exact public wheel for the base, `trino`, `mcp`, and `mcp,trino`
requirements from `https://pypi.org/simple` in separate clean environments.
Every profile passed `pip check`, then ran the literal README commands
`test-data-agent doctor` and `test-data-agent demo --output out/demo`. Each
demo manifest reported `synthetic: true`, `source_rows_copied: false`, and
`validation_valid: true`.

Verification run #8 executed from workflow commit `130c00a` against the same
immutable tag and release commit. Separate clean environments covered the
base, `trino`, `mcp`, `mcp,trino`, `parquet`, `openai`, and `all` profiles.
Every profile passed the exact `test-data-agent --version` assertion,
`doctor`, `demo`, and manifest checks on Python `3.12.13`. The install reports
recorded version `1.0.0rc4`, the profile name, and wheel SHA-256
`f38ac6cadacec56229ffe25ae12170aaf388fad842ae8ed14d0675b24bd8fde4`.
The package job also reverified the wheel, source-distribution, and SBOM
digests listed above. Its separate container matrix passed the published CLI,
generator-MCP, and Trino-MCP image jobs.
