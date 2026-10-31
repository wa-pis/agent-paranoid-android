# Tasks: migrate-documentation-to-readthedocs

Parallel-build implementation is in progress. Hosted acceptance and switching remain open.

## Compatibility and setup

- [x] Inventory MkDocs/hooks, release catalog, publication, export, public
  verification, retention and URL contracts; map reused/replaced components.
- [ ] Confirm service plan/features/limits; document actual project URL,
  minimum GitHub import access and owner-only account/setup actions.

## Parallel build

- [ ] Add `.readthedocs.yaml` with explicit supported Python/tool versions and
  frozen docs dependencies; retain license and strict-build checks.
- [ ] Adapt MkDocs/theme/hooks and version links, keeping package version,
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
