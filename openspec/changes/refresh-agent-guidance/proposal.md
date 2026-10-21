# Refresh portable agent guidance

## Why

Prompts focus on Trino while the package supports local CSV/folder/profile
planning and explicitly separate transformation consumers. Skills omit the
exact-spec approval/recovery handoff. Wheel users receive skills but not prompt
templates, and resource checks do not cover supporting references or UI metadata.

## Scope

Update prompt/skill instructions against installed CLI and MCP contracts; add
folder, safe-profile and local transformation request templates and skill UI
metadata. Bundle prompts alongside skills in wheels and check complete offline
resource discovery. Keep original prompt filenames and skill names stable. Copy bundled prompts
into the Docker build context. Resolve the CI-reported PYSEC-2026-4320 advisory
by updating only the transitive certifi lock entry to 2026.10.19; retain verified
TLS and all direct dependency ranges.

This is instruction and packaging maintenance. It adds no CLI/MCP registration,
approval issuer, source access, data preservation authority or activated runtime
extension. It does not close the separate transformation/session campaign.

## Coordination

Work lives in an isolated worktree. General README, docs, navigation and release
history are being maintained separately; the usage guide is `prompts/README.md`.
