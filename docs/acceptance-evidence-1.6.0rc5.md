# Cross-interface Acceptance Evidence For RC5

## Status and identities

The automated runtime campaign passed before the RC5 version change. Human
Codex acceptance and RC5 publication remain open. This document records what
actually ran, without treating a previous artifact as a newly built RC5 wheel.
The [plan](acceptance-matrix.md) and [release process](release.md) still apply.

| Identity | Value |
| --- | --- |
| Final campaign source | `408ec527795146cb0971dc12f7eb75cb9415b0a6` |
| Installed matrix/SDK execution source | `2eecfd6980bd88cf1c8a4152ed3f8792f6c30895` |
| Campaign wheel version | `1.6.0rc4` development build, distinct from published RC4 |
| Byte-identical wheel SHA-256 at both sources | `5eaddcebc83961d4c3e74daa0d12fdd25657d77734a1745456c80e2106a108e6` |
| Final campaign sdist SHA-256 | `a31db8a1b5f8e57504ef04fd52bdabbf63013916101bd92815aba8e359ba1d4d` |
| CI synthetic merge commit | `9e0c01dcc70a37bb3a7027cbf09de005d07f5b8d` |

The final campaign commit changes only an isolated MCP inventory test. Rebuilt
wheels are identical, and the matrix runner, fixture and selected SDK test
definitions were checked for equivalence. Reports retain their real execution
SHA. The full source gate and corrected isolated test ran on `408ec527`.
GitHub's comparison between that head and the CI merge commit has no changed
files. These are earlier runtime proofs, not fresh RC5 release gates or hashes.

## Results

| Check | Result and scope |
| --- | --- |
| Full source gate | 4121 passed, 23 classified skips, 91.46% coverage; schema, lint/types, compile, licenses/dependencies, budgets and quickstart passed. |
| Hosted full Python matrix | Python 3.11–3.14 each passed 4121 tests with 23 skips; coverage 91.46%, 91.46%, 91.46%, 91.41%. |
| Installed matrix | 600/600 logical cells per MCP SDK major, two seeded repeats per cell, completed workers and reaped MCP processes. |
| SDK permissions/options | Per SDK: 771 passed, 6 excluded legacy preservation combinations, including 21 real stdio cases. |
| Finite option pairs | 464/464 defined compatible pairs; 52 behavioral cases plus an invariant over nine representative axes. |
| Isolated registration | Five passed: three common CLI flag placements, configured console tool inventory and offline piped OAuth refusal. |
| Additional delegated CLI | 22 passed: direct format-editor settings/refusals and six operations across three JSON/debug positions on expected-refusal paths. Configuration only, no approval/receipt. |
| Live fictional acquisition | Four PostgreSQL and six Trino routes passed with restricted readers. |
| Hardened containers | Six actual workloads: three targets on AMD64/ARM64; non-root, read-only, network-none, bounded resources and dropped capabilities. ARM64 uses CI emulation. |
| Installed package profiles | 18 passed: base, six optional extras, seven minimum-dependency profiles and four Python wheel-compatibility profiles. |
| Documentation and specifications | Strict MkDocs and all 29 then-current OpenSpec items passed. |

Hosted evidence: [CI, 25 successful jobs](https://github.com/wa-pis/agent-paranoid-android/actions/runs/38913092295),
[containers](https://github.com/wa-pis/agent-paranoid-android/actions/runs/38913092595),
[Security](https://github.com/wa-pis/agent-paranoid-android/actions/runs/38913092444) and
[Documentation](https://github.com/wa-pis/agent-paranoid-android/actions/runs/38913092389).

The installed MCP 1 environment used Python 3.12.13, MCP 1.30.0, Pydantic
2.14.1 and PyArrow 26; MCP 2 used Python 3.12.13, MCP 2.2.0, Pydantic 2.13.4
and PyArrow 25. All 157 installed package files matched the campaign wheel.
Independent AI review closed the confirmed runtime findings; this is separate
from human dataset approval and must be renewed for the final RC5 main SHA.

## Coverage limits and unresolved steps

The 600 logical cells combine ten source handoffs, four outputs, five modes and
Python/CLI/real-stdio MCP. Acquisition is prepared once per source route, then
an independently authored reviewed specification exercises generation semantics.
Database aggregates in this matrix are stand-ins; separate live integrations
establish actual acquisition. This is not 600 live profiling/inference runs.

The 179 typed model properties, 225 top-level CLI flag occurrences, delegated
operation inventory and 131 default MCP argument occurrences are navigation
inventories. Finite pair coverage does not establish every possible value,
all triples or all option combinations. Supplemental CLI refusal tests do not
claim arbitrary internal-exception/debug behavior or per-leaf help coverage.

The 23 full-gate skips comprise ten live integration cases exercised separately,
five isolated composition cases exercised separately, six explicitly excluded
legacy preservation combinations and two inapplicable retained-destination
combinations. Excluded/N/A cases are not counted as passed. Applicable bounded
preservation refusal and destination-refusal checks passed separately.

The required six-container baseline passed. Two supplemental live-Trino runs
inside final containers remain unexecuted after local dependency/network setup
failed; they are outside that baseline and distinct from the successful live
database and installed-process tests. Owned database/container resources were
cleaned up. Temporary fictional test fixtures are retained with local evidence.

Actual Codex plan/inspect calls, exact-specification human review and clean
client completion require their own evidence. Automated SDK/PTY cases do not
provide human approval. Permission to publish RC5 does not close this step.
RC5 requires its own exact-main gates, Ubuntu hashes, signed acceptance and
post-publication verification before the campaign or release is declared complete.
