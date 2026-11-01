# Cloudflare Pages Publication

**Status: cancelled by the maintainer on 2026-11-01; GitHub Pages is the selected
primary host.** Cloudflare served the same MkDocs site and did not add managed
Read the Docs functionality. Both `Cloudflare documentation` and `Cloudflare
documentation PR preview` workflows were set to `disabled_manually` in GitHub.
They do not automatically publish normal editions or PR previews. Projects,
deployments and credentials were not deleted or read. Existing Cloudflare URLs
are retained snapshots and are no longer the primary publication.

The material below records the completed experiment, including verified
production, isolated previews and recovery. It does not authorize re-enabling
publication. The repository return and its public verification are tracked in
`migrate-documentation-to-cloudflare-pages`; the migration itself is cancelled,
not completed. No paid plan, custom domain, DNS change or package release is
required to return to GitHub Pages.

## Build And Trust Boundary

Keep the existing strict GitHub `Documentation` workflow, frozen Python/docs
packages, Chromium PDF exporter, release verification, mike editions and retained
rendered artifacts. Cloudflare receives prebuilt assets through Direct Upload;
it does not need to run the Python build or receive private source data.

`Cloudflare documentation` supports trusted automatic production and manual
parallel/recovery publication from main only.
Its source-run gate requires a completed successful main-push run of
`.github/workflows/docs.yml` in this repository, binds the exact source SHA and
then downloads only that run's `documentation-site` artifact. PR, fork, failed,
running and unrelated workflow sources are rejected before publication.

The uploader executes only trusted main deployment code in an empty working
directory. Site artifacts are data: symlinks, Worker/Functions entrypoints and
host/tool configuration are rejected. All local edition/entry/export hashes are
checked before upload. Credential access belongs only to the pinned Cloudflare
action steps; no PR source is checked out or run with that credential.

Normal parallel uploads always use `migration-RUN_ID`, never the production branch.
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
for this project. The observed normal project is `agent-paranoid-android`; its parallel deployment
addresses are recorded below.

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

The first workflow does not implement managed normal-project production
promotion or canonical replacement. Separate PR publication and isolated recovery
controls are described below; their live acceptance remains required. Existing RTD/GitHub Pages resources are retained until
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


## Isolated Hosted Recovery Rehearsal

The separate Direct Upload project `agent-paranoid-android-recovery` is reserved
for recovery tests. In the manual workflow, `recovery=true` derives this name
from the configured normal project and selects branch `main` only in that
separate project. The default remains `recovery=false`: a normal-project
`migration-RUN_ID` preview. No free-form project or production-branch input is
accepted. The account-scoped Pages token already covers this project; no new
permissions or private variables are required.

Choose two successful main Documentation runs with retained artifacts and
different candidate documentation revisions. Publish A and then B with
`recovery=true`, leaving `rejection=none`. Both uploads must pass every edition's
same-build verification. Confirm the recovery project's production base URL
serves B, including its candidate identity; root stable alone may be identical
between the two builds and cannot establish which deployment is active.

Use Cloudflare's Deployments rollback control to restore the successful A
production deployment. Verify the recovery **production base URL**, not A's
immutable deployment URL, against A's retained artifact across all editions and
all four exports. Cloudflare permits rollback only to successful production
deployments; preview deployments are not rollback targets.

For controlled failures, repeat the manual workflow with `recovery=true` and
`rejection=identity`, then `rejection=hash`. These choices alter only the freshly
downloaded disposable artifact copy: an identity mismatch or a fictional entry
comment must fail the existing provenance/hash gate before uploader execution.
They cannot be selected for normal publication. After each failure, verify the
same known-good recovery production base against A again, and check the normal
project/default and accepted GitHub Pages publication remain unchanged.

These controls and their fictional tests prepare a rehearsal; they do not prove
that a hosted rollback or rejected deployment has occurred. Record the actual
run IDs, A/B identities, rollback result and unchanged-default checks before
closing the recovery task. This does not authorize a normal-project production
or canonical switch.


