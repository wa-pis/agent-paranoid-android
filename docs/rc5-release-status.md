# 1.6.0rc5 Release Status

RC5 is authorized and being prepared in
[PR #623](https://github.com/wa-pis/agent-paranoid-android/pull/623).
It has not been tagged, published or publicly accepted.
Published [RC4 evidence](release-evidence-1.6.0rc4.md) remains historical and
immutable.

RC5 packages the [RC4 feedback corrections](rc4-external-feedback.md),
[source/output contract](reference/source-output-matrix.md), portable business
rules and [MCP permission reference](reference/mcp-permissions.md). The
[runtime campaign evidence](acceptance-evidence-1.6.0rc5.md) records the earlier
tested source, artifact identities and limits; it is not a replacement for
exact-RC5 release gates.

## Required before publication

- Actual Codex call evidence, human review of the exact specification and client
  completion; no agent-issued local preservation approval.
- Independent review and full local/hosted gates for the exact final main SHA.
- Fresh Ubuntu no-publish wheel/sdist hashes, independently rehashed downloads
  and a validated signed acceptance manifest/tag.

After publication, record the GitHub/PyPI workflow results, distribution hashes,
three immutable image digests and successful `Verify Published Release` run
here. No public release result is claimed by this preparation document.
