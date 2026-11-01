# Parallel Cloudflare Pages Publication

The maintainer selected Cloudflare Pages on 2026-11-01 after the RTD Community
experiment. The active change is
[`migrate-documentation-to-cloudflare-pages`](https://github.com/wa-pis/agent-paranoid-android/tree/main/openspec/changes/migrate-documentation-to-cloudflare-pages).
This is preparation for a parallel deployment, not a completed hosting switch.
GitHub Pages remains accepted. No paid plan, custom domain, DNS change, package
release or tag rewrite is required by this implementation.

## Build And Trust Boundary

Keep the existing strict GitHub `Documentation` workflow, frozen Python/docs
packages, Chromium PDF exporter, release verification, mike editions and retained
rendered artifacts. Cloudflare receives prebuilt assets through Direct Upload;
it does not need to run the Python build or receive private source data.

`Cloudflare documentation parallel acceptance` runs manually from main only.
Its source-run gate requires a completed successful main-push run of
`.github/workflows/docs.yml` in this repository, binds the exact source SHA and
then downloads only that run's `documentation-site` artifact. PR, fork, failed,
running and unrelated workflow sources are rejected before publication.

The uploader executes only trusted main deployment code in an empty working
directory. Site artifacts are data: symlinks, Worker/Functions entrypoints and
host/tool configuration are rejected. All local edition/entry/export hashes are
checked before upload. Credential access belongs only to the pinned Cloudflare
action steps; no PR source is checked out or run with that credential.

Initial uploads always use `migration-RUN_ID`, never the production branch.
The payload adds only `_headers`: noindex for parallel publication and attachment
headers for standalone HTML, covering both `.html` and Cloudflare's extensionless
paths at root and in version directories. Page/export bytes and recorded hashes
are preserved. The Free-plan preflight uses 20,000 files and 25 MiB per asset.
A retained real site passed with 1,212 files, 91,676,529 bytes and five editions;
this is a local payload result, not evidence of a Cloudflare upload.

## Owner Setup

Use an existing Cloudflare account. Create a Pages Direct Upload project with
production branch `main`, or choose `create_project=true` on the first workflow
run to create it through the reviewed uploader. Do not select Git integration
for this project. A project name and actual `pages.dev` addresses are not yet
assumed available.

Create the GitHub environment `cloudflare-pages-preview`, restricted to main.
Configure these values in that environment:

| Name | Kind | Value |
| --- | --- | --- |
| `CLOUDFLARE_ACCOUNT_ID` | Variable | The selected account's 32-character ID |
| `CLOUDFLARE_PAGES_PROJECT` | Variable | The chosen Direct Upload project name |
| `CLOUDFLARE_API_TOKEN` | Secret | Scoped Cloudflare API token described below |

The official Direct Upload integration requires **Account → Cloudflare Pages →
Edit**, limited to the intended account. This is an account-wide Pages permission;
it must not be described as limited to one project. Use a dedicated token and
revoke it when no longer needed. The token does not need DNS, zone, Worker/KV/R2
or repository administration permissions. The owner must review the actual
permission screen before creating it. Never paste the token into chat, a file,
workflow input, repository variable, command history or screenshot. Transfer it
directly from Cloudflare to the named GitHub environment secret; the agent does
not need to read its value.

## First Parallel Deployment

1. Select a successful main `Documentation` run with a retained, unexpired
   `documentation-site` artifact. Run 41284167968 is an observed example at
   `2ea24cfebc74356c53c0117ca094ee9d60961cb9`, not a permanent default source.
2. Run `Cloudflare documentation parallel acceptance` from main with that numeric
   `source_run_id`. Select `create_project` only for the first project creation.
3. Inspect the returned immutable deployment URL. The verifier retains the mike
   stable alias/destination gate, compares each edition's public identity,
   chapter/manifest inventory, exact entry bytes and all four exports against
   that same downloaded build, and requires HTML attachment headers.
4. A failed check leaves the accepted GitHub Pages site and canonical links
   unchanged. Uploading a parallel branch is not production promotion.

The first workflow does not implement automatic PR publishing, managed production
promotion, canonical replacement or hosted rollback. Those remain required tasks
in the active OpenSpec. Existing RTD/GitHub Pages resources are retained until
equivalent Cloudflare functionality and recovery are verified.

## References

- [Direct Upload with CI](https://developers.cloudflare.com/pages/how-to/use-direct-upload-with-continuous-integration/)
- [Asset limits](https://developers.cloudflare.com/pages/platform/limits/)
- [Static response headers](https://developers.cloudflare.com/pages/configuration/headers/)
- [Preview deployments](https://developers.cloudflare.com/pages/configuration/preview-deployments/)
- [Rollback](https://developers.cloudflare.com/pages/configuration/rollbacks/)
