# 1.6.0rc3 Published Release Evidence

GitHub and PyPI publication succeeded. Container publication and complete public acceptance succeeded.

The protected SSH-signed tag `v1.6.0rc3` targets exact main commit
`450f6319cbad4b39c54e42b1fcb56529ca0de214`, merged through
[PR #610](https://github.com/wa-pis/agent-paranoid-android/pull/610).
RC3 corrects external feedback and conservative field relationship inference;
see [feedback corrections and migration](rc3-feedback.md).

[Exact-main acceptance](https://github.com/wa-pis/agent-paranoid-android/issues/611)
records independent AI review by APA-RC3-Reviewer, including the initial false
relationship finding and its verified correction. The final exact main tree
matches the reviewed candidate. AI review does not represent human dataset
approval. RC2 transformation permissions remain unchanged.

The exact-main local release gate passed with 3351 tests, 23 skips and 91.06%
coverage. Strict documentation and installed-wheel feedback and field-binding
checks passed. The signed manifest binds exact-commit review, all four hosted
gates and independently rehashed Ubuntu preflight distributions.

| Gate | Evidence | Result |
| --- | --- | --- |
| CI | [Run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/38304130163) | Passed |
| Containers | [Run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/38304129997) | Passed |
| Documentation | [Run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/38304129986) | Passed |
| Security | [Run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/38304130002) | Passed |
| Ubuntu artifact preflight | [Run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/38304288121) | Passed |

| Artifact | SHA-256 |
| --- | --- |
| `agent_paranoid_android-1.6.0rc3-py3-none-any.whl` | `79faa9d81b117674ecea3842f30a7059ecf225036c919c66f4cad45e5c35bb44` |
| `agent_paranoid_android-1.6.0rc3.tar.gz` | `493ddf54fe12144ad42a3f5d9dc2d4f99d4073a72ed9c1de61b0feea2fd90ebb` |

GitHub Release [38305526320](https://github.com/wa-pis/agent-paranoid-android/actions/runs/38305526320) and PyPI Trusted Publishing [38306284523](https://github.com/wa-pis/agent-paranoid-android/actions/runs/38306284523) succeeded. Downloaded GitHub assets match every SHA256SUMS entry; wheel and sdist match the signed manifest. Both portable provenance verifications passed with the exact release tag and release.yml signer. Public PyPI hashes match both distributions.

Container publication [38305526430](https://github.com/wa-pis/agent-paranoid-android/actions/runs/38305526430) and [Verify Published Release](https://github.com/wa-pis/agent-paranoid-android/actions/runs/38306820821) succeeded. Public acceptance verified all seven hash-pinned installation profiles, upgrade from 0.12.0, doctor, synthetic demo, exact-fingerprint agent approval and audit verification, public documentation, and all three signed multi-platform containers with SBOM and provenance checks.

The field-link regression also passed independently on the all-extra package installed from public PyPI: unrelated numeric keys infer no links; an explicitly declared different-name field binding resolves all references.

| Image | Immutable manifest digest |
| --- | --- |
| `ghcr.io/wa-pis/agent-paranoid-android-cli:1.6.0rc3` | `sha256:c1783c5ea73470d5ba226322a36a62916d40e2362ae79769d3ab263ebbc5dae9` |
| `ghcr.io/wa-pis/agent-paranoid-android-generator-mcp:1.6.0rc3` | `sha256:e72bfd23c357440c0c213223df312152391d5c8245bb047e5a0d46139326f16f` |
| `ghcr.io/wa-pis/agent-paranoid-android-trino-mcp:1.6.0rc3` | `sha256:75f6f7180d494eda9c79dba9ff0a3d0f00806b4cd0ecdcb806b3bceeac3537da` |

This post-publication documentation does not alter the immutable tag.
