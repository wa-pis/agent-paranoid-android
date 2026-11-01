# Tasks: migrate-documentation-to-cloudflare-pages

The maintainer selected Cloudflare on 2026-11-01. RTD evaluation is retained as
partial evidence, not a completed/archived migration. Account existence is
confirmed; the Direct Upload project and owner-installed GitHub secret are now
configured. Live upload/verification evidence is scoped below; full migration
acceptance remains incomplete.

- [x] Carry forward the existing identity/export/release/recovery inventory and
  document the owner's host decision without weakening acceptance.
- [x] Add a static-only asset preflight, Cloudflare size/count checks and HTML
  attachment headers; test rejection and unchanged artifact bytes.
- [ ] Prepare a trusted manual parallel deployment from an exact successful main
  Documentation run; retain its manifests and verify public bytes before promotion.
- [x] Confirm actual account/project, minimal permissions and owner-only secret
  setup without exposing credentials; record real URLs and service limits.
- [ ] Verify stable/candidate/development/historical mapping and faithful retained
  editions, bilingual navigation/search, old links/anchors and all four downloads.
- [ ] Add isolated PR preview publication/statuses; verify success, deliberate
  failure, noindex/labels and absence of private variables/publication rights in PR code.
- [ ] Rehearse hosted rollback and failed build/identity/hash/default preservation.
- [ ] Switch canonical/default publication only after full acceptance; preserve
  Pages URLs and remove only replaced hosting steps and RTD-specific integration.
- [ ] Update baseline specifications, README/operator guide/both roadmaps, close
  completed tasks and archive only after the selected migration is complete.

Preparation evidence: the static payload preflight passed on an isolated copy of
trusted retained artifact 41239505389: 1,212 files, 91,676,529 bytes, five editions.
It preserves entry/export bytes and adds transport-only headers. Focused tests
cover source-run provenance, no backend/symlinks, file limits, hash rejection,
all-edition public verification routing, attachment headers and manual-main-only
credential boundaries. The first workflow
41317904495 uploaded source run 41286373400 (main `3c03ccca`) successfully to
`https://42e53263.agent-paranoid-android.pages.dev/`, then failed verification
with Cloudflare 1010/default urllib User-Agent. The documented descriptive
application User-Agent correction passed local verification of all five exact
same-build editions, all four exports and attachment headers. A browser HTML
download matched its retained hash. The corrected CI workflow has not yet passed;
manual acceptance remains open. Project production branch is main; GitHub's
publication environment permits main only. The owner installed the secret
directly; no token value was read. See the operator guide for permission scope,
expiry and precise evidence limits. No production/canonical switch is claimed.
