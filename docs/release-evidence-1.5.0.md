# 1.5.0 Published Release Evidence

The protected SSH-signed tag `v1.5.0` identifies exact commit
`dee79d4980934cf444a1f5d57ed05ec21d41ea2b`, tree
`308c2da61bf7899df8144615d294c945883c6d15`.
Stable promotes the publicly accepted
[1.5.0rc1 runtime](release-evidence-1.5.0rc1.md) through version and
documentation changes only. No runtime, dependency graph, workflow, container,
schema or test-scenario changes were introduced during promotion.

## Independent Review

[Exact-commit approval](https://github.com/wa-pis/agent-paranoid-android/issues/511)
was provided by APA-Release-Reviewer (Pauli), a separate read-only Codex AI
reviewer, on 2026-09-23 Europe/Samara (2026-09-22 UTC). This is AI-only review,
not human approval; the exact model version was not independently verified.

The reviewer inspected the full promotion diff, confirmed final merge-tree
identity, independently queried all exact-commit gates and rehashed the Ubuntu
wheel and sdist. The RC privacy-disclosure and short-string-diversity findings
remained closed. A stale documentation baseline was corrected and re-reviewed.
There were no outstanding release-blocking findings within review scope.

The release agent reran the full local gate on the exact final SHA:
1362 passed, 10 live-service skips, 90.59% coverage. Lint, typing, licenses,
direct safety boundaries, budgets, schema freshness, README quickstart and
strict documentation checks passed. The independent reviewer did not rerun
the full local suite; its source checks and artifact verification are separate
evidence.

## Gates And Publication

| Gate | Evidence | Result |
| --- | --- | --- |
| CI | [Run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/35790195805) | Passed |
| Containers | [Run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/35790195773) | Passed |
| Documentation | [Run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/35790195717) | Passed |
| Security | [Run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/35790195744) | Passed |
| Ubuntu preflight | [Run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/35790229614) | Passed |
| GitHub Release | [Run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/35790883229) | Passed |
| Signed containers | [Run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/35790883153) | Passed |
| PyPI Trusted Publishing | [Run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/35791168193) | Passed |
| Public acceptance | [Run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/35791411828) | Passed on attempt 2 |

On public-acceptance attempt 1, the base and MCP installation jobs received
`No matching distribution found for agent-paranoid-android==1.5.0` while
other profiles installed the same public release successfully. Only those two
failed jobs were rerun; both passed. This was transient public-index visibility,
not a runtime test failure. No tag, source, artifact, dependency or check was
changed or bypassed.

## Public Artifacts

The [GitHub stable release](https://github.com/wa-pis/agent-paranoid-android/releases/tag/v1.5.0)
and [PyPI package](https://pypi.org/project/agent-paranoid-android/1.5.0/)
are public. The published distribution hashes match the signed acceptance
manifest and Ubuntu preflight.

| Artifact | SHA-256 |
| --- | --- |
| `agent_paranoid_android-1.5.0-py3-none-any.whl` | `45dd9845a804c8cf33fe3a46cb15b80f688f2778e925a1cde7087589153b0f53` |
| `agent_paranoid_android-1.5.0.tar.gz` | `7bacebf7c8fb6cad60a2017b0ebb5e590af6a9c401ffeaee2afcd79c7b561aff` |
| `agent-paranoid-android-1.5.0.sigstore.json` | `82ae904d6dd5315e390dc24dffdfb5cf96996f5337d371d9d2a0d7e34699ddaf` |
| `sbom.cdx.json` | `aaf10440a0846b251efd948f73f384074d4fbaf7f7c21bf4e09dff6ad90fa75c` |
| `SHA256SUMS` | `69711d6492bc74e3bfc1a82e1e3e33fea9d01d533a883184327724fa07a8281b` |

| Multi-platform image | Digest |
| --- | --- |
| `ghcr.io/wa-pis/agent-paranoid-android-cli:1.5.0` | `sha256:bad4d563ab3a506759a19ca7e6473d1033ffc342c08a873e2564d88ae2904647` |
| `ghcr.io/wa-pis/agent-paranoid-android-generator-mcp:1.5.0` | `sha256:bea2526e9f22dfd94259e485682f58b91ec3853600f39e93f01f8275e409255f` |
| `ghcr.io/wa-pis/agent-paranoid-android-trino-mcp:1.5.0` | `sha256:9305e1ef9b33b715abcf74603008eff8b32efaa38c5a4b1240ccede168d466e4` |

## Public Acceptance

All public verification jobs passed: base, parquet, mcp, trino, mcp-trino,
openai and all installations; README doctor/demo; installed-package agent
planning, approval and audit workflows; public documentation; wheel/sdist
checksums and portable Sigstore/GitHub attestations; and all three
multi-platform containers with SBOM, provenance, signatures and health checks.

No production data or live provider credentials were used. The immutable
release tag remains at the reviewed commit; this post-publication evidence
does not change the released source.

