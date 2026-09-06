# 1.3.2rc1 Published Release Evidence

The protected SSH-signed tag `v1.3.2rc1` identifies exact main commit
`5eb29ce4af94049e27c32462211725e5f896d9b6`. This corrective candidate is publicly accepted as the
source tree for version- and documentation-only stable `1.3.2` promotion.
It corrects generation and validation contracts; it does not certify statistical
anonymity or statistical fidelity.

## Independent Review And Gates

[Implementation PR #490](https://github.com/wa-pis/agent-paranoid-android/pull/490)
and [candidate PR #491](https://github.com/wa-pis/agent-paranoid-android/pull/491)
merged with required checks green. The cumulative candidate and final exact
commit received [independent AI-assisted approval](https://github.com/wa-pis/agent-paranoid-android/issues/492)
using OpenCode / Nemotron 3 Ultra Free. This is not a human-review claim.
The initial review's outstanding operational evidence was supplied and the
final review concluded APPROVED with no substantive blockers.

The immutable Codex Security implementation review found one low-severity
numeric-string privacy regression; it was corrected before RC preparation,
independently verified, and covered in all generation modes. The exact RC
release gate passed 1289 tests with 10 live-service skips and 90.34% coverage;
strict documentation validation also passed.

| Gate | Evidence | Result |
| --- | --- | --- |
| Release artifact preflight | [Run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/34056927396) | Passed |
| Documentation | [Run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/34056912434) | Passed |
| Security | [Run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/34056912537) | Passed |
| Containers | [Run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/34056912458) | Passed |
| OpenSSF Scorecard | [Run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/34056912360) | Passed |
| CI | [Run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/34056912445) | Passed |
| Release / GitHub artifacts | [Run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/34057434330) | Passed |
| Signed multi-platform containers | [Run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/34057434324) | Passed |
| PyPI Trusted Publishing | [Run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/34057556703) | Passed |
| Verify Published Release | [Run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/34057671253) | Passed |

## Published Artifacts

The [GitHub prerelease](https://github.com/wa-pis/agent-paranoid-android/releases/tag/v1.3.2rc1)
and [PyPI release](https://pypi.org/project/agent-paranoid-android/1.3.2rc1/)
were published on 2026-09-06 UTC. The signed acceptance manifest binds exact
commit, independent approval, gates, historical finding dispositions and
Ubuntu-derived package hashes. Local signature and acceptance checks passed
before tag push. Publication rebuilt matching distributions and verified their
portable Sigstore bundle before uploading.

| Artifact | SHA-256 |
| --- | --- |
| `SHA256SUMS` | `d7e9e099a62fc371416994bb9fab20d6fce69df6f48c74b0fab9273e690fedb1` |
| `agent-paranoid-android-1.3.2rc1.sigstore.json` | `0e79e0863f13dd91791efc3d467c4a86594e69ab97068c0f9e72b68f1f8edebc` |
| `agent_paranoid_android-1.3.2rc1-py3-none-any.whl` | `231c644a207f243b5bbec65334eaed1ff3c14d3fc1d940c1c3e499f433edb200` |
| `agent_paranoid_android-1.3.2rc1.tar.gz` | `8d45dca22d7447eeed69b608472a02b4f700619d649b7fba1e9aceb07b24d4fa` |
| `sbom.cdx.json` | `d8779bb05995e1f9e59ea5a88ab5a8ece5e7d370497d25c8947693b7bc58ab36` |

## Signed Containers

| Image | Multi-platform digest |
| --- | --- |
| `ghcr.io/wa-pis/agent-paranoid-android-cli:1.3.2rc1` | `sha256:b65a322df45efb9c07ebfb0bfb39af723eb0e81f9d51050c8e6ed5be8609b041` |
| `ghcr.io/wa-pis/agent-paranoid-android-generator-mcp:1.3.2rc1` | `sha256:da074d2635376a508fbaae24c186adbe6791b890dc6d57f77513b2e9ad040b5e` |
| `ghcr.io/wa-pis/agent-paranoid-android-trino-mcp:1.3.2rc1` | `sha256:28916cb5082fff2f7efa8b6c0cdf271c4e5a102f2d68232cf122a8a496d63287` |

All images cover linux/amd64 and linux/arm64. Public acceptance verified
checksums, GitHub provenance, portable Python attestations, PyPI hash equality,
Cosign signatures, SBOMs, hardened container health checks, public documentation,
and installed-wheel synthetic workflows. Clean public installs passed for base,
parquet, mcp, trino, mcp-trino, openai and all profiles. No production data or
live provider credentials were used.
