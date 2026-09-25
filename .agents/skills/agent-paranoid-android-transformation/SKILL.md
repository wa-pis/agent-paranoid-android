---
name: agent-paranoid-android-transformation
description: Plan or review selective one-to-one source transformation without confusing proposed behavior with the shipped source-free generator.
---

# Selective transformation

Use this skill for the `selective-source-transformation` change only. First
read `openspec/changes/selective-source-transformation/progress.md`, then the
relevant section of `plan.md`, `tasks.md`, `policy-contract.md`, or
`client-acceptance.md`. Check the current branch and diff; a proposal or private
parser is not an executable public feature.

- Keep the shipped synthetic path source-free. Never route source rows through
  generation, examples, logs, MCP responses, or an external model.
- Treat possible PII as sensitive by default. The proposed per-field profile
  review distinguishes `sensitive: true` (transform) from an explicitly
  reviewed `sensitive: false` (candidate for preservation). Include a
  system-authored, value-free comment describing the likely field meaning,
  rationale, and uncertainty so a human can decide; that comment is evidence,
  not permission. Follow the current OpenSpec if this design changes.
- Do not enable preservation from a field flag, mapping, profile, or model
  suggestion alone. The planned permission is a trusted local interactive CLI
  confirmation tied to the exact plan, classification, source, and mapping
  bytes. An agent or MCP client cannot mint that receipt. The execution path
  remains disabled until the documented safety amendment, executable tests,
  and independent safety review are complete.
- Keep inline YAML and local CSV mappings private; expose only bounded,
  value-free summaries. Preserve one-to-one row and relationship invariants
  only when the approved contract explicitly permits it. Never treat a percent
  or preservation metric as permission to disclose or copy values.
- Use fictional fixtures for local checks. Do not connect a real database or
  external API merely to demonstrate the proposal. Record unverified private
  acceptance as pending, not passed.

For implementation ownership, use `docs/implementation_map.md` and the
task-specific guide from `AGENTS.md`; avoid inventing a new public CLI/MCP/API
contract from unfinished OpenSpec text.
