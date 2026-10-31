# Publishing Documentation

## Tools And Local Preview

Hosting remains **GitHub Pages**. MkDocs renders pages, **mike** owns version
storage, aliases and the version selector, and **mkdocs-print-site-plugin**
assembles the printable handbook. HTMLArk embeds its assets; Chrome prints PDF.
Read the Docs integration is being prepared in parallel; no host switch or
verified Read the Docs project URL has been recorded. The theme name alone does
not connect a service. See [parallel hosting preparation](#parallel-read-the-docs-preparation).

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
| `versions/X.Y.ZrcN/` | Exact release-candidate guide, explicitly not stable |
| `versions/next/` | Current development guide or copy alias of the latest RC |
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
stable package; it does not manufacture earlier snapshots. A development or RC build
requires already-published stable state and preserves the complete stable root.
RC builds retain their exact version directory and move only the `next` copy
alias; later candidates preserve earlier RC directories. RC identity binds to
its tag commit once available and otherwise to the candidate source. The label
does not claim successful package publication or public acceptance.

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

## Parallel Read the Docs Preparation

The active OpenSpec is `migrate-documentation-to-readthedocs`. GitHub Pages
remains the accepted publication while service access and public acceptance
are incomplete. The reported connected-service failure has no confirmed cause;
no successful account connection or imported project is recorded here.

### Reuse And Host Responsibilities

| Existing component | Parallel build decision |
| --- | --- |
| `mkdocs.yml`, `docs/`, bilingual theme/search | Keep; use the host-provided edition canonical URL |
| `scripts/documentation_hooks.py` | Reuse identity, scoped search, chapter inventory and all four exporters |
| `docs/releases.json` | Keep accepted stable package identities; a host alias cannot replace release evidence |
| `scripts/build_documentation.py` | Retain Pages/mike publication, compatibility root, snapshots and atomic local output |
| `scripts/build_readthedocs.py` | Render one isolated edition; no mike tree, deployment credentials, default changes or Pages writes |
| `.github/workflows/docs.yml` | Retain licenses, strict builds, focused contracts, release verification, Pages deployment and public checks |
| `scripts/verify_documentation.py` | Retain all existing public Pages checks; its mike-specific mapping is not an RTD acceptance check |
| Pages build artifacts and `gh-pages` | Retain recovery bundle, rendered output and existing 90-day retention; no cleanup during parallel testing |

Normal RTD builds use the same PDF, standalone HTML, Markdown ZIP and offline
site ZIP exporters. `documentation.json` preserves package version, package
source and documentation revision separately. A development build can describe
a released candidate while having a newer documentation revision. A tagged
build must match a clean checkout and its package tag. A stable tag is labelled as awaiting public acceptance; its build alone does
not prove a public release or agreement with the accepted catalog. This
builder does not establish an accepted stable/default mapping.

PR builds (`READTHEDOCS_VERSION_TYPE=external`) have a visible preview label,
`noindex`, and bilingual download pages explaining that downloads are omitted.
They do not install the export browser. Normal builds require all four exports;
a failed strict build/export leaves the previous local output intact.

### Tooling And Local Reproduction

`.readthedocs.yaml` selects Ubuntu 24.04, Python 3.12 and uv 0.11.23.
Installation uses the frozen docs-only dependency group without installing the
application. Playwright is a docs-only browser distributor; its locked version
selects Chromium for the existing PDF exporter. It does not automate accounts
or use a user's browser profile. License checking runs before rendering.

```bash
uv sync --frozen --only-group docs --no-install-project --python 3.12
uv run --no-sync python scripts/check_dependency_licenses.py
uv run --no-sync playwright install --no-shell chromium
READTHEDOCS_VERSION_TYPE=branch \
READTHEDOCS_GIT_IDENTIFIER=main \
READTHEDOCS_CANONICAL_URL=https://example.invalid/en/latest/ \
uv run --no-sync python -m scripts.build_readthedocs --output /tmp/apa-rtd/html
```

Package tags are fetched explicitly after checkout so shallow service clones
do not silently lose released package provenance. The example URL is fictional,
not a deployed project. On the host, the builder
uses `READTHEDOCS_CANONICAL_URL`, verifies `READTHEDOCS_GIT_COMMIT_HASH` against
the checkout, and writes HTML plus downloads under `READTHEDOCS_OUTPUT/html`.
Ubuntu browser libraries and fonts are declared through RTD's supported
`build.apt_packages`, based on the locked Playwright Chromium dependency list;
installation does not require an ad hoc privileged shell command. Actual service execution and build time must
still be verified; a local build does not prove the hosted environment works.

### Account Setup And Acceptance Still Required

The Community service documents a 15-minute build limit, 7 GB memory and two
concurrent builds. Confirm the actual account plan before import. Owner actions
remain: connect the GitHub integration with only the intended repository,
inspect the exact requested permissions, import the public repository, record
the real project URL, configure version activation/defaults, and enable PR
checks. Do not store private environment variables or publishing credentials
in preview builds. A paid plan, custom domain or broader repository access is
not assumed.

Do not let automatic `stable` tag selection act as release acceptance. Before
switching any canonical/default URL, the remaining work must prove accepted
stable/candidate/development mappings, faithful historical documentation refs
or retained snapshots, public release evidence, bilingual navigation/search,
old links and anchors, all four downloaded hashes and rollback. Immutable old
tags lacking host configuration stay intact.

Read the Docs can inject add-ons into served HTML. The current Pages verifier
checks the exact entry-page bytes as well as download bytes: host injection
must be resolved and verified against actual served output, not accommodated
by silently dropping the entry-page integrity check. No host acceptance or
retirement of Pages is implied by a successful local build.

References: [configuration](https://docs.readthedocs.com/platform/stable/config-file/v2.html),
[environment](https://docs.readthedocs.com/platform/stable/reference/environment-variables.html),
[build limits](https://docs.readthedocs.com/platform/stable/builds.html),
[PR previews](https://docs.readthedocs.com/platform/stable/pull-requests.html),
[browser versions](https://playwright.dev/python/docs/browsers).
