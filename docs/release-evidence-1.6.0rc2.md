# 1.6.0rc2 Published Release Evidence

The protected SSH-signed tag `v1.6.0rc2` identifies exact main commit
`21f4a04ed4acd7c33caac9fda8c6c03b7f0501d1`, merged through
[PR #607](https://github.com/wa-pis/agent-paranoid-android/pull/607).
The candidate adds local MCP onboarding, exact-fingerprint human review,
SDK stdio workflow coverage and unexpected native-exception redaction.

## Acceptance

[Exact-main acceptance](https://github.com/wa-pis/agent-paranoid-android/issues/608)
records independent AI review by APA-RC2-Reviewer, including the initial P1
native-exception finding and its verified correction. Final main has the exact
reviewed source tree. AI review does not represent human or GitHub approval.
Actual human acceptance in Claude Desktop 1.46388.4 completed using a fictional
fixture, explicit review and approval of fingerprint
`bfca7ee8a871ef0baae16ccac9ae99ad77d7705f7d1333a5b6641eca12ec2985`,
seed 81 and four generated customers. Validation and source-row disjointness
were verified. See the OpenSpec client-acceptance and review records.
The signed tag manifest binds review, four exact-main gates and Ubuntu hashes.

## Gates And Publication

| Gate | Evidence | Result |
| --- | --- | --- |
| CI | [Run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/37839132106) | Passed |
| Containers | [Run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/37839132014) | Passed |
| Documentation | [Run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/37839131975) | Passed |
| Security | [Run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/37839131939) | Passed |
| Ubuntu artifact preflight | [Run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/37839244179) | Passed |
| GitHub Release | [Run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/37840474596) | Passed |
| Signed containers | [Run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/37840474599) | Passed |
| PyPI Trusted Publishing | [Run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/37841342683) | Passed |
| Verify Published Release | [Run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/37842786407) | Passed |

The exact-main local release gate passed with 3326 tests, 23 skips and 91.03%
coverage. This post-publication documentation does not alter the immutable tag.

## Public Artifacts

The [GitHub prerelease](https://github.com/wa-pis/agent-paranoid-android/releases/tag/v1.6.0rc2)
and [PyPI candidate](https://pypi.org/project/agent-paranoid-android/1.6.0rc2/)
are published. Wheel and sdist hashes match independently rehashed Ubuntu
preflight artifacts and the signed manifest.

| Artifact | SHA-256 |
| --- | --- |
| `agent_paranoid_android-1.6.0rc2-py3-none-any.whl` | `1fa1da2dba508c7c6152bc0af590a3be209c5e298fbc58bb7cc9a1543c87ac28` |
| `agent_paranoid_android-1.6.0rc2.tar.gz` | `32bac1ff7c94c4d3bb1a78862783363ecb00db0155f9f12ed66937130647a41d` |

Container publication verified keyless signatures and provenance attestations
for these immutable multi-platform manifest digests:

| Image | Digest |
| --- | --- |
| `ghcr.io/wa-pis/agent-paranoid-android-cli:1.6.0rc2` | `sha256:49cf775c4817a9d74bc0939dff23a921df0e2a18ded17367ee76fc3cd852c883` |
| `ghcr.io/wa-pis/agent-paranoid-android-generator-mcp:1.6.0rc2` | `sha256:222dc508743fa3b2849c022c710c54352007d937e332d03c77b5fdc39ba28f19` |
| `ghcr.io/wa-pis/agent-paranoid-android-trino-mcp:1.6.0rc2` | `sha256:81554cf595966236e7c892fc6f766800cb42b7102743dd34f6da6a8d4053921c` |

Public verification passed checksums, attestations, all seven hash-pinned
installation profiles, public documentation and all three signed containers.
