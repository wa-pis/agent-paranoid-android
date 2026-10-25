# OpenSpec Archive

Completed design changes are retained in the
[OpenSpec archive](https://github.com/wa-pis/agent-paranoid-android/tree/main/openspec/changes/archive).
The archive records accepted proposals, designs, tasks, and capability deltas;
it is implementation history rather than user documentation.

Current product direction is summarized in the [Roadmap](roadmap.md). Public
behavior is described by the canonical
[OpenSpec capabilities](https://github.com/wa-pis/agent-paranoid-android/tree/main/openspec/specs)
and the task-oriented documentation site.

## 2026-10-25 reconciliation

Fourteen completed changes were archived after checking their actual merge,
review and release evidence. Their requirement deltas were integrated into
`openspec/specs` by the normal archive operation; archival did not skip baseline
updates. Nine changes were already complete, and five remaining delivery gates
were reconciled with [1.7.0rc1 public acceptance](release-evidence-1.7.0rc1.md).
Historical checkpoints retain their source identities.

Five changes remain active: external 1.6 feedback intake, historical Trino
configuration evidence, bounded-profile provenance, the separate source-row EAV
extension and selective transformation follow-through. Unavailable historical
settings, live/private acceptance and new preservation authority are not inferred
from release publication. See the [current work plan](https://github.com/wa-pis/agent-paranoid-android/tree/main/openspec/changes).

Baseline reconciliation retains historical RC3 refusal text in its archive and
uses the later accepted edge/load/overwrite contract in current capabilities.
New capability purposes and ADR navigation are filled explicitly; current
release requirements use the authorized candidate rather than a historical
1.6-only version. No executable behavior or authority changes with this cleanup.
