# Change Proposal: Versioned, task-oriented documentation

## Summary

Make the latest stable release the default documentation experience. Shorten
the main navigation, consolidate repeated explanations, and move old-release,
RC, review and publication material out of the everyday user journey. Add
explicit documentation versions so readers can distinguish installed behavior,
historical guidance and unreleased work.

Status: implemented with standard MkDocs plugins and locally verified; public
deployment pending. The owner requested
execution of the plan and added PDF/other offline exports on 2026-10-22.
Public deployment and its exact-revision verification remain separate steps.

## Motivation

Owner feedback: documentation is excessive and offers too little practical
help, especially because old versions and RC details dominate current guidance.
During preparation of the project overview, `docs/roadmap.md` still described
preparing stable 1.6.0 while `docs/1.6.0-release-status.md` recorded publication.
The main MkDocs navigation also exposes several historical RC/acceptance pages.

Readers need to understand the purpose, choose generation or transformation,
complete a task, and find the relevant reference without reconstructing release
history. This implements the accepted direction in ADR-0028.

## Scope

- A compact stable entry point and task-oriented navigation.
- Canonical references instead of duplicated evolving settings and release prose.
- Version-labelled documentation, a stable default and an explicit archive.
- A separate maintainer/history entry for release, RC and review evidence.
- A release procedure that publishes the matching docs and verifies the stable
  pointer, links and version identity.
- Reconcile current claims against release evidence, including completed work
  still presented as a future plan.
- Keep GitHub Pages and use mike for version storage, aliases and selector.
- Export the user handbook through print-site as PDF and standalone HTML, plus
  Markdown source and selected-version site ZIPs, bound to package/docs identity.

Out of scope: runtime/API/schema changes, activating extensions, approving
datasets, changing accepted architectural decisions, deleting or rewriting
immutable release/review evidence, or manufacturing snapshots for old versions.

## Safety Impact

Keep actionable safety conditions beside the relevant operation. Consolidation
must preserve source-free generation, separate mixed-origin transformation,
read-only bounded database access, and exact local preservation approval.
Registration, successful release checks and a documentation version never
authorize a dataset. Historical evidence retains its original source identity.

## Compatibility

CLI, MCP, DatasetSpec and artifact contracts remain unchanged. Preserve existing
documentation links through retained pages, aliases or redirects. Legacy
migration guidance stays discoverable from the applicable version; stable
examples must match the selected released package.