## Live Preview And Link Evidence (2026-11-01)

[PR #677](https://github.com/wa-pis/agent-paranoid-android/pull/677) produced a
successful exact-head preview for `d439b5d5` through
[publisher 41323969006](https://github.com/wa-pis/agent-paranoid-android/actions/runs/41323969006)
at [deployment 1a1ca15f](https://1a1ca15f.agent-paranoid-android-previews.pages.dev/).
A browser confirmed its visible non-stable banner and edition-local Trino search.

The disposable [PR #678](https://github.com/wa-pis/agent-paranoid-android/pull/678)
then built fictional bilingual markers at `e885a63d`. Its
[source run 41323969881](https://github.com/wa-pis/agent-paranoid-android/actions/runs/41323969881)
passed a separate observation job with no source checkout: checks reported only
that the environment-scoped token and all three publication variables were absent;
no values were printed. The actual preview job still has no secret expressions,
publication environment or publication rights. The source run succeeded and its
exact-head `docs/cloudflare-preview` status linked to
[deployment e9c20db0](https://e9c20db0.agent-paranoid-android-previews.pages.dev/).
An independent public verification against that run's retained artifact passed
identity, bilingual entry/search bytes and noindex. The browser displayed the
fictional marker and exact source SHA. This is a same-repository rehearsal;
fork provenance rejection/acceptance is covered by fictional metadata tests,
not claimed as a live fork run.

On the accepted parallel normal deployment `1641144a`, 30 additional public
files matched retained build 41286373400 exactly: Russian entries, English and
Russian configuration/Trino pages, and search indices for all five editions.
English `#trino-connection` and existing localized configuration heading anchors
were retained. Each search index included Russian records and only relative
edition-local locations (root/stable: 786 records, 355 Russian; candidate/next:
816 records, 355 Russian). The current `next` is the RC copy alias while the
package source remains 1.7.0rc1; it is not presented as a separate development
release. Native mike's development mapping remains covered by standard-plugin
tests, and no unverified stable version was added.


At `be96b6da`, the same disposable PR deliberately failed its preview source step
after rendering. [Source 41324502142](https://github.com/wa-pis/agent-paranoid-android/actions/runs/41324502142)
failed while its strict normal build and boolean isolation observation passed.
[Publisher 41324670213](https://github.com/wa-pis/agent-paranoid-android/actions/runs/41324670213)
validated the current head, posted `docs/cloudflare-preview=failure`, and skipped
the credentialed upload job. The prior `pr-678` branch alias still matched the
retained `e885a63d` preview exactly. Reverification passed all five normal
Cloudflare editions against retained build 41286373400 and the accepted GitHub
Pages stable default. PR #678 was closed without merging. These are actual
success/failure/default-preservation observations, not just workflow simulations.


## Live Hosted Recovery Evidence (2026-11-01)

The recovery project has production branch `main`, no Git connection, and a
separate production base `https://agent-paranoid-android-recovery.pages.dev/`.
Normal project production remained empty throughout this rehearsal.

- A: [publisher 41324897408](https://github.com/wa-pis/agent-paranoid-android/actions/runs/41324897408)
  accepted source 41286373400 and deployed `bc8969bc`. Its candidate/next
  documentation revision is `3c03ccca`. Both the immutable URL and the recovery
  production base passed all five same-build edition/download checks.
- B: [publisher 41325086334](https://github.com/wa-pis/agent-paranoid-android/actions/runs/41325086334)
  accepted source 41319731486 and deployed `eec2c87d`. Its candidate/next
  documentation revision is `b99b7c8c`. The production base was demonstrably B,
  not A, and passed all five checks against B's retained artifact. Root stable
  retained documentation `5344b390` in both builds; checking root alone would
  have missed the change.
- Cloudflare's real rollback control restored production to A/`bc8969bc`.
  The production base's candidate identity changed back to A and differed from
  B. All five editions, exact manifests/entries, all four exports and standalone
  HTML attachment headers passed again against retained A.
- [Identity rejection 41325547847](https://github.com/wa-pis/agent-paranoid-android/actions/runs/41325547847)
  and [hash rejection 41325550670](https://github.com/wa-pis/agent-paranoid-android/actions/runs/41325550670)
  deliberately changed disposable B artifact copies. Each failed at the existing
  static/provenance/hash preflight with the expected reason; project creation
  and credentialed upload steps were skipped. After both refusals, the recovery
  production base still passed all five A edition/download checks.

A dashboard check then confirmed the normal project still said **No production
deployment yet**, with only its two migration previews. The accepted GitHub Pages
stable default had already passed unchanged after the failed PR rehearsal.
The native mike selector was exercised on Cloudflare: selecting `1.7.0rc1` from
`versions/stable/` opened that candidate on the same Cloudflare deployment,
showing its explicit candidate label and `3c03ccca` identity. No normal-project
production or canonical switch is implied by these recovery results.


## Automatic Production Publisher

After preview and hosted recovery acceptance, the reviewed publisher can consume
successful main-push Documentation completions automatically. It still checks
source API provenance and every retained artifact hash; immediately before the
credentialed upload it requires the source SHA to equal the current main SHA.
Stale reruns, failed runs and PR sources cannot become normal production through
this path. Only this trusted workflow event selects the configured normal
project's `main` branch; manual dispatch remains a migration preview or an
explicitly separate recovery rehearsal. The two modes cannot be mixed.

Automatic production adds attachment headers without the parallel noindex rule.
It verifies both the immutable deployment and the normal project's production
base against every same-build retained edition and all four exports. PR previews
and recovery remain separate and unindexed. The existing GitHub Pages publisher,
public verification and native mike retention remain active for old links and
recovery.

PR #681 enabled this publisher. The first normal production publication passed:

- Source [Documentation 41331122749](https://github.com/wa-pis/agent-paranoid-android/actions/runs/41331122749)
  built main `c8c7c97b7422c15e5068484919ca57536844c29c` successfully.
- Automatic [publisher 41331311059](https://github.com/wa-pis/agent-paranoid-android/actions/runs/41331311059)
  deployed [immutable `bad72846`](https://bad72846.agent-paranoid-android.pages.dev/).
  The static payload contained 1,214 files, 91,943,587 bytes and five editions.
  Both immutable and production-base verification passed every edition and all
  four same-build exports. A browser visit confirmed the production root.
- Root and maintained stable retain documentation identity `5344b390`; the RC
  and `next` aliases carry this source build's documentation revision. Publication
  does not promote the RC package or change the verified stable catalog.

The subsequent canonical/link change makes Cloudflare the README entry point
and the configured host for newly rendered editions. The native mike hook uses
that configured host with its existing `versions/` deploy prefix; it does not
introduce a second edition catalog. Actual standard-plugin tests build a new
candidate/development edition on a changed host and verify its canonical URL
while checking retained stable HTML and identities byte for byte.

Existing rendered historical/root/stable bytes, identities, exports and their
original GitHub Pages canonical URLs are retained. They are not rewritten to
pretend they were built on the new host. New canonical URLs take effect only
when a new edition is rendered. GitHub Pages keeps the same retained tree for
old links and recovery. Project-specific RTD automation must be disabled before
its configuration is removed; this owner-session cleanup remains outstanding.
No package release or stable catalog promotion occurs in this step.


## Return To GitHub Pages

The last Cloudflare canonical build was Documentation 41334153435 at
`84edf346467a5b90ef7d395f54519ffa1b60afa7`, published successfully by 41334341512
to `1a52d73d`. Immutable and production-base checks passed all five editions and
four exports. Public candidate/next canonicals pointed to Cloudflare; frozen
root/stable retained their original GitHub Pages canonicals and `5344b390`
identity. The maintainer then chose GitHub Pages instead of maintaining two
hosting systems. README and newly rendered canonicals return to GitHub Pages;
public acceptance of that return is recorded separately once the main build
and its public verifier succeed. Prior successful checks are retained as
experiment evidence, not claimed as acceptance of the return.
