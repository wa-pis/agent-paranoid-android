---
name: agent-paranoid-android-transformation
description: Review and execute explicitly requested one-to-one mixed-origin data transformations with Agent Paranoid Android, including local preservation approval and configured frozen sessions. Does not provide source-free synthetic generation or grant dataset access.
---

# Selective transformation

Use only installed transformation interfaces. Inspect the package version and
CLI help or MCP tool list. The registered single-source names are CLI
`transform-review`, `transform-approve`, `transform-execute`, and MCP
`review_transformation`, `execute_transformation`; availability depends on the
installation. Review alone is not execution or approval authority. Missing
capabilities must stop the dependent step. Never emulate transformation with
`generate`, custom source-row scripts or unrestricted SQL. Skills do not
activate extensions or authorize datasets.

## Local single-source workflow

1. Use local input/policy/mapping paths and a fresh output destination inside
   the allowed workspace. Request value-free per-field review and retain the
   exact displayed snapshot digest. Do not load source cells or mapping entries
   into chat, a provider request, logs or default MCP responses.
2. Review field actions and sensitivity uncertainty. Direct preservation or a
   preserve fallback requires an explicit per-field non-sensitive decision,
   no positive/conflicting sensitivity evidence, and a bounded operator comment.
   Unknown, sensitive and disputed fields remain blocked; DECIMAL preservation
   remains blocked by default. A `sensitive: false` flag alone is not approval.
3. Explicit `substitute` / `replace_text` mappings follow the installed reviewed
   contract uniformly across fields. A replacement equalling another fixed
   source value alone does not make it preservation or prohibit a sensitive
   permutation. Sensitivity stays a value-free field note. This never authorizes
   implicit copying, direct preserve or disclosure of mapping literals.
4. When preserving, hand off the exact local review to the operator for fresh
   controlling-TTY `transform-approve`. The operator must review the bound plan,
   source bytes, classification and mapping bytes. Agents and MCP cannot issue
   approval, simulate a TTY, create receipts or supply an approval boolean.
5. A supported `transform-execute` / `execute_transformation` consumer uses the
   exact reviewed snapshot digest and, for preservation, the matching locally
   issued receipt. Inspect installed help/schema for actual argument names.
   Changed source, policy/classification or mapping bytes require fresh review
   and fresh local approval when preserving; a new digest cannot validate an
   old receipt. Never bypass a failed binding check.
6. Report bounded, value-free validation, counts and artifact paths. Label the
   output mixed-origin and one-to-one, never fully synthetic. Do not return
   source or output rows, mapping literals, secrets or backend exception text.
   A reported unchanged percentage grants no disclosure or copying permission.

Saved multi-source profiles and configured SQL sessions have a separate
capture/expiry workflow. Read [references/sessions.md](references/sessions.md)
only for those requests. Do not open a database session for a local-file task.

If a necessary review, approval or safety capability is unavailable, explain
which step cannot proceed. Offer source-free synthetic generation as a separate
alternative only; do not silently change the user's intended outcome.
