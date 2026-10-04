# Full audit evidence

Runtime: `33a9ebdc3d1d158984945c3053f866cdd20bbc8d`; scan `7c5f98ba-72e6-4081-88a3-bee689b1d599`. Public/source baseline only. No private source rows, credentials or live access.

| ID | Priority | Finding | Offline proof |
| --- | --- | --- | --- |
| F1 | P1 | Trino exact sensitive residuals | fake singleton aggregate retained; zero-formula SQL source trace |
| F2 | P2 | Sensitive SQL column alias becomes local category | authorized synthetic bigint alias retained with sensitive=false |
| F3 | P2 | OpenAI transmits local category literals | fake SDK: default masked; local transmitted; store=false |
| F4 | P2 | Folder exponent identifier enters numeric statistics | exact fictional numeric bound retained; profile safety passed |
| F5 | P2 | Cache preserves categories after opt-in removal | current allowlist empty; original safe enum labels retained |
| F6 | P2 | Formula allocates before budget enforcement | instrumented multiplier 10^12 reached; no huge allocation; small control passes |
| F7 | P2 | Parquet decoded expansion/cumulative cells | encoded8246B, decoded2098176B, limit65536B; accepted256rows |
| F8 | P2 | CSV MCP profiling ignores invocation deadline | injected clock2s vs1s; success and profile publication |
| F9 | P3 | Audit verifier reads full oversized line before bound | independent static CLI-to-parser trace |

The source review covers all production Python modules and release scripts/workflows. Unit tests/docs/specs were supporting evidence rather than independently line-reviewed wholesale. No fresh complete test suite or vulnerability-feed dependency audit was executed during discovery. Earlier passing tests are not proof of remediation.

Canonical report sealed: Codex Security scan `7c5f98ba-72e6-4081-88a3-bee689b1d599`, `report.md`; nine findings (high1, medium7, low1), original immutable runtime SHA. Retained outside repository by Codex Security. Future runs must record the new exact SHA, test results and canonical fresh-audit report before release.

## F9 remediation

Shared `verify_audit_log` reads at most4097bytes before parsing. Synthetic LF/no-LF oversized records fail on first bounded read; exact4096byte authenticated records pass.16audit tests, Ruff, focused mypy, strict OpenSpec and independent read-only candidate review pass. No full release gate or fresh whole-project audit yet.

## F4/F5 remediation

Folder exponent and rounded identifier forms now produce masked patterns without extrema. Cache format5 binds exact sorted scopes, preserves duplicate identity, verifies stored scopes and rejects format4. Tests cover default/allowed/changed permission, order, mismatch, repeated legitimate reuse and canonical privacy.89focused tests passed from writable temporary cwd; Ruff/focused mypy passed; independent review found no surviving route. Whole-project re-audit and RC gates remain pending.
