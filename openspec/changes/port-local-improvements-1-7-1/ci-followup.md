# PR #718 CI Follow-up — 2026-11-25

This supplements the frozen local reports; it does not rewrite them. Machine-readable results and every check/job link are in [ci-followup-checks.json](ci-followup-checks.json).

## Exact Source

[PR #718](https://github.com/wa-pis/agent-paranoid-android/pull/718), branch `codex/port-local-improvements-1-7-1`, was checked at **`0529fb43ce1dbe85bb948623f83a66ac58500fdd`**. GitHub reported the PR open, mergeable and clean when this metadata was collected. These results belong to that SHA; the later commit adding this report is outside the recorded CI snapshot.

Three follow-up fixes are included:

- [`c855178b`](https://github.com/wa-pis/agent-paranoid-android/commit/c855178bd2eaaac03dcff0d634bb662aaa71fe5a): align local database examples with query-source policy 1.2.
- [`b8fc1c2b`](https://github.com/wa-pis/agent-paranoid-android/commit/b8fc1c2bfcaa63becebb8e8ae8cb10b314ebda2e): scope the three independently verified secret-scan false positives to immutable fingerprints.
- [`0529fb43`](https://github.com/wa-pis/agent-paranoid-android/commit/0529fb43ce1dbe85bb948623f83a66ac58500fdd): configure private DuckDB scratch before disabling external access; retain pre-ingestion denial, limits and failure cleanup.

## Completed CI

**51 passed, 5 skipped, 0 failed or pending.** All four workflow runs report the exact head SHA above and conclusion `success`.

| Workflow | Passed | Skipped | Run |
| --- | ---: | ---: | --- |
| CI | 36 | 0 | [45562814769](https://github.com/wa-pis/agent-paranoid-android/actions/runs/45562814769) |
| Containers | 7 | 2 | [45562814738](https://github.com/wa-pis/agent-paranoid-android/actions/runs/45562814738) |
| Documentation | 2 | 3 | [45562814811](https://github.com/wa-pis/agent-paranoid-android/actions/runs/45562814811) |
| Security | 4 | 0 | [45562814933](https://github.com/wa-pis/agent-paranoid-android/actions/runs/45562814933) |
| External status contexts | 2 | 0 | Individual links in the JSON |

The CI matrix includes Python 3.11–3.15, optional and minimum dependency wheel profiles, PostgreSQL/Trino integration, container checks and ARM64 validation. The five skipped results are retained individually in the JSON and are not counted as passes.

## Local Results

Aggregate metadata was parsed from the saved local JUnit and coverage files, without reading test values or logs:

- Primary run: **6,252 passed, 25 skipped, 8 failed**, with no errors. The eight failures came from controlling-TTY availability in that execution environment.
- Separate controlling-TTY rerun: **8 passed**, with zero failures, errors or skips.
- Coverage: **92.24058345642541%**, 19,983 covered of 21,664 statements.

These are two local invocations, not a claim that the primary invocation was failure-free. The current GitHub checks above are independently green.

## Scope

The earlier reports remain source-bound historical evidence, including [final-review.md](final-review.md) and its `1a40ad08` manifest. No source-file hash map is duplicated here. No raw CI logs, fixture values or credentials were retrieved. Large benchmarks are outside this CI snapshot; earlier timing results do not establish performance for this SHA. Green checks do not replace human review or authorize a release, dataset approval or new transformation activation.

A separate [fresh public CSV campaign](public-csv-current.md) now measures this
same implementation. Its 16 runs and 127 focused tests are additional local
evidence, not part of the CI snapshot above.
