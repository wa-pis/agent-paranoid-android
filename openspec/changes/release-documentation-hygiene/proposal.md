# Change Proposal: release-documentation-hygiene

## Summary

Separate user-facing release notes from internal OpenSpec, audit, and release
engineering evidence. Keep `CHANGELOG.md` useful for people upgrading the
package while preserving detailed implementation history in the appropriate
OpenSpec archives and evidence documents.

## Motivation

The current `Unreleased` section mixes user-visible behavior with internal
contract consolidation, CI gates, archived changes, and security evidence.
That makes it difficult to identify what changed for users and encourages
release notes to become an engineering journal.

## Scope

In scope:

- Define the user-facing changelog categories: Added, Changed, Fixed,
  Security, Deprecated, Removed, and Migration notes.
- Keep entries concise and describe observable behavior, compatibility, and
  migration impact.
- Move detailed OpenSpec and audit trail information to existing canonical
  specs, archived changes, security reviews, or release evidence documents.
- Link release notes to the detailed evidence where useful.
- Preserve historical release information and do not erase security findings.

Out of scope:

- Changing runtime behavior, package versioning, or release automation.
- Deleting engineering evidence or rewriting historical facts.
- Hiding security changes behind vague user-facing wording.

## Safety Impact

No runtime safety behavior changes. Security-relevant user impact remains in
the `Security` category, while detailed evidence remains reviewable in the
linked OpenSpec or security documents.

## Compatibility

The changelog URL and historical version headings remain stable. This is a
documentation contract change only; no CLI, Python, MCP, artifact, or
generation behavior changes.
