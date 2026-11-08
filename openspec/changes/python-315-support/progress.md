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
