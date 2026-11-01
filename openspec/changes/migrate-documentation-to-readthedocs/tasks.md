# Tasks: migrate-documentation-to-readthedocs

Hosting choice superseded on 2026-11-01 by the maintainer-selected
`migrate-documentation-to-cloudflare-pages`. Keep the partial evidence below;
this migration is not complete and is not archived as completed.

## Compatibility and setup

- [x] Inventory MkDocs/hooks, release catalog, publication, export, public
  verification, retention and URL contracts; map reused/replaced components.
- [ ] Confirm service plan/features/limits; document actual project URL,
  minimum GitHub import access and owner-only account/setup actions.

## Parallel build

- [x] Add `.readthedocs.yaml` with explicit supported Python/tool versions and
  frozen docs dependencies; retain license and strict-build checks.
- [x] Adapt MkDocs/theme/hooks and version links, keeping package version,
  package source and documentation revision distinct.
- [ ] Verify parallel normal-version builds and all four downloads, their
  chapter inventories, offline links and manifest hashes.

## Versions and previews

- [ ] Map verified stable, candidate, development and historical editions,
  including immutable tags lacking host config; retain faithful Pages snapshots
  when a matching managed build cannot be demonstrated.
- [ ] Gate stable/default promotion on public release acceptance and docs
  verification; test RC/unverified-tag refusal and edition-local search/navigation.
- [ ] Enable isolated PR previews/status checks; verify a fictional PR,
  deliberate failure, preview labelling, no private variables/deployment rights.

## Acceptance and switch

- [ ] Extend focused documentation/build contracts and pass strict MkDocs and
  OpenSpec checks; verify public identities, bilingual search/navigation,
  historical deep links/anchors and actual download hashes.
- [ ] Document and rehearse rollback to retained Pages output; a failed build,
  identity, mapping or download check must leave the known-good default intact.
- [ ] After parallel acceptance, switch canonical links, keep previous URLs
  usable and remove only replaced publication steps; retain release verification,
  exports, CI and recovery functionality.
- [ ] Record source revisions, public URLs and checks; update README/operator
  guide/both roadmaps; archive with baseline updates only after completion.

## Preparation Evidence

The operator guide's “Parallel Read the Docs Preparation” section records the
component inventory, retained checks/URLs/recovery and pending account setup.
The initial adapter renders one edition and cannot promote a default. Local
contract and export results are recorded with the implementation; actual host
builds, GitHub App permissions, URL, version mappings, PR statuses and rollback
remain unverified. Do not close those tasks from local test results alone.

Local preparation check (2026-11-01): 97 focused documentation/build tests,
strict MkDocs, strict change validation and 28 docs dependency licenses passed.
A Python 3.12 build with the locked Playwright Chromium produced the four real
exports; all four file hashes and entry-page hash matched, with 36 chapters.
These are local results, not proof of RTD publication or default promotion.

Public-edition gate preparation (2026-11-01): normal builds retain their exact
manifest in trusted logs; documentation CI retains normal/preview identities
and normal manifest for 90 days. The new verifier compares public identity,
complete manifest/chapter inventory, exact entry bytes and all four downloads
against the same retained build. 119 focused tests, strict MkDocs/OpenSpec and
Ruff passed locally. Same-site file+digest replacement and injected HTML are
rejected; the existing Pages alias/destination checks remain enforced. These
checks do not authorize stable/default promotion and have not run against an
actual RTD project. No hosted acceptance task is closed by this evidence.

PR #668 merged as `1eb22683ec6a2b379f1efcd47873a0452071e761` after 38 successful
checks (five intentional skips). Linux CI exercised normal and preview builds;
the explicit frozen config/license/strict-build preparation task is complete.
This does not prove native service configuration or a host switch.

Retained Pages evidence (2026-11-01): trusted successful run 40960334365,
workflow source `d14d3dc06af541bd89f8b047e5d54207c925e9a8`. Actual public Pages
passed the new same-build manifest/entry/four-download check. Local rejection
left the known-good output intact; atomic restoration recovered all 1,211 files
byte-for-byte and passed both Pages alias and edition checks. See the operator
guide for identities and manifest hash. No public rollback was deployed and RTD
rollback/default behaviour remains unverified, so the hosted recovery task
stays open. Development `.devN` versions also have focused non-stable tests.

PR #669 merged as `f5aca0b9f938ea50c06adbec68a0ded708b8b934` after 38 successful
checks (five intentional skips). The same-build edition gate, retained log/CI
manifests, development-version tests and recovery evidence are now in main.

Plan preflight: upstream RTD commit
`f343b74e8cbe292a2d3b8f0ed415fd9cbe1aa57a` disables the global Addons switch in
the non-Business project form; middleware requests injection based on the global
flag. The operator guide links the exact sources. Entry-page and standalone-HTML
bytes must be tested on the actual service; individual addon toggles, a paid
plan or an untested exception to integrity checks are not acceptance evidence.
Account connection and the actual project URL/settings remain unverified.

Native service evidence (2026-11-01): project `agent-paranoid-android` now has
successful PR build 35554849 (PR #671, source `5e2115b0386e9d039d248a112003bd48722d1b91`)
and normal build 35554945 (documentation source `0991058d08067284b8346a05c62944bd71131a57`).
The rendered latest edition distinguishes package 1.7.0rc1/source `64b7c8c3bbb0174fd7e159c4dfb42312045a1716`
from its newer documentation revision and development status. English/Russian
navigation, both search interfaces and the retained Pages stable link work.
This closes the rendering/identity adaptation task, not managed version mapping.

PDF and both downloaded ZIP hashes matched the normal build's retained log;
archive CRCs and all 36 chapter sources passed. Original standalone HTML inside
the site ZIP also matched its digest and contained no service scripts. Directly
served standalone HTML has RTD Addons and EthicalAds scripts in the browser DOM;
HTTP verification returned 403, leaving raw served HTML/entry hashes unverified.
The operator guide records exact URLs, identities, hashes and evidence limits.
Do not close the four-download/public-integrity, managed-preview isolation,
rollback or switch tasks from these partial checks. Project import and PR status
integration are observed, but installed scopes, account limits and private-variable
isolation still require owner-side inspection. The earlier account-unverified
notes above describe preparation before this native evidence.

Deliberate external-preview rejection: test PR #673 was closed without merge.
Native build 35555440 at source `8056bd791e7a2adaf2e0e7b6bd81986e54fb7398`
reached the fictional rejection and exited 17 before rendering; GitHub reported
RTD FAILURE. Earlier test revisions failed parsing, not this runtime path.
After failure, the API default remained latest, normal build 35554945 stayed
successful, and browser reload retained documentation revision `0991058d08067284b8346a05c62944bd71131a57`.
This proves the same-repository external-build rejection/status path only;
private-variable/fork isolation and hosted recovery remain open.
