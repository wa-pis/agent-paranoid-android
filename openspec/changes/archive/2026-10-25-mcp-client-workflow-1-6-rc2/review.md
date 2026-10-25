# Independent AI Candidate Review

## Identity And Scope

Reviewer pseudonym: APA-RC2-Reviewer, independent read-only reviewer subagent
`/root/rc2_reviewer`. Date: 2026-10-09, Europe/Samara. AI review only; this is
not human acceptance, a GitHub-required approval, or permission to publish.

Accepted comparison baseline: v1.6.0rc1,
`68a20cf333b6d1bdbb02d36e64fb62ef929b2173`.
Reviewed all candidate diff hunks, connected MCP exception handling, planning,
fingerprint approval, recovery, contracts, tests and release documentation.
No source-generation or approval implementation change was observed beyond
existing-tool descriptions and shared transport redaction. No new source-
preserving registrations or permissions were introduced by the RC2 diff.

## Initial Candidate And Finding

Candidate: `5ce70b65814a4a5740cfa4bf8af4aac981ebb18a`.
P1: SDK 1 wrapped OSError and other native exception types into text-bearing
ToolError; the first RC2 correction covered RuntimeError and known typed
errors only. A fictional private OSError marker was reflected in the response.
Disposition: release held, fix required, no clearance on this initial SHA.

Independent initial workflow/wire checks: SDK 1.28.1 / Python 3.11 and
SDK 2.2.0 / Python 3.13 each passed 5 existing tests; those passing tests did
not establish coverage of the missing native exception classes.

## Corrected Candidate

Candidate: `eafb3d771da16d354ad7f33d395feeebe2bfc84f`.
P1 disposition: closed by independent re-review. The shared transport detaches
native causes, including OSError and ValueError. Exact application ToolError
preservation matches the established explicit-error contract; subclasses and
other native causes follow redaction. Cleanup and budget diagnostics remain
reconstructed from exact typed errors rather than arbitrary exception text.

Independent workflow, wire/log and transport suites:

- MCP 1.28.1 / Python 3.11: 58 passed.
- MCP 2.2.0 / Python 3.13: 58 passed.

No remaining findings in this corrected reviewed RC2 diff. An in-progress
progress.md modification was excluded from the exact-commit review.

## Outstanding Release Evidence

Final main SHA binding and any subsequent changes require independent review
on that exact source. Genuine manual client acceptance, exact-main gates,
Ubuntu preflight hashes, signed acceptance manifest and public verification
were not established by this review. Do not reuse this report as approval of
a different final release commit without explicit reviewer confirmation.

## Final Main Binding

APA-RC2-Reviewer independently cleared final main
21f4a04ed4acd7c33caac9fda8c6c03b7f0501d1 on 2026-10-09, verifying an empty
tracked diff and exact tree equality with corrected eafb3d7:
0e5754d1ff5d955b4d2a8b0b9fdace39ed090071. RC1 is an ancestor; no intervening
source changes or new findings. Previous P1 remains closed. The independent
58+58 SDK checks carry forward for the identical tree; no redundant tests ran.
Uncommitted post-release evidence files are excluded. This is AI source clearance
only; artifact and publication gates remain separate.

Public exact-main source and human-client evidence:
https://github.com/wa-pis/agent-paranoid-android/issues/608
Recorded by the release operator from the independent AI reviewer report;
not a human/GitHub approval. Pending gates are explicitly separate there.
