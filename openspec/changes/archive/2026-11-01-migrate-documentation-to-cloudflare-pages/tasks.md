# Tasks: migrate-documentation-to-cloudflare-pages

Status: cancelled by the maintainer on 2026-11-01; return to GitHub Pages selected.
The historical maintainer choice was Cloudflare on 2026-11-01. RTD evaluation is retained as
partial evidence, not a completed/archived migration. Account existence is
confirmed; the Direct Upload project and owner-installed GitHub secret are now
configured. Live upload/verification evidence is scoped below; full migration
acceptance remains incomplete.

- [x] Carry forward the existing identity/export/release/recovery inventory and
  document the owner's host decision without weakening acceptance.
- [x] Add a static-only asset preflight, Cloudflare size/count checks and HTML
  attachment headers; test rejection and unchanged artifact bytes.
- [x] Prepare a trusted manual parallel deployment from an exact successful main
  Documentation run; retain its manifests and verify public bytes before promotion.
- [x] Confirm actual account/project, minimal permissions and owner-only secret
  setup without exposing credentials; record real URLs and service limits.
- [x] Verify stable/candidate/development/historical mapping and faithful retained
  editions, bilingual navigation/search, old links/anchors and all four downloads.
- [x] Add isolated PR preview publication/statuses; verify success, deliberate
  failure, noindex/labels and absence of private variables/publication rights in PR code.
- [x] Rehearse hosted rollback and failed build/identity/hash/default preservation.
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
download matched its retained hash. Corrected main publisher run 41319733062 at `b99b7c8c` passed all five
same-build editions at `https://1641144a.agent-paranoid-android.pages.dev/`.
Manual parallel acceptance is complete for that source artifact; it does not
prove the remaining development/history/link/preview/recovery/switch gates. Project production branch is main; GitHub's
publication environment permits main only. The owner installed the secret
directly; no token value was read. See the operator guide for permission scope,
expiry and precise evidence limits. No production/canonical switch is claimed.

Preview preparation: the separate `agent-paranoid-android-previews` Direct Upload
project is created and configured in the main-only publisher environment. The
new source job builds exact PR heads without that environment; the trusted
workflow_run publisher accepts only current API-bound PR artifacts, treats them
as static data, verifies bilingual/search bytes and noindex, and posts exact-head
statuses. Fictional tests cover fork metadata, stale/closed/ambiguous sources,
backend rejection, false labels and modified assets. Live positive/negative and
private-variable rehearsals are still required; the preview checkbox stays open.

Recovery preparation: a derived, separate `agent-paranoid-android-recovery`
project permits production A/B and rollback rehearsals while normal publication
remains a migration preview. Controlled identity/hash failures affect only a
disposable downloaded copy and are disallowed outside recovery mode. Focused
tests bind the destination and rejection-before-upload contract. Actual hosted
A/B, base-URL rollback and unchanged-default evidence remain required; the
recovery checkbox stays open.

Live preview acceptance: PR #678 source 41323969881 at `e885a63d` passed the
boolean-only absence observation and exact-byte/noindex bilingual verification
at `e9c20db0.agent-paranoid-android-previews.pages.dev`. Deliberately failed source
41324502142 at `be96b6da` produced exact-head failure through publisher
41324670213, whose credentialed publication job was skipped. The previous
`pr-678` preview remained byte-identical; all five normal Cloudflare editions
and the accepted GitHub Pages stable default reverified unchanged. The test PR
was closed without merging. Fork behavior is covered by fictional metadata tests,
not a live fork rehearsal. PR #677 passed every applicable CI check and merged;
its recovery controls are ready for hosted A/B acceptance, which remains open.

Live recovery acceptance: successful publishers 41324897408 (A/`bc8969bc`, source
41286373400) and 41325086334 (B/`eec2c87d`, source 41319731486) passed immutable and
production-base checks. Candidate identities proved the base served B and then A
after a real Cloudflare rollback. Every edition and all four exports passed
against A after rollback. Identity/hash rejection runs 41325547847 and
41325550670 failed at preflight with uploader skipped; A reverified after both.
Normal project production remained empty. See the operator guide for full
provenance and exact evidence limits. Mapping acceptance covers the current
RC-as-next alias, retained stable/history, bilingual links/search and actual
native mike selection; the development-version path is standard-plugin-tested,
not represented as a separate live package release. Canonical/default promotion
and final baseline/cleanup/archive tasks remain open.

Automatic production preparation: trusted main workflow_run events accept only
successful main Documentation push artifacts, recheck the current main SHA
immediately before upload, choose normal production explicitly, and verify its
base URL as well as the immutable deployment. Manual/recovery/preview isolation
and GitHub Pages recovery remain intact. Actual production evidence and the
subsequent canonical/README/cleanup work are still required; switch remains open.


First normal production acceptance: Documentation 41331122749 at main
`c8c7c97b7422c15e5068484919ca57536844c29c` and automatic publisher 41331311059
both succeeded. Deployment `bad72846` and the normal production base passed all
five editions and four same-build exports (1,214 static files, 91,943,587 bytes).
The production root was also opened in a browser. The subsequent reviewed
canonical/link change configures Cloudflare for newly rendered editions and
README links, while retaining frozen historical/root/stable HTML and its original
GitHub Pages canonical URLs. Native mike tests exercise the host change and exact
stable-byte preservation. Public verification of that new canonical build and
project-specific RTD trigger cleanup remain required; the combined switch task
and final baseline/archive task stay open.


## Owner-Directed Return (2026-11-01)

The migration is cancelled, not successfully completed. Prior completed tasks
remain evidence; unfinished Cloudflare acceptance/baseline tasks above are no
longer the intended destination and their delta must not be applied on archival.

- [x] Record the owner decision to keep GitHub Pages primary.
- [x] Disable both Cloudflare publisher workflows in GitHub; API confirmed
  `disabled_manually` for normal production and PR previews. Preserve projects,
  deployments and secret values without reading or deleting them.
- [x] Restore README and new-edition canonical URLs to GitHub Pages through a
  checked exact-SHA protected merge; retain native mike and frozen edition bytes.
- [x] Verify the actual successful main Documentation publication, public
  identities/exports, new GitHub Pages canonical and old stable preservation.
- [x] Reconcile baseline/operator/roadmaps with the final owner decision and
  archive cancelled Cloudflare/superseded RTD proposals without their unaccepted
  host-specific deltas. RTD project-build cleanup is manual owner work; do not
  claim it occurred or remove RTD config before confirmation.


Return acceptance: PR #683 merged checked head
`5c9dca79e693dffd4695bee41cee8850bf085f26` as main
`508b39be4a2526ac1674ccb8da41780837a4cfe9`. Documentation
[41336088977](https://github.com/wa-pis/agent-paranoid-android/actions/runs/41336088977)
succeeded through build, deployment, same-build public verification and mike
retention. Independent public reads of all five editions confirmed GitHub Pages
canonicals, Russian entry points and bilingual search. Root/stable/1.6.0 retained
`5344b390`; candidate/next identify the new `508b39be` documentation revision.
Both Cloudflare workflows remained `disabled_manually` after the merge.
Archival disposition is cancelled/superseded with `--skip-specs`: historical
incomplete tasks above stay unchecked, and their hosting delta is not applied.
RTD project-build cleanup remains an explicit manual owner follow-up; its
configuration is retained and no cleanup acceptance is claimed.
