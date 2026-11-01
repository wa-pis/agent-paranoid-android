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

Four changes remain active: external 1.6 feedback intake, historical Trino
configuration evidence, bounded-profile provenance and selective transformation
follow-through. Source-row EAV pivot/unpivot remains deferred in the roadmap,
outside the completed synthetic EAV slice. Unavailable historical
settings, live/private acceptance and new preservation authority are not inferred
from release publication. See the [current work plan](https://github.com/wa-pis/agent-paranoid-android/tree/main/openspec/changes).

Baseline reconciliation retains historical RC3 refusal text in its archive and
uses the later accepted edge/load/overwrite contract in current capabilities.
New capability purposes and ADR navigation are filled explicitly; current
release requirements use the authorized candidate rather than a historical
1.6-only version. No executable behavior or authority changes with this cleanup.

The historical activation-composition fixture retains its executable/contract
tail byte-for-byte. Its maintained documentation projection was refreshed for
the corrected architecture page so forward/reverse composition remains tested;
this is not a new activation patch applied to production.

Continued feedback work also reconciles nine completed transformation delivery
tasks and their public-contract subtask with actual stable/candidate evidence.
The [remaining scope and installed replay](https://github.com/wa-pis/agent-paranoid-android/blob/main/openspec/changes/selective-source-transformation/release-1.7-reconciliation.md)
retain the original source identities. A subsequent [installed feedback replay](feedback-acceptance-1.7.0rc1.md)
closes the findings 1–26/section E matrix and reviewed-script replay; three
transformation composite tasks remain unchecked.

The completed conditional-formula/source-free EAV change was also archived,
bringing this reconciliation to fifteen archives. Its exact requirement delta
already matched the business-rules baseline, so the normal archive operation
needed no duplicate specification update. The deferred source-row operation is
explicitly retained in both roadmaps; it was not implemented or accepted by
archival.


## 2026-11-01 hosting decisions

The Cloudflare proposal is archived as **cancelled**, and the earlier RTD
proposal as **superseded**. These are disposition archives, not completed
capabilities. Historical incomplete checkboxes remain open. Both were archived
with `--skip-specs`; neither unaccepted hosting delta was applied to the baseline.
The baseline records the maintainer's final choice of GitHub Pages, while its
existing edition/export/public-verification requirements remain intact.

[PR #683](https://github.com/wa-pis/agent-paranoid-android/pull/683) restored links
and new canonicals; [Documentation 41336088977](https://github.com/wa-pis/agent-paranoid-android/actions/runs/41336088977)
passed main build, publication, public verification and retained mike versions.
Both Cloudflare publishers are disabled; their projects and historical snapshots
are retained. RTD project-build retirement remains manual owner follow-up and
its configuration is retained until confirmed. No migration acceptance or
package promotion is inferred from these archives.
