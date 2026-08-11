# 1.0.0rc6 Published Release Evidence

This document records the immutable public-artifact evidence for
`v1.0.0rc6`. It is release-engineering evidence for maintainers, not an
additional product or privacy guarantee.

## Immutable Release Identity

The signed annotated tag `v1.0.0rc6` resolves to release commit
`2b65515313281aaeb180bb95328785ef46be0202`. Its acceptance manifest binds that
commit to the closed RC6 findings, exact gate URLs, approval record, and wheel
and source-distribution hashes.

The exact commit received an
[AI-assisted independent review](https://github.com/wa-pis/agent-paranoid-android/issues/397)
under stable pseudonym `opencode-nemotron-3-ultra-free-rc6`, using OpenCode with
Nemotron 3 Ultra Free. This is not a human-review claim or a waiver. The review
found no unresolved Critical or High defect and accepted the documented Low
findings as non-blocking for RC6.

| Gate | Evidence | Result |
| --- | --- | --- |
| Exact-commit CI | [CI run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/31518585730) | Passed |
| Exact-commit documentation | [Documentation run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/31518585728) | Passed |
| Exact-commit security | [Security run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/31518585687) | Passed |
| Full release gate, GitHub Release, package SBOM, and attestations | [Release run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/31526175512) | Passed |
| Multi-platform GHCR images, SBOM, provenance, and signatures | [Containers run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/31526175468) | Passed |
| PyPI trusted publication and public-index verification | [Publish PyPI run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/31526347718) | Passed |
| Independent public-artifact acceptance | [Verify Published Release run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/31526588778) | Passed |

The resulting [GitHub prerelease](https://github.com/wa-pis/agent-paranoid-android/releases/tag/v1.0.0rc6)
and [PyPI release](https://pypi.org/project/agent-paranoid-android/1.0.0rc6/)
were published on 2026-08-11 and remain bound to the tag above.

## Package Digests

The successful post-publish workflow verified `SHA256SUMS`, GitHub
attestations, and equality between the GitHub Release and public PyPI wheel and
source-distribution hashes.

| Artifact | SHA-256 |
| --- | --- |
| `agent_paranoid_android-1.0.0rc6-py3-none-any.whl` | `2346ed729b2e5594d204beb615e8ae3d94d13bf5ecc7625af7e6fca01826f830` |
| `agent_paranoid_android-1.0.0rc6.tar.gz` | `3a95920e0ed2e7dad27a4be316c66696e952680e7b4f7485fb16cbb0f53a29a7` |
| `sbom.cdx.json` | `33a04a48fc0b4bebfa5260c0e15c5fbb3f5fd901958583d4320e158052e53175` |
| `SHA256SUMS` | `7f15e2cbb12f66e81b7aba453920a3239ff72368e2d70a6f031f2a8eb16dcd1f` |

## Container Digests

| Image | Multi-platform digest |
| --- | --- |
| `ghcr.io/wa-pis/agent-paranoid-android-cli:1.0.0rc6` | `sha256:a6a2741ba933242d8fda9f6ceef798b669506a016a6f0660826425f643928c2e` |
| `ghcr.io/wa-pis/agent-paranoid-android-generator-mcp:1.0.0rc6` | `sha256:bb8f4d944d837e54aecc3ff38193fe1aededfe7a52da860765acd44b5d6152d0` |
| `ghcr.io/wa-pis/agent-paranoid-android-trino-mcp:1.0.0rc6` | `sha256:94e95a986d79d2af634676646b817f436066883dea706eb1f38dd7ae63ff8bd9` |

For each image, verification resolved the version tag to the recorded digest,
required `linux/amd64` and `linux/arm64`, inspected the embedded SBOM, verified
the GitHub attestation and keyless Cosign signature, and pulled and ran the
published image under its hardened health-check configuration.

## Public Acceptance Result

The post-publish workflow installed the exact public package in separate clean
environments for the base, `parquet`, `mcp`, `trino`, `mcp,trino`, `openai`,
and `all` profiles. It verified package identity, dependencies, public CLI
contracts, the literal README quickstart, deterministic synthetic generation,
agent approval, audit verification, and upgrade from public `0.12.0`.

The optional `postgres` profile was then installed from public PyPI in a fresh
environment with hash-pinned dependencies and the verified wheel. The
[PostgreSQL profile evidence](https://github.com/wa-pis/agent-paranoid-android/issues/398)
records successful `--version`, `doctor`, `doctor --require-extra postgres`,
CSV/JSON quickstarts, PostgreSQL command discovery, and two byte-identical SQL
exports containing a transaction, quoted DDL, INSERT statements, and `NULL`
handling. That public-wheel smoke opened no database connection and makes no
live-database claim.

The source documentation now uses present-tense installation language. The
README embedded in the immutable RC6 distributions remains the content of the
tagged source; no published package was replaced to change its long
description.

The separate disposable PostgreSQL acceptance check used only synthetic data,
proved the profiling role could not write, enforced schema/table/column
allowlists and budgets, preserved only the approved enum, executed the
generated SQL in an empty target, checked foreign keys, and cleaned up the
temporary cluster.

Together with the exact-commit approval and the accepted Low-risk ledger in
[Known Issues](known-issues.md), these checks close RC6 acceptance. Promotion
to stable `1.0.0` remains a separate, metadata-only release process based on
this immutable source tree.
