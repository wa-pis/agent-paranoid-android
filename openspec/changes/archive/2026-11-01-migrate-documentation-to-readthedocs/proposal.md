# Change Proposal: migrate-documentation-to-readthedocs

Status: hosting choice superseded on 2026-11-01 by
`migrate-documentation-to-cloudflare-pages`; that migration was then cancelled
by the maintainer in favor of keeping GitHub Pages. Partial evidence is retained;
uncompleted RTD hosting requirements are not accepted into the baseline.

## Why

GitHub Pages currently hosts our MkDocs/mike/Actions documentation pipeline.
Read the Docs can provide managed versions, builds and PR previews. Move
hosting there while preserving existing documentation contracts. The user
requested this work plan on 2026-10-30. Native parallel normal and PR builds
now succeed; public integrity, managed editions and the hosting switch remain
open as recorded in the task evidence.

## What Changes

- Add reproducible Read the Docs configuration for existing MkDocs content.
- Preserve verified stable, candidate and historical editions with distinct
  package source and documentation revision identities.
- Add isolated PR previews; retain strict documentation and release checks.
- Preserve bilingual navigation/search, historical links and PDF, standalone
  HTML, Markdown ZIP and offline site ZIP downloads.
- Validate parallel hosting and rollback before switching the canonical entry
  point or removing replaced Pages/mike publication steps.

## Scope and Compatibility

Implementation covers host configuration, locked docs dependencies, MkDocs
hooks/theme, version catalog, exports, publication, public verification and
operator instructions. Check current service eligibility/limits and minimum
GitHub integration access; record owner-only account setup without requesting
credentials. The verified stable default is currently1.6.0;1.7.0rc1 is a
separate candidate. Preserve immutable tags and signed artifacts. Historical
editions lacking host configuration need matching documentation refs or retained
verified snapshots, never current prose relabelled as an old release.

No application API/version, dataset permission, Sphinx/theme rewrite, package
release or paid/custom domain is included. This proposal alone does not connect
accounts, deploy hosting, change DNS or switch public links.

## Safety Impact

Builds use tracked docs/code and fictional fixtures only. No user datasets,
receipts, production services or provider calls enter builds/exports. Untrusted
PR previews receive no private variables or deployment authority and cannot
change verified editions/defaults. Keep dependency/license, strict-build,
release acceptance and public identity/hash gates. Existing source-free and
local preservation approval guarantees remain unchanged.
