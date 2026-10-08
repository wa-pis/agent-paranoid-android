# 1.6.0rc1 Published Release Evidence

The protected SSH-signed tag `v1.6.0rc1` identifies exact main commit
`68a20cf333b6d1bdbb02d36e64fb62ef929b2173`, merged through
[PR #603](https://github.com/wa-pis/agent-paranoid-android/pull/603).
This candidate includes selective source transformation and the completed
security-audit remediation. Stable `1.6.0` is not authorized.

## Independent Review

The complete fresh exact-main security scan
`29bd70cb-1039-4d1a-a8f6-a1eb3193bbdb` finished with zero confirmed findings
and no production-source coverage gaps. Earlier finding-bearing candidate
reports do not establish this commit's clearance.
[Exact-main acceptance](https://github.com/wa-pis/agent-paranoid-android/issues/604)
was recorded by APA-Release-Reviewer as independent AI-only review; it is not
human approval. The signed tag's acceptance manifest binds that review, all
four exact-main gates and the Ubuntu distribution hashes to this commit.

## Gates And Publication

| Gate | Evidence | Result |
| --- | --- | --- |
| CI | [Run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/37708975214) | Passed, including disposable synthetic Trino |
| Containers | [Run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/37708975307) | Passed |
| Documentation | [Run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/37708975239) | Passed |
| Security | [Run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/37708975150) | Passed |
| Ubuntu artifact preflight | [Run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/37708997851) | Passed |
| GitHub Release | [Run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/37711582305) | Passed |
| Signed containers | [Run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/37711582307) | Passed |
| PyPI Trusted Publishing | [Run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/37712080913) | Passed |
| Verify Published Release | [Run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/37712402058) | Passed |

Publication and final public acceptance succeeded. This evidence page is a post-publication documentation
update and does not change the immutable tag or released runtime.

## Public Artifacts

The [GitHub prerelease](https://github.com/wa-pis/agent-paranoid-android/releases/tag/v1.6.0rc1)
and [PyPI candidate](https://pypi.org/project/agent-paranoid-android/1.6.0rc1/)
are published. Distribution hashes match the independently rehashed Ubuntu
preflight and signed acceptance manifest. Additional asset digests below are
reported by GitHub's published release metadata.

| Artifact | SHA-256 |
| --- | --- |
| `agent_paranoid_android-1.6.0rc1-py3-none-any.whl` | `deb5378d845e8c133a2292fb0e90d1e019fe1e1c332063e209b0af10cda50fa8` |
| `agent_paranoid_android-1.6.0rc1.tar.gz` | `e67add4257fb5a0a193af5bfeb377394adf34fa9b84489bc844cbddc5c1c22e0` |
| `agent-paranoid-android-1.6.0rc1.sigstore.json` | `78207e9fc5c02f3b9f8113b3105777683caf83d2c6a81bb0e6d022ccc7f4db28` |
| `sbom.cdx.json` | `8a766bd29ebd914051417018799be64748e2f9e4e30708b64c9387ede7b304e9` |
| `SHA256SUMS` | `089970ca7d78a65091caecb469aa3485250f0c0f3ccdf335813823d881de8a96` |

The container publication workflow created provenance attestations and verified
keyless signatures for these immutable multi-platform manifest digests:

| Image | Digest |
| --- | --- |
| `ghcr.io/wa-pis/agent-paranoid-android-cli:1.6.0rc1` | `sha256:3d03a4f4a6a05fa800cd33950ba8360b793308db0a4935867cb8e530768a23c9` |
| `ghcr.io/wa-pis/agent-paranoid-android-generator-mcp:1.6.0rc1` | `sha256:2813b0b9ca59163262f3516e6df283bfcc7950b3414b9d5f50fd46807036aa97` |
| `ghcr.io/wa-pis/agent-paranoid-android-trino-mcp:1.6.0rc1` | `sha256:fe75a231324c7f18ba2424c89c3946ac5c7d3986fe26fb4e39007528dbe8e56b` |

The public verification workflow passed downloaded checksums and portable
attestations, hash-pinned installed package profiles, documentation and all
three signed multi-platform containers. No production data or external AI calls were used for acceptance.
