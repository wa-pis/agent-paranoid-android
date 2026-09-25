---
name: agent-paranoid-android-transformation
description: Help users request selective one-to-one data transformation while preserving sensitive-data and local-approval boundaries.
---

# Selective transformation

Use this skill when a user wants a one-to-one output with some source values
retained and other values transformed. This is not synthetic generation.
Check the installed CLI help or MCP tool list for an explicit transformation
interface. If none exists, say it is unavailable in this installation; do
not approximate it with `generate`, a custom script, or unrestricted SQL.
This skill works offline and does not activate a proposed feature.
If `transform-review` is installed, it can display a value-free local review
and snapshot digest only. Its presence does not imply approval or an executable
transformation command; check those capabilities separately before proceeding.

When an explicit interface is available:

1. Request a value-free per-field profile for human review. The system's
   comment should explain the likely meaning of each field, why it may be
   sensitive, and uncertainty, without showing cell values.
2. Treat `sensitive: true` as requiring transformation. An explicitly reviewed
   `sensitive: false` is only a candidate for preservation, not permission by
   itself. Unknown or conflicting classifications fail closed.
3. Let the user review field actions and any private inline YAML or local CSV
   mapping. Never send source values or mapping entries to an external model,
   default MCP response, log, or public summary.
4. Preservation requires the product's trusted local interactive CLI approval
   of the exact plan, classification, source and mapping bytes. An agent or
   MCP client may consume a valid matching receipt only if that installed
   interface explicitly supports it; neither may create the receipt.
5. Report only bounded, value-free validation and output summaries. A
   preservation percentage is not permission to disclose values or copy rows.

If the installed interface lacks any required review, approval, or safety
step, stop and report the unavailable step. Offer the source-free synthetic
workflow as a separate alternative, never as a silent substitute.
