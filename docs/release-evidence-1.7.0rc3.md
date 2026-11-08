# 1.7.0rc3 Release Evidence

GitHub, PyPI and all three signed multi-platform container targets are published.
All 12 public acceptance jobs passed on attempt 1. Stable 1.6.0 remains recommended.

## Source and independent review

The owner authorized the next RC with Python 3.15 on 2026-11-08.
[PR #694](https://github.com/wa-pis/agent-paranoid-android/pull/694) merged after
all 48 checks passed. SSH-signed tag `v1.7.0rc3` targets exact main
`09b6fb207b22364ff41f70d7b51abe30d1a458fa`; tag object
`025ce54fade67eee8bb7f5e0c7c6f2b9ff3abbb6`. Final tree:
`a85bf16018c4ce4fb0bcadab45dcea257e1e960b`. Raw signed commit-object SHA-256:
`0c0897bcab3ea61d2c2ef3ef4a1e23fdb37c352a834d1aa504426d7ac37ae5ea`.
GitHub verifies the merge signature. The local allowed-signer identity check,
version check and signed manifest/artifact validation passed before tag push.

The independent read-only technical AI reviewer explicitly inspected this exact
main commit and the complete delta from signed v1.7.0rc2. Review covered DAG/FK
proofs, mandatory recovery validation, cumulative work/deadlines, worker cleanup,
atomic publication, approval/signature/manifest gates, Python 3.15 dependencies
and pinned bootstrap. No actionable release-blocking findings remained.
The [review receipt](https://github.com/wa-pis/agent-paranoid-android/pull/694)
is technical AI acceptance, not human consent or GitHub approval.

## Explicit manual-client exception

After the prepared Claude Desktop packet and its pending manual acceptance gate
were presented, the owner instructed “в этот раз пропустим” (“skip it this time”)
on 2026-11-08. Manual Claude Desktop acceptance was **waived for this RC only**;
it was not executed or passed. The fictional plan remains awaiting approval,
without an approval receipt or generated dataset. No human client evidence is
claimed. Automated checks and historical human records do not replace this
missing manual result. This exception grants no dataset approval or policy
bypass and does not change the product's approval enforcement.

## Exact-source gates and artifacts

All final-main workflows passed:
[CI](https://github.com/wa-pis/agent-paranoid-android/actions/runs/42514907721),
[Containers](https://github.com/wa-pis/agent-paranoid-android/actions/runs/42514907803),
[Documentation](https://github.com/wa-pis/agent-paranoid-android/actions/runs/42514907747),
[Security](https://github.com/wa-pis/agent-paranoid-android/actions/runs/42514907726)
and [Scorecard](https://github.com/wa-pis/agent-paranoid-android/actions/runs/42514907785).
The [Ubuntu preflight](https://github.com/wa-pis/agent-paranoid-android/actions/runs/42514912301)
passed the full gate: 4,857 tests passed, 25 skipped, two warnings, 92% coverage,
plus isolated installed-wheel smoke/doctor checks. Local exact-main CPython
3.15.2/macOS arm64 release gate: 4,902 passed, 24 skipped, two warnings,
92% coverage. Strict documentation build passed. Different optional documentation
dependencies account for the differing local/Ubuntu collection scope; opt-in
live services were not exercised.

| Artifact | SHA-256 |
| --- | --- |
| `agent_paranoid_android-1.7.0rc3-py3-none-any.whl` | `5345e27a5a8311d72cedda193747c861f2d646ef0de374bd9bd74e1405c5195d` |
| `agent_paranoid_android-1.7.0rc3.tar.gz` | `b494591a356c9ff90ce629bcdade98791114faee25b09fca5b6eb61fe0cf6ff8` |

Both archives were independently rehashed. Read-only AI artifact review compared
all 181 wheel payload files (including five skills and eight prompts), all 186
RECORD entries and 1,245 sdist source files to exact reviewed Git blobs. Generated
metadata, Python 3.11–3.15 classifiers, extras, entrypoints, README and license
matched. No unexplained files, duplicate paths, traversal or symlinks were found.
Inspection did not extract or execute archive contents. Separately, the exact
Ubuntu wheel installed in an isolated Python 3.15.2 MCP environment and passed
profile/doctor checks; real SDK stdio planning/inspection reached awaiting
approval. It did not execute human approval or generation.

## Publication and public acceptance

[Release](https://github.com/wa-pis/agent-paranoid-android/actions/runs/42516413538)
completed successfully. The [GitHub prerelease](https://github.com/wa-pis/agent-paranoid-android/releases/tag/v1.7.0rc3)
was published at 2026-11-08 19:52:08 UTC.
[Trusted PyPI publication](https://github.com/wa-pis/agent-paranoid-android/actions/runs/42517193106)
uploaded the distributions. Actual public GitHub and PyPI wheel/sdist downloads
were rehashed against the signed manifest; all matched. Both GitHub distributions
passed portable Sigstore provenance verification against exact workflow
`release.yml` and `refs/tags/v1.7.0rc3`. Public PyPI metadata includes the Python
3.15 classifier and retains `Requires-Python: >=3.11`. Candidate documentation
is publicly available under `versions/1.7.0rc3/`.

[Containers](https://github.com/wa-pis/agent-paranoid-android/actions/runs/42516413574)
completed all six AMD64/ARM64 validation jobs and all three image publications.

| Image | Immutable multi-platform manifest digest |
| --- | --- |
| `ghcr.io/wa-pis/agent-paranoid-android-cli:1.7.0rc3` | `sha256:8cd356df652a30ab4fdc366da53403cc3239eaa7c1bba41bcccd3c3a88ab1fef` |
| `ghcr.io/wa-pis/agent-paranoid-android-generator-mcp:1.7.0rc3` | `sha256:d69327626a6397a911cd4e3428f5f493697df4729ae122b40fb92a77654bb3d2` |
| `ghcr.io/wa-pis/agent-paranoid-android-trino-mcp:1.7.0rc3` | `sha256:277b9ac502ec1ecc2828cef75ed41bbc1f7ddaff7b4b212b3a55c233b736d840` |

[Verify Published Release](https://github.com/wa-pis/agent-paranoid-android/actions/runs/42517687082)
passed all 12 jobs on attempt 1 at the exact tagged source: immutable identity,
package/documentation, seven public installation profiles and three container
targets. Checks cover public downloads and installation/upgrade, doctor,
fictional synthetic and agent workflows, portable package provenance, image
SBOM/provenance, keyless signatures and hardened container workloads. Container
signature identity is
`https://github.com/wa-pis/agent-paranoid-android/.github/workflows/containers.yml@refs/tags/v1.7.0rc3`.
This automated fictional acceptance is distinct from the waived human client
check above.

## Scope and limits

Standard GIL-enabled CPython 3.11–3.15 is supported; PyYAML 6.0.3 may require
a compiler on Python 3.15. No free-threaded or alternate-interpreter support,
cross-Python byte identity or Python 3.15 speed guarantee is claimed.

The explicit scalable relational engine supports bounded acyclic synthetic
many-to-one/one-to-one graphs, chains, multiple parents and nullable links.
Cycles, composite keys, shared PK/FK identities, global rules and unsupported
modes reject before generation. Linux/macOS execution only; memory checks are
cooperative. The development four-worker median was 1.953×, below the ≥2× target
and with substantial variation; this is not a release-artifact speed claim.
See [capacity guidance](how-to/dataset-capacity.md).

Only fictional fixtures were used. No production data, live database/provider
calls, source-preserving activation or new human dataset approval is claimed.
Candidate guides remain isolated under `versions/1.7.0rc3/`; stable 1.6.0 keeps
the default documentation.
