# 1.6.0rc5 Release Status

RC5 is authorized. [PR #623](https://github.com/wa-pis/agent-paranoid-android/pull/623)
was merged on 2026-10-16. The frozen runtime candidate is exact main
`890925afdff68e97cafe38a28605d2874c9dad79`.
GitHub, PyPI and all three container publication workflows passed.
Post-publication acceptance passed on the first attempt, all 12 jobs; see the
[publication evidence](release-evidence-1.6.0rc5.md).
Published [RC4 evidence](release-evidence-1.6.0rc4.md) remains historical and
immutable.

RC5 packages the [RC4 feedback corrections](rc4-external-feedback.md),
[source/output contract](reference/source-output-matrix.md), portable business
rules and [MCP permission reference](reference/mcp-permissions.md). The
[runtime campaign evidence](acceptance-evidence-1.6.0rc5.md) separates the earlier
campaign from fresh exact-RC5 checks, artifact identities and coverage limits.

## Completed candidate checks

- The confirmed DECIMAL formatting issue is fixed, with focused regressions.
- The full exact-main gate passed: 4197 tests, 23 classified skips and 91.49%
  coverage. Strict documentation and OpenSpec checks passed.
- Independent AI source review approved that exact main SHA. CI, Containers,
  Documentation and Security passed on the same commit.
- Both installed MCP SDK matrices passed 600/600 logical cells, with two seeded
  repeats per cell. Fresh Ubuntu no-publish artifacts were downloaded and
  independently rehashed. See the [candidate checkpoint](acceptance-evidence-1.6.0rc5.md#exact-rc5-candidate-checkpoint).
- Actual Codex and current-specification human acceptance passed: full-file
  review and new consent preceded generation; validation and the separate
  artifact audit passed. See the [manual evidence and observation limits](acceptance-evidence-1.6.0rc5.md#actual-codex-and-human-specification-acceptance).

These results belong to the frozen candidate, not to later documentation
commits. A changed release candidate needs its own exact-commit evidence.

## Publication and retained limits

The completed manual acceptance is bound to the frozen candidate and the exact
reviewed specification. Separate trust/tool UI prompts and normal client
exit/disconnect were not independently observed; the final bound MCP process
check found none remaining. The separately gated transformation/session campaign
is still open, and this synthetic scenario grants no local preservation authority.

The signed tag and acceptance manifest bind the frozen source and Ubuntu
preflight hashes. GitHub/PyPI publication and the three-target container
publication workflow succeeded. Public PyPI hashes match the preflight.

The three immutable image digests and publication signature checks are recorded
in the [published release evidence](release-evidence-1.6.0rc5.md).
`Verify Published Release` passed with all 12 jobs on the first attempt, including
the Python-package/documentation job, all seven public installation profiles and
all three container targets. Release-specific publication and public acceptance
are complete.
