# Progress: CPython 3.15 Support

## 2026-11-08 — Proposal Prepared Offline

The owner requested an OpenSpec for Python 3.15. Inspected package metadata,
quality/wheel matrices, runtime support and dependency compatibility policies.
Prepared proposal, design, tasks and delta requirements. No runtime, dependency,
classifier, support claim or CI job has changed.

Local base: fd7a9c8b014cd295c2d814afde6a1618b2781515, the feature head of merged
PR #691. The merge object and newer main are not locally available; network
outage prevents refreshing remote state. Original dirty workspace is preserved;
this work uses the isolated `codex/python-315-support-spec` branch.

Blocked checks: official Python release status, dependency/wheel availability,
remote-main synchronization and push need network access. No Python 3.15 test
result, human acceptance or release evidence is claimed.

Local verification passed: `openspec validate python-315-support --strict` and
`tests/test_documentation.py::test_completed_openspec_changes_are_archived_and_baselined`
(1 passed, 0.78 s), plus whitespace checks. The catalog test includes the new
active change. No full runtime suite was repeated for this specification-only
change. Next: verify official status and reconcile with current main after
connectivity returns before implementation or publication.

## 2026-11-08 — Connectivity And Official Status Verified

Network access recovered. Fetched origin/main at
18cba3235752717632b511577fcab81517daa09c (merged PR #691) and rebased this
specification branch on it without conflicts. The original dirty workspace
remains untouched.

Verified the official [3.15.0 release page](https://www.python.org/downloads/release/python-3150/)
and [PEP 790](https://peps.python.org/pep-0790/): stable 3.15.0 shipped
2026-10-09; 3.15.2 is listed as released 2026-10-26. Updated the proposal and
tasks to select blocking stable-version CI as the implementation path. This
verifies release status only, not installation or project compatibility.

Remaining implementation work: audit dependency/native-wheel availability,
install a recorded stable interpreter, and execute the compatibility matrix
before changing support claims. No runtime implementation or release has been
performed by this specification-only change.

## 2026-11-08 — Implementation Deferred By Owner

The owner requested stopping and deferring the update. The local verification
process was interrupted; the full release gate did not complete and no 3.15
support is claimed. Work remains uncommitted in this isolated worktree; no
implementation was pushed, merged, tagged or published.

Before stopping, verified a standard GIL-enabled CPython 3.15.2 standalone
build (20261026, macOS arm64), archive SHA-256
285a6b924713bec9c1cdf442ba5ebfbafbab070060b34d607c30546b758e64a6.
The previous lock lacked 3.15 PyArrow wheels and attempted a source build that
failed for missing Arrow C++ development files. Targeted local lock updates
installed all extras successfully: Pydantic 2.14.3/core 2.50.4, PyArrow 26.0.1,
jiter 0.19.0, orjson 3.13.0, librt 0.16.0, typing-inspection 0.4.5. Some other
native dependencies built locally; wheel-only installation is not proven.

Local drafts extend CI matrices and compatibility policy/tests. Lint, typing,
compilation, license/compatibility policy and 19 focused privacy/SQL checks
passed. The full suite was interrupted during collection before running tests. No dependency
range or runtime support classifier has changed. Do not mark implementation
tasks complete. Resume only when requested, starting with current git/remote
state and the remaining dependency/platform/test evidence.

## 2026-11-08 — Owner Resumed Implementation

The owner explicitly resumed Python 3.15 support. A new isolated branch
`codex/python-315-support` starts from final main
4e1651c6fe9f5573f280ef6497701a98f46d022e; the deferred worktree and unrelated
workspace edits remain untouched. Rechecked the official release page and
PEP 790: standard GIL-enabled CPython 3.15.2 is stable. Local interpreter is
3.15.2, Clang 23.1.3, standalone build 20261026, macOS 26.6.2 arm64.

Regenerated the lock with uv 0.11.23: only Pydantic 2.14.3/core 2.50.4,
PyArrow 26.0.1, jiter 0.19.0, orjson 3.13.0, librt 0.16.0 and
typing-inspection 0.4.5 changed versions. Retained merged GigaChat 0.2.4,
Hatchling 1.33.0, pinned workflow actions and the security bootstrap fix.
No runtime dependency range or Python 3.11 minimum profile changed.
PyPI metadata confirms cp315 wheels for core/Arrow/jiter/orjson/librt on
macOS and Linux x86_64/aarch64. This is availability evidence, not execution
on another platform. PyYAML 6.0.3 has no cp315 wheel; binary-only resolution
fails explicitly. Normal source installation succeeds locally; documentation
records the possible compiler requirement rather than claiming wheel-only support.

Built wheel/sdist and verified base, parquet, mcp, trino, postgres, openai,
gigachat and all in eight clean CPython 3.15 environments outside the checkout.
Every installed-package check and `doctor` passed, including optional capability
checks. These unconstrained installs test the declared ranges; the full suite
uses the reviewed frozen lock. No external databases/providers were contacted.

Lint, type checking, compilation, license/compatibility policy and 19 direct
privacy/SQL tests passed. Focused packaging/compatibility/runtime documentation:
29 passed. Strict OpenSpec validation passed. First full-suite run in the
restricted process environment rejected controlling-TTY fixtures. The exact six
batch confirmation tests pass with normal terminal access, with no code change
or relaxed approval check. The full gate is being repeated with that access;
Linux CI and previous-runtime compatibility remain pending. No release is made.

### Full Local Gate And Linux Tooling Correction

Source b2935188b69c3d7245825abfb73cf753603d93cc passed the complete
`scripts/check_release.sh` under CPython 3.15.2/macOS arm64 with terminal access:
4856 passed, 26 skipped, 2 warnings, 92% coverage, 179.12 seconds for the suite.
Operational budgets, both schema freshness checks and synthetic quickstart
passed. Existing opt-in live integrations remained skipped. The separately
rechecked terminal/MCP transformation files passed 217 tests with 4 skips.
The restricted run's eight failures were terminal-access failures; no runtime
code or approval gates changed. The rebuilt wheel includes the 3.15 classifier
and unchanged `Requires-Python: >=3.11`.

PR #693 started Linux CI. All isolated optional/base/all wheel checks, including
3.15, passed. Python 3.15 quality failed before project tests because pip-api
0.0.34 vendors a parser importing removed `sre_constants`. Targeted update to
pip-api 0.0.35 (development/audit dependency only) restores `pip_audit --version`.
This is the eighth changed lock package; no runtime package/range changed.
License/compatibility checks and the 30 focused tests pass with this update.
Full hashed audit and refreshed CI remain pending; promotion is not yet complete.

### Verified Implementation And Promotion Evidence

Implementation source: 76bfa0ecdaf1d9fed5fde76b3ec051e90cec66d3, PR
[#693](https://github.com/wa-pis/agent-paranoid-android/pull/693).
All 47 applicable checks passed on that exact head, with no pending or failed
checks and a clean merge status. The final follow-up records documentation
and task evidence only; it does not change the verified implementation.

[Linux CI run 42488490529](https://github.com/wa-pis/agent-paranoid-android/actions/runs/42488490529)
passed full Python 3.11, 3.12, 3.13, 3.14 and 3.15 jobs, every minimum profile,
base/all wheel compatibility and every optional-extra install profile.
Python 3.15.2 Linux x86_64: 4857 passed, 25 skipped, 2 warnings, 92% coverage,
443.11 seconds. These include both scalable engines' 1/2/4-worker and batch
comparisons, cancellation/resource/recovery/cleanup contracts and real SDK
stdio tests. Prior macOS arm64 full-gate results above cover the other
execution platform. Hash-checked pip-audit passed locally and in each Linux
quality job; no known vulnerabilities were found. No audit was skipped,
allowed to fail or moved to an older interpreter.

Public metadata, blocking CI and English/Russian support/dependency/release
guidance now include standard CPython 3.15. Python 3.11 minima, older jobs,
source-free generation, workspace/SQL/approval gates and budgets remain intact.
PyYAML source-build availability is explicitly documented. No free-threaded,
alternate interpreter, new platform, cross-Python byte identity or speedup is
claimed. Implementation is verified; a future RC still needs its separate
authorization, exact-release review/preflight/publication gates and artifacts.
