# 1.0.0rc1 Unreleased Inventory

This inventory classifies the 89 top-level bullets under `Unreleased` in
`CHANGELOG.md` at commit `fcd841a`. Numbering follows source order and ignores
wrapped continuation lines. The ranges below are exhaustive and non-overlapping.

| Source block | User impact | Security impact | Migration impact | Internal evidence |
| --- | --- | --- | --- | --- |
| Uncategorized, 1-16 | 1-12, 14-16 | 13 | None | None |
| `Added`, 17-59 | 17-18, 20-21, 23-33 | 22 | None | 19, 34-59 |
| `Fixed`, 60-89 | 60-62, 77, 85-87 | 63-65, 74-75, 78, 84 | None | 66-73, 76, 79-83, 88-89 |
| **Totals** | **37** | **9** | **0** | **43** |

The classification is exclusive and records the primary release-reader impact.
Compatibility notes that require no operator action remain user or security
impact; no current entry requires a migration step.

## Review Disposition

- Keep the 37 user-impact items, combine duplicates, and place each concise
  result under `Added`, `Changed`, or `Fixed`.
- Keep the nine safety and supply-chain items under `Security`, combining
  implementation evidence with the user-visible guarantee it supports.
- Move the 43 internal-evidence items to the roadmap, OpenSpec archives,
  compatibility references, security review, or release evidence as applicable.
  Preserve the facts in those canonical documents rather than in the changelog.
- Do not add an empty `Migration` section. Add one only if the final RC review
  identifies a concrete action required from an operator or API consumer.

This snapshot is an audit aid, not a permanent changelog category. The 43
internal-evidence entries are preserved in the
[RC evidence record](release-evidence-1.0.0rc1.md) after their removal from the
user-facing changelog.
