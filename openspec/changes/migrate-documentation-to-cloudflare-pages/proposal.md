# Change Proposal: migrate-documentation-to-cloudflare-pages

Status: **cancelled by the maintainer on 2026-11-01**. GitHub Pages is selected
as primary; Cloudflare added hosting rather than the sought managed documentation
features. Completed experiment evidence is retained. The migration delta is not
accepted into baseline specifications. Return tasks are tracked below before
archival; incomplete acceptance boxes must not be converted to completed work.

## Why

On 2026-11-01 the maintainer selected Cloudflare Pages after native RTD
Community evaluation showed service scripts in directly served standalone HTML.
This supersedes the uncompleted hosting choice in
`migrate-documentation-to-readthedocs`; its verified build, identity, export and
rejection evidence is retained. It does not declare that migration complete.

## What Changes

- Keep MkDocs, bilingual content/search, mike editions, four exporters, frozen
  Python dependencies and exact-source release acceptance.
- Publish prebuilt static assets using Cloudflare Pages Direct Upload, with
  trusted deployment jobs separated from source/PR execution.
- First deploy a parallel non-production branch, retaining source-run provenance,
  download manifests and exact public-byte checks before any promotion.
- Add explicit attachment headers for standalone HTML, preserve historical
  snapshots and old GitHub Pages URLs, and rehearse hosted rollback.
- Add isolated PR previews without passing publication credentials to PR code.

## Compatibility And Safety

No runtime/package release, tag rewrite, theme replacement, dataset access,
paid plan, custom domain or DNS change is included. Owner-only project/account
setup and scoped credentials are required; tokens are never requested in chat.
GitHub Pages remains accepted until the full Cloudflare acceptance and recovery
contract passes. RTD is neither deleted nor expanded by this proposal.
