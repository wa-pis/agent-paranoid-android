# Design: Versioned, task-oriented documentation

## Approach

1. Inventory pages as current task guides, canonical reference, concepts,
   maintainer material, migration guidance or historical evidence. Record a
   keep/merge/shorten/archive decision and replacement URL for each moved page.
2. Keep the primary journey focused on purpose, installation/demo, preparing a
   dataset, business rules, reviewing output, selective transformation and
   troubleshooting. Explain generation versus transformation before commands.
   Link CLI/Python/MCP choices and source/output matrices at the relevant step.
3. Consolidate repeated settings into their canonical reference. Replace release
   narratives in ordinary guides with a short applicable-version note and a
   link. Retain safety preconditions at the point of action.
4. Group historical release and RC evidence behind an explicit history entry.
   Keep it accessible without listing every old release in primary navigation.
   Scope default search to the selected documentation version; search/archive
   results must identify historical or prerelease material.

## Version And Publication Contract

- Default entry resolves to the latest publicly verified stable release, with
  its exact package version visible. Existing unversioned links remain usable.
- Each newly published release gets a guide recording the exact package source
  commit and the documentation revision separately. Later reviewed documentation
  corrections do not inherit runtime review. Documentation and DatasetSpec schema
  versions are distinct.
- A version selector exposes available stable snapshots and an explicit archive.
  Old pages identify their version and link to current stable documentation.
- Unreleased/prerelease documentation, if published, has a separate entry and
  visible status. It must not replace the stable default or imply availability
  in the selected stable package. RC evidence belongs to history/maintainers.
- Do not label today's main-branch prose as documentation for an older release.
  Only expose historical snapshots that can be built and identified honestly;
  retain existing historical evidence separately when no snapshot is available.
- Retain immutable release/review artifacts unchanged. Later documentation
  corrections are identified as corrections and do not inherit exact-SHA review
  or runtime acceptance from a release. A maintained version guide is not claimed
  to be untouched release-era prose.
- The release workflow builds matching docs, checks version metadata, internal
  links, installed-package examples and the deployed version. Move the stable
  pointer only after public release verification and docs checks pass. A failed
  deployment leaves the prior known-good default available.

Use **mike** with the existing MkDocs/Pages hosting. It owns rendered version
storage in `gh-pages`, the `versions/versions.json` index, aliases and the native
readthedocs-theme selector. Copy aliases avoid symlinks in Pages artifacts.
The unversioned root remains maintained stable content for link compatibility;
its banner links to `versions/stable/` and the native selector. `versions/X.Y.Z/`
identifies the package guide; `versions/next/` is explicitly development-only.
Old rendered package guides are retained without rebuilding. Current-version
guides can receive reviewed corrections with a new documentation revision;
they are not represented as immutable original-release source snapshots.

`docs/releases.json` is a release-evidence gate, not another version store.
The main-only workflow checks its exact package source and successful public
verification run. The adapter invokes standard tools inside a disposable Git
repository, leaving the developer's branches alone. Preview builds preserve the
previous stable root from published state and fail if stable state is absent.

Complete main publications are serialized. Build/export failures leave the
public site untouched. After Pages deployment, public verification compares
metadata and entry/export hashes. Only then can the separate write-scoped job
retain mike's native Git bundle, with no force push. PR builds remain read-only.
Failures after Pages deployment require restoring a retained successful artifact;
no atomic public check or automatic rollback is claimed. If state retention
fails, recover the matching workflow artifact before another publication.

## Portable Documentation

**mkdocs-print-site-plugin** assembles the user-navigation handbook, excluding
history, roadmap and documentation administration. **HTMLArk** embeds its local
assets; Chrome's standard print command produces PDF in a temporary isolated
profile with DNS blocked. The adapter corrects the print plugin's links to
references omitted from the book into explicit selected-version website links;
it does not implement another Markdown renderer or version selector.

Provide PDF, standalone HTML, a full Markdown documentation source ZIP and a
selected-version offline site ZIP. Keeping the complete source tree avoids a
separate custom Markdown link-rewriting mechanism. Historical source remains
labelled and distinct from the handbook. The manifest identifies package
version/source, documentation revision, chapter inventory and artifact hashes.
The ZIP excludes its own archive to avoid recursive packaging. Browser search
in an extracted site uses a local HTTP server. Export never reads datasets or
approvals. Build in staging, verify links/text and inspect the rendered PDF.

## Acceptance And Failure Modes

Verify routes from the stable entry point to demo, CSV generation, related
tables, business rules, PostgreSQL/Trino, CLI/Python/MCP, transformation and output
review. A reader must not need an RC acceptance page to complete a stable task.
Check representative old URLs/anchors and selected-version search isolation.
Run strict documentation build, focused documentation contracts and fictional
installed-package examples. Record before/after navigation and duplicated
content removed; use representative user walkthroughs to assess usefulness.

If moving a page breaks a link or hides a safety condition, retain a bridge or
fix the destination before removal. If sources disagree about current status,
resolve against version-bound release evidence and public contracts; do not
rewrite historical decisions to make them appear current.
