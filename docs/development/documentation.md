# Publishing Documentation

## Tools And Local Preview

Hosting remains **GitHub Pages**. MkDocs renders pages, **mike** owns version
storage, aliases and the version selector, and **mkdocs-print-site-plugin**
assembles the printable handbook. HTMLArk embeds its assets; Chrome prints PDF.
There is no Read the Docs service or separate account to configure.

```bash
uv sync --frozen --only-group docs --no-install-project
uv run --no-sync mkdocs build --strict
uv run --no-sync python -m scripts.build_documentation --output site --verify-release --state-bundle site.bundle
python3 -m http.server --directory site 8000
```

The complete build needs Chrome/Chromium. Pass `--browser PATH` if necessary.
It uses a temporary browser profile and blocks DNS; HTML embedding can read only
resources inside the rendered site. Documentation export never reads datasets,
receipts, credentials or user browser profiles. A plain `mkdocs serve` includes
the print page but does not generate download files.

The small project adapter verifies release evidence, attaches provenance, keeps
legacy root URLs, scopes search and packages downloads. It delegates rendering,
version storage, aliases and selector behavior to the installed tools. The
locked documentation group is separate from runtime package dependencies.

## Versions And Compatibility

| Location | Meaning |
| --- | --- |
| Site root | Maintained guide for the verified stable package; existing URLs work |
| `versions/stable/` | mike's copy alias to the selected stable guide, with selector |
| `versions/X.Y.Z/` | Guide for that exact package version, with its own search index |
| `versions/next/` | Clearly labelled development documentation |
| `documentation.json` | Package version/source, documentation revision and status |
| `downloads/` | PDF, standalone HTML, Markdown source ZIP, selected-version site ZIP |

A package-version guide may receive reviewed documentation corrections while it
is current. Its metadata records the documentation commit separately from the
package release commit. **It is not an untouched snapshot of the release-era
prose**, and it does not inherit the package's exact-SHA review. Once another
package becomes current, older rendered guides remain unchanged unless an
explicitly reviewed correction is published for them. Never relabel today's
prose as guidance for an unsupported historical package.

mike stores generated versions and aliases in the `gh-pages` branch. That branch
is publication state, not a source branch. The root tree is a compatibility copy
of maintained stable guidance; it links to the native version selector. All
other versions have independent search indexes. Historical/maintainer pages
remain available through the history index but are excluded from default search.

Local builds use `refs/remotes/origin/gh-pages` when available. Fetch it first to
retain existing versions, or pass `--state-ref REF` to a local branch containing
previous native state. First publication bootstraps only the current verified
stable package; it does not manufacture earlier snapshots. A `next` build
requires already-published stable state and preserves the complete stable root.

## Publication And Release Gates

1. Finish the existing exact-source package release gates and public verification.
2. Add its stable version, exact release commit and successful public-verification
   run ID to `docs/releases.json`; retain prior catalog entries. Advance `stable`
   only for the publicly verified stable package. RCs stay out of this pointer.
3. Review guides and fictional installed-package examples against that package.
   Run focused documentation checks and inspect the complete export.
4. Merge the reviewed source change. The main-only Pages workflow verifies the
   catalog, builds all formats and publishes the complete Pages artifact.
5. Public verification compares exact metadata, the native stable alias/destination, entry-page hash and all four
   download hashes. **Only after that succeeds** does a separate write-scoped job
   retain the native mike Git bundle in `gh-pages`, without force-pushing.

PR builds have read-only repository permissions and never push state. Complete
main publications are serialized. Build/export failure leaves the deployed site
untouched. A failure after Pages deployment requires restoring a retained prior
successful Pages artifact; public verification is not an atomic deployment and
there is no automatic rollback. If retaining mike state fails after successful
verification, restore the matching `documentation-mike-state` workflow artifact
before another publication, so version history is not lost. Artifacts are retained
for 90 days; `gh-pages` retains published version history.

Builds use a disposable Git repository and cannot change a developer's branches.
Local site replacement is staged and restores the prior output on handled errors
or interruptions. If another writer prevents restoration, recover the preserved
sibling `.apa-docs-backup-*` directory manually.

## Checks

```bash
uv run --no-sync pytest tests/test_documentation.py tests/test_documentation_build.py
uv run --no-sync mkdocs build --strict
```

Tests require both the documentation group and development test dependencies.
The PDF and standalone HTML contain the current navigation's user chapters,
excluding history, roadmap and documentation administration. The Markdown ZIP
preserves the full documentation source tree so reference links remain reusable;
historical pages keep their original provenance. The site ZIP contains one
selected version, without recursively including other versions or its own ZIP.


## Russian Edition

`docs/ru/` mirrors current user-guide paths. Keep translated command blocks and
review gates synchronized with their English counterpart; untranslated specialist
API tutorials and historical records must be labelled English rather than
presented as translated content. `docs/ru/quality-report.md` records example and
build evidence, including checks that were not run.

The existing theme switches to the Russian navigation for `ru/` pages. Its
English / Русский links resolve within the current mike version; a missing
counterpart falls back to the other language's home with an explicit label.
Markdown language links also work in the repository. Built-in search indexes
both English and Russian, while the history classification normalizes `ru/`.
No new localization plugin or runtime dependency is required.

The combined PDF/HTML handbook is bilingual. Print-site and the export chapter
manifest exclude history, roadmap, downloads and versions for both languages.
Markdown and offline-site ZIPs include both editions. Do not make language
switches point to the unversioned production root: that would silently change
the package version when reading an older guide.
