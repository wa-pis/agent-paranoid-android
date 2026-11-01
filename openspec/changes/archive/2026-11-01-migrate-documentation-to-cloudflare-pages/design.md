# Cloudflare Pages migration design

## Reuse And Deployment Boundary

Reuse the successful GitHub Documentation build and its retained rendered site,
release gate and mike state. Cloudflare receives prebuilt files; do not move PDF
rendering into an unverified native build image. Direct Upload is selected before
project creation; native Git integration and Direct Upload have different project
setup semantics.

First manual deployments consume only a completed successful main-push
`.github/workflows/docs.yml` run from this repository. Validate its numeric run ID,
repository, workflow path, branch, event, conclusion and exact commit before
retrieving its artifact. Treat artifacts as data: reject symlinks, backend/Worker
entrypoints and deployment configuration; never execute scripts from the artifact.
Only trusted checked-in deployment code handles Cloudflare credentials.

The initial target is a non-production `migration-RUN_ID` branch in an explicitly
configured Pages project, never the production branch. Verify the exact retained
manifest, entry bytes and all four exports at the returned HTTPS deployment URL.
Do not promote or switch canonical links on a failed check.

## Hosting Contracts

Check the Free-plan 20,000-file and 25 MiB-per-file asset limits before upload.
Add only reviewed `_headers` rules for HTML attachments; do not rewrite content,
manifest hashes or historical identities to make a host check pass. Establish
normal Cloudflare serving without HTML transforms/analytics injection before
acceptance. Support root and version-local standalone HTML attachments.

Preserve existing stable/candidate/historical content and the three distinct
package/source/documentation identities. Keep the accepted stable authority in
the release catalog; a branch name, upload or new tag cannot promote it. Adjust
canonical URLs in a reviewed build only after parallel verification, keeping old
Pages URLs usable. Existing retained editions are not relabelled current prose.

## Previews And Recovery Still Required

PR build jobs receive no Cloudflare secret. A trusted publisher must bind a
successful source run to its PR/head commit and publish static preview data in a
separate preview project/origin. No checkout or execution of PR source occurs
with publishing rights. Check success, deliberate failure, labels, noindex,
edition-local search and private-variable isolation on the actual service.

Retain known-good deployments and the original Pages recovery artifacts. Prove
hosted rollback plus rejection/default preservation before production promotion,
then remove only superseded hosting steps. RTD cleanup is a separate reviewed
step after equivalent Cloudflare capability is accepted.

## Primary References

- https://developers.cloudflare.com/pages/how-to/use-direct-upload-with-continuous-integration/
- https://developers.cloudflare.com/pages/platform/limits/
- https://developers.cloudflare.com/pages/configuration/headers/
- https://developers.cloudflare.com/pages/configuration/preview-deployments/
- https://developers.cloudflare.com/pages/configuration/rollbacks/
