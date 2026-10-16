# Cross-interface Acceptance Evidence For RC5

## Status and identities

The historical automated runtime campaign passed before RC5 preparation. Human
Codex acceptance and RC5 publication remain open. This document records what
actually ran, without treating a previous artifact as a newly built RC5 wheel.
The [plan](acceptance-matrix.md) and [release process](release.md) still apply.

## Exact RC5 candidate checkpoint

On 2026-10-16, [PR #623](https://github.com/wa-pis/agent-paranoid-android/pull/623)
merged as frozen main `890925afdff68e97cafe38a28605d2874c9dad79`. Its tree
`a2f57bba64603b4ae2a39c97f958c506315e630c` matches repaired reference
`cd4f1cdba042862909fc9ccfe06fc52e4389e622`. The following are candidate checks;
RC5 remains untagged and unpublished. Later documentation commits do not change
these source identities or inherit their results.

| Exact-main check | Result and evidence |
| --- | --- |
| Full local gate | 4197 passed, 23 classified skips, no failures, 91.49% coverage; schema, lint/types, compile, licenses/dependencies, budgets and quickstart passed. |
| Documentation and OpenSpec | Strict MkDocs passed; all 30 then-current OpenSpec items passed strict validation. |
| CI | [Main workflow](https://github.com/wa-pis/agent-paranoid-android/actions/runs/38923245358): Python 3.11–3.14 each passed 4197 tests with 23 skips; coverage 91.49%, 91.49%, 91.49%, 91.44%. Eighteen installed package profiles, four PostgreSQL routes and six Trino routes passed. |
| Containers | [Main workflow](https://github.com/wa-pis/agent-paranoid-android/actions/runs/38923245187): six actual hardened workloads across three targets and AMD64/ARM64 passed. |
| Documentation | [Main workflow](https://github.com/wa-pis/agent-paranoid-android/actions/runs/38923245368) passed. |
| Security | [Main workflow](https://github.com/wa-pis/agent-paranoid-android/actions/runs/38923245355) passed. |
| Installed matrices | Fresh exact-main runner/fixture: 600/600 logical cells on each of MCP 1.30.0 and 2.2.0, two seeded repeats per cell; workers completed and MCP processes were reaped. |
| Independent AI source review | Exact-main technical approval recorded in [PR #623](https://github.com/wa-pis/agent-paranoid-android/pull/623), subject to separate manual and release gates. Decision record SHA-256: `2ff4128de6dfe767f878b0347d61db38b4cf328276fcf08bcb4cb5eb6f4f030b`. This is not human dataset consent or a GitHub-required human approval. |
| Ubuntu no-publish preflight | [Exact-main run](https://github.com/wa-pis/agent-paranoid-android/actions/runs/38923785970) passed with Python 3.12.15: 4197 passed, 23 skips, build and installed-wheel checks. Downloaded wheel/sdist hashes were independently verified. |

The focused SDK suites ran separately on `cd4f1cdba042862909fc9ccfe06fc52e4389e622`:
847 passed and six legacy combinations excluded per SDK. Their 24 referenced
test/configuration files and all 157 package payloads were verified identical
at main. Those focused results retain their actual `cd4f1cdb` execution identity;
they are not described as fresh main execution. The 600-cell matrices above
were rerun for main. Their acquisition and finite-coverage limits remain those
described below.

Ubuntu publication-preflight artifacts:

| Artifact | SHA-256 |
| --- | --- |
| `agent_paranoid_android-1.6.0rc5-py3-none-any.whl` | `969f969d57c0c87784cf7708d165507d8c3cd34eb41dccccaff43bdd08dea6d1` |
| `agent_paranoid_android-1.6.0rc5.tar.gz` | `d2011e802d64157e9351805e94f97e2202b4c52a7c14511f6b6973b1079d3ae8` |

The separate macOS manual-client wheel has SHA-256
`b32e459cd7a346bba2dc47e2caf61760c7fb8d35327cd486d286667389551368`.
All 162 wheel members, including 157 package files, match the Ubuntu wheel in
content; only ZIP timestamps differ. The macOS hash is not the publication
preflight hash.

An actual Codex CLI `0.162.0-alpha.17.2` planning call was observed. The final
authored specification was installed afterward. Earlier consent predating that
file does not approve it. The existing conversation can be
[resumed](how-to/mcp.md#resume-an-existing-synthetic-plan), but resume/configuration
preflight and mocked launcher checks are preparation only. Fresh actual-client
inspection, full current-file human review, new specific consent, generation,
validation, artifact verification and client completion remain unresolved.
No signed acceptance/tag, publication or public-release verification is claimed.

## Historical campaign identities

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
Independent RC5 review subsequently found unbounded DECIMAL fixed-point
formatting in typed Parquet and its controlled-invalid fallback. The correction
uses one bounded converter across validation and output adapters. That runtime
change superseded version-only equivalence and required fresh installed-matrix
and full release gates on the corrected RC5 candidate. The candidate checkpoint
above records those reruns. Results below remain the historical campaign
baseline, not acceptance of the correction.

## Historical campaign results

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

Actual Codex inspection, exact-specification human review and client completion
require their own evidence beyond the observed planning call. Automated SDK/PTY
cases do not provide human approval. Permission to publish RC5 does not close
this step. The current exact-main gates and Ubuntu hashes above do not replace
signed acceptance, publication or post-publication verification. The separately
gated transformation/session campaign also remains open; this ordinary synthetic
run grants no preservation authority or claim of complete campaign acceptance.
