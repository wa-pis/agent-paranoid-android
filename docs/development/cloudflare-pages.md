# Parallel Cloudflare Pages Publication

The maintainer selected Cloudflare Pages on 2026-11-01 after the RTD Community
experiment. The active change is
[`migrate-documentation-to-cloudflare-pages`](https://github.com/wa-pis/agent-paranoid-android/tree/main/openspec/changes/migrate-documentation-to-cloudflare-pages).
A first parallel deployment is available; this is not a completed hosting switch.
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

## First Live Evidence (2026-11-01)

The owner created `agent-paranoid-android` as a Direct Upload project. Its
production branch is `main`; Git integration, project variables and bindings
are absent. The GitHub environment restricts deployment to main and contains
the account/project variables and an owner-installed `CLOUDFLARE_API_TOKEN`.
The prepared token summary grants Pages Edit to the selected account and expires
on 2027-01-30; its value was not read by the agent.

[Workflow 41317904495](https://github.com/wa-pis/agent-paranoid-android/actions/runs/41317904495)
uploaded trusted Documentation run 41286373400 at
`3c03ccca95f430e928cd0e6af254e62d31043966` to
[immutable deployment 42e53263](https://42e53263.agent-paranoid-android.pages.dev/).
The upload succeeded, but the workflow's verification failed with HTTP 403/error
1010 from the default Python urllib User-Agent. This is not a green workflow.
Cloudflare's [documented resolution](https://developers.cloudflare.com/support/troubleshooting/http-status-codes/cloudflare-1xxx-errors/error-1010/)
is a descriptive application User-Agent. Both byte verification and attachment
checks identify the documentation verifier explicitly; browser impersonation or
security-setting changes are not required.

Using that correction, the local verifier passed all five same-build editions:
root, `versions/1.6.0`, `versions/stable`, `versions/1.7.0rc1` and `versions/next`.
It checked identities, the stable alias, exact full manifests/chapter inventory,
entry bytes, all four export hashes and standalone HTML attachment headers.
Root/stable remain maintained 1.6.0 guidance at documentation `5344b390`; candidate
and next remain 1.7.0rc1 at documentation `3c03ccca`, not stable. The fresh upload
payload contains 1,214 files and 91,808,365 bytes. A real browser HTML download
was 710,301 bytes and matched the root retained manifest exactly.

These results cover the named immutable deployment, not production promotion,
automatic PR previews, hosted rollback or a completed migration. The corrected main workflow
[41319733062](https://github.com/wa-pis/agent-paranoid-android/actions/runs/41319733062)
passed on publisher commit `b99b7c8cc2a52a8eea7c78ef15b57b25e6fd3941`,
using the same source artifact 41286373400 and verifying all five editions at
[deployment 1641144a](https://1641144a.agent-paranoid-android.pages.dev/).
Production remains empty; both observed deployments are Preview/migration builds.

## Isolated PR Preview Pipeline

The separate Direct Upload project `agent-paranoid-android-previews` has been
created. Configure `CLOUDFLARE_PAGES_PREVIEW_PROJECT` with that exact value in the
existing main-only publication environment. This does not add private variables
or bindings to the Cloudflare preview project.

The Documentation workflow builds the exact PR source head in an unprivileged
job, with no publication environment, Cloudflare credential or shared uploader
cache. Strict normal documentation/release checks must pass first. The labelled
preview artifact omits normal exports and retains bilingual pages/search.

`Cloudflare documentation PR preview` handles the completed run using only
trusted default-branch code. GitHub API metadata must bind that repository's
Documentation PR run to exactly one currently open PR with the same source head
and head/base repositories. Fork metadata is supported; missing, changed, closed
or ambiguous associations are rejected. The publisher checks the current head
again immediately before upload. Source failure posts an exact-head failed
`docs/cloudflare-preview` status without opening a publication environment.

Successful source artifacts are treated only as data: the existing static asset
checks reject Functions, Workers, deployment configuration, symlinks and oversized
inputs. The PR identity must match the authenticated source SHA and be visibly
labelled `PR preview / not stable`. The uploader runs in an empty directory and
uses only the separate preview project with branch `pr-N`. It never checks out
or executes PR code with publication rights. Byte verification covers identity,
English/Russian entry/search pages and their shared search index, plus the real
HTTPS/noindex response. The exact source head receives a success/failure status
and immutable deployment link. Failed publication does not change normal editions.

Pipeline implementation and fictional tests are preparation. Actual successful
and deliberately failed PR rehearsals, private-variable isolation observations,
preview UI checks and normal-default preservation must still be recorded before
closing the preview task. See GitHub's
[workflow event reference](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows)
and [secure-use reference](https://docs.github.com/en/actions/reference/security/secure-use).
