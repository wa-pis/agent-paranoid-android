# 1.6.0rc4 Published Release Evidence

GitHub, PyPI and all three containers were published successfully. Public acceptance passed.

The protected SSH-signed tag `v1.6.0rc4` targets exact main commit
`e62a28b75b710afa541aa15b12b5c6fe1f1ecaac`, after
[PR #613](https://github.com/wa-pis/agent-paranoid-android/pull/613) and the
numeric scaling correction in [PR #615](https://github.com/wa-pis/agent-paranoid-android/pull/615).
RC4 implements folder overwrite, valid edge cases and bounded load generation;
see [generation modes and replacement](reference/generation-modes.md).
RC3 remains immutable.

[Exact-main acceptance](https://github.com/wa-pis/agent-paranoid-android/issues/614)
records independent AI review by APA-RC4-Reviewer, including the edge scaling
correction. The final main tree matches the reviewed candidate. AI review does
not represent human dataset approval. Transformation permissions remain unchanged.

The exact-main local release gate passed with 3365 tests and 23 skips.
Strict documentation and the isolated installed-wheel field relationship,
load multiplier, exact count, edge and folder replacement checks passed.
The signed manifest binds exact-commit review, all four hosted gates and
independently rehashed Ubuntu preflight distributions. Earlier main `6e162d…`
and its preflight were superseded before tagging and were not published.

| Gate | Evidence | Result |
| --- | --- | --- |
| CI | [Run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/38369077202) | Passed |
| Containers | [Run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/38369077106) | Passed |
| Documentation | [Run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/38369077390) | Passed |
| Security | [Run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/38369077325) | Passed |
| Ubuntu artifact preflight | [Run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/38369367113) | Passed |

| Artifact | SHA-256 |
| --- | --- |
| `agent_paranoid_android-1.6.0rc4-py3-none-any.whl` | `19de1f0d81d07f2bbff43b4915906c1643db68e0d1431170b29b06bfd92ed27f` |
| `agent_paranoid_android-1.6.0rc4.tar.gz` | `76fa111d1a90d8b46f9742dd602296ce7464620c9bf0de589814f90bff34e1fd` |

GitHub Release [publication run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/38370495674),
PyPI Trusted Publishing [run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/38371538032)
and container [publication run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/38370495609)
succeeded. Every downloaded GitHub checksum entry matches; wheel and sdist
match the signed acceptance manifest. Both portable tag-bound provenance
verifications passed, and public PyPI hashes match both distributions.

[Verify Published Release](https://github.com/wa-pis/agent-paranoid-android/actions/runs/38371905206)
passed on attempt 2. The initial attempt encountered transient PyPI index
propagation: the main package check, base profile and MCP profile did not yet
see RC4. Only those failed jobs were rerun; published artifacts were unchanged.
The complete run verified all seven hash-pinned installation profiles, upgrade
from 0.12.0, doctor, synthetic demo, exact-fingerprint agent approval and audit
verification, public documentation, and all three signed multi-platform
containers with SBOM, provenance and hardened runtime checks.

The all-extra wheel installed independently from public PyPI also passed the
field-link, default load ×10, exact-count override, linked edge and complete
folder overwrite regressions using fictional data only.

| Image | Immutable manifest digest |
| --- | --- |
| `ghcr.io/wa-pis/agent-paranoid-android-cli:1.6.0rc4` | `sha256:62b8aedafb4861179f0d0dc9ec4f8108630de94869e66087affff365c28336ce` |
| `ghcr.io/wa-pis/agent-paranoid-android-generator-mcp:1.6.0rc4` | `sha256:7ef59aeca38b5fcdf82c52ef79d0211e33e4c26c68f9dda53a1159d648306c6a` |
| `ghcr.io/wa-pis/agent-paranoid-android-trino-mcp:1.6.0rc4` | `sha256:45e0a60f5ddaecb4a461ce5f8cf6768ae848d6fe08a0dc4886c0fc9be91dafc8` |

This post-publication documentation does not alter the immutable tag.
