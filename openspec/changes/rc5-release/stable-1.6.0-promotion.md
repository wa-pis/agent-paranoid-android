# Stable 1.6.0 promotion

## Authorization and scope

On 2026-10-16 the owner requested a full stable `1.6.0` containing all accepted
changes since `1.5.0`. This supersedes the earlier absence of stable authorization;
it does not rewrite the completed RC5 record, issue preservation approval, or
activate deferred features.

Promote publicly verified `v1.6.0rc5`, commit
`890925afdff68e97cafe38a28605d2874c9dad79`, with the documentation reconciliation
at main `304e75d7f998fae6c8d58595a432880ac9da1531`. Review the complete diff against
that tag under `docs/release.md`: only package/version maturity metadata, the root
lockfile version, release-facing documentation and the hard-coded current stable
version assertion may change. Any runtime, dependency, packaging, schema, fixture,
workflow or behavioral/safety test correction requires another accepted RC.

## Acceptance

Complete fresh exact-source local/CI gates, independent exact-main technical
review and Ubuntu no-publish artifact verification. Bind the signed acceptance
manifest and tag to the resulting commit and hashes. Publish through the existing
protected process, verify GitHub/PyPI/three signed container targets, and record
the successful public verification run before declaring stable available.

Preserve actual source/artifact/environment identities for historical RC5
automated and human evidence; unchanged runtime is a binding argument, not a
fresh execution claim. The separately gated fictional transformation/session
campaign is tracked in `cross-interface-acceptance`. For this requested full
stable release, complete its outstanding fictional installed-artifact and actual
local-terminal human steps before declaring the combined work accepted. It
remains open until those results exist; this does not reopen completed RC5 gates.
No assistant may invent those steps or issue a preservation receipt.
Broader/private/live-provider acceptance is not implied by stable publication.

Status is maintained in `docs/1.6.0-release-status.md` and the stable section of
this change's tasks. The existing RC5 tasks retain their historical meaning.
