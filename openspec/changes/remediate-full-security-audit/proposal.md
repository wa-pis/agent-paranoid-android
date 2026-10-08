# Change: Remediate full-project security audit

## Why

A complete security review of runtime commit `33a9ebdc3d1d158984945c3053f866cdd20bbc8d` found nine validated violations of data-confidentiality or resource-enforcement boundaries. Existing selective-transformation approval does not close these defects. The owner authorized OpenSpec remediation, recurring work, a fresh full security review after fixes, and RC publication only when review and release gates pass (2026-10-05).

## What Changes

- Block exact sensitive residuals in Trino rule profiling and retain SQL physical-column sensitivity across aliases.
- Keep local category literals local at the OpenAI boundary, enforce folder numeric sensitivity consistently, and bind category permission to profile cache reuse.
- Bound formula work before allocation, decoded Parquet materialization and cumulative cells, CSV request deadlines, and audit record reads.
- Add focused synthetic regressions, relevant public documentation/changelog updates, and recorded exact-SHA validation.
- Re-audit the complete final project after fixes. Confirmed new findings return the workflow to remediation.
- Release only `1.6.0rc1` (or the next unused RC in that series if already published), after the existing selective-transformation acceptance and every release gate. Stable publication is not authorized.

## Impact

Affected capabilities: safe-csv-profiling, sql-query-source-profiling, mcp-interface, synthetic-generation, dataset-validation, agent-orchestration and release-supply-chain. No unrestricted SQL, production data, live DB/provider access, source-row copying or relaxed privacy policy is authorized. Preserve existing API behavior for valid safe inputs; document necessary fail-closed changes. Prefer shared enforcement over transport-only guards.

## Authority And Completion

The user authorizes implementation, tests, focused commit/push, and conditional RC release. Required GitHub approval, signatures, immutable tags, accepted source identity, provenance and artifact verification remain real gates and must never be fabricated or bypassed. This change complements `selective-source-transformation`; its remaining acceptance tasks remain mandatory. See [tasks](tasks.md) and [audit evidence](evidence.md).
