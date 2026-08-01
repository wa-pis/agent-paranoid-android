# Changelog Policy

`CHANGELOG.md` is for people deciding whether and how to upgrade. It records
observable behavior, compatibility, security, and migration impact. OpenSpec,
audit logs, scanner output, CI implementation, and detailed release evidence
remain in their canonical documents and are linked only when they help a
reader evaluate the release.

## Unreleased Categories

Put every new user-facing entry under `## Unreleased` and one of these
categories, in this order when present:

| Category | Use it for |
| --- | --- |
| `Added` | New commands, formats, workflows, integrations, or documented capabilities. |
| `Changed` | Observable behavior, defaults, compatibility, performance, or output-contract changes. |
| `Fixed` | User-visible defects corrected without intentionally changing the supported contract. |
| `Security` | Boundary hardening, vulnerability fixes, or changed safety guarantees. Do not include exploit details before a fix is available. |
| `Deprecated` | Supported surfaces scheduled for removal, including replacement and support window. |
| `Removed` | Previously supported surfaces removed with the applicable compatibility decision. |
| `Migration` | Concrete actions required to adopt a breaking or operationally significant change. |

Omit empty categories. Historical release headings keep their original wording;
the policy applies to new `Unreleased` entries and future releases.

## Entry Rules

- Start with the observable result, not the PR, test, module, or implementation
  technique.
- Keep one user-relevant change per bullet and avoid repeating the same change
  in an uncategorized summary.
- State changed defaults, compatibility ranges, deprecations, removals, and
  required operator actions explicitly.
- Keep security impact in `Security` even when detailed scanner or review
  evidence moves elsewhere.
- Link to a migration guide, compatibility policy, security review, or release
  evidence document when the short entry cannot carry the necessary context.
- Do not add bullets solely for OpenSpec bookkeeping, refactors with no
  observable effect, CI implementation detail, or evidence collection. Preserve
  that information in OpenSpec archives, the roadmap, or release evidence.

## Release Review

Before cutting a release candidate:

1. Classify every `Unreleased` bullet as user impact, security impact,
   migration impact, or internal evidence.
2. Keep the first three classes concise in the appropriate category.
3. Move internal evidence to an existing canonical document without deleting
   historical facts; add a link from the changelog only when useful.
4. Check category order, duplicate entries, compatibility language, and links.
5. Move the reviewed categories under the version heading without rewriting
   historical release sections.
