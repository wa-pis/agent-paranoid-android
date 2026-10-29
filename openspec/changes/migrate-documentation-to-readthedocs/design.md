# Read the Docs migration design

## Existing components

- `mkdocs.yml`: readthedocs theme, bilingual search, mike and print-site.
  The theme name is not a hosting connection.
- `scripts/documentation_hooks.py`, `docs/theme/`: Pages-specific canonical
  URLs, stable/version selector, page identity and portable HTML handling.
- `scripts/build_documentation.py`, `docs/releases.json`: accepted release
  catalog, version composition, exports and identity/hash manifests.
- `.github/workflows/docs.yml`: frozen installation/licenses, contracts,
  strict build, version/export generation, Pages deployment, public verification
  and retained mike state. Inventory exact callers before implementation.
- `tests/test_documentation.py`, `tests/test_documentation_build.py`:
  extend existing contracts rather than replacing them with host smoke alone.

## Approach

First prove a parallel native MkDocs build with supported pinned tooling and
frozen dependencies. Reuse existing content and export helpers; check service
plan support, quotas and system dependencies before choosing settings. Keep
GitHub CI's strict documentation and release acceptance checks.

Read the Docs manages online versions, with an explicit mapping to the verified
release catalog. `latest` denotes development, not a published package; an RC
is labelled separately. Disable or constrain automatic stable promotion so a
new tag or successful host build alone cannot advance the verified default.
Keep package version/source and documentation revision separate on pages and
in manifests. Preview metadata grants no release acceptance.

Historical immutable tags may lack the new config. Use reviewed documentation
refs based on matching verified edition content plus hosting integration,
retaining original package identity; otherwise retain the verified Pages
snapshot. Never rewrite release tags or relabel main as an older edition.

Adapt canonical links, selectors and version-local search to actual host URLs.
Retain mike only where needed for legacy Pages or offline packaging; avoid two
independent stable authorities. Preserve existing exporters: MkDocs hosting
alone does not prove equivalent PDF, HTML, Markdown or offline-site downloads.
PR previews may omit downloads when labelled; normal editions require all four.

Connect/import through the maintainer's Read the Docs account using minimum
GitHub integration access. Document account-only settings and owner actions;
never request/store/print passwords or tokens. Untrusted PR builds receive no
private variables, production inputs or verified-edition publication authority.
Exercise both successful and failing fictional PRs with visible build status.
No paid plan or custom domain is assumed by this proposal.

Before switching canonical links, verify stable/candidate/development identity,
bilingual navigation/search, historical links/anchors, cross-version isolation
and downloaded artifact hashes against public release evidence. Retain old
Pages URLs via retained editions or tested link mappings. Rehearse restoration
of known-good Pages output; remove redundant publication steps only after the
replacement and recovery are verified. Do not remove required checks/exports.

## References

- https://docs.readthedocs.com/platform/stable/intro/mkdocs.html
- https://docs.readthedocs.com/platform/stable/config-file/v2.html
- https://docs.readthedocs.com/platform/stable/pull-requests.html
- https://docs.readthedocs.com/platform/stable/automation-rules.html
