# 1.6.0rc5 Release Status

RC5 is authorized. [PR #623](https://github.com/wa-pis/agent-paranoid-android/pull/623)
was merged on 2026-10-16. The frozen runtime candidate is exact main
`890925afdff68e97cafe38a28605d2874c9dad79`.
It has not been tagged, published or publicly accepted.
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

These results belong to the frozen candidate, not to later documentation
commits. A changed release candidate needs its own exact-commit evidence.

## Still required before publication

An actual Codex client created the fictional plan. The final authored
specification was then prepared; consent sent before that preparation is not
approval of the current file. The remaining manual sequence is to
[resume the existing plan](how-to/mcp.md#resume-an-existing-synthetic-plan),
inspect it, open and read the full current specification, give new specific
consent, generate, validate, verify artifacts and finish the client run.
Client-resume preflight and automated tests do not complete these human steps.

After that acceptance, validate the signed acceptance manifest, create the
signed tag and publish through the existing release workflows. There is no
agent-issued local preservation approval in this synthetic scenario.

After publication, record the GitHub/PyPI workflow results, distribution hashes,
three immutable image digests and successful `Verify Published Release` run
here. No public release result is claimed by this preparation document.
