# Known Issues

This page records security findings that are understood and accepted for the
`1.0.0rc6` and `1.0.0` product scope. They are retained as historical finding
records after resolution; the original acceptance did not prove that the
behavior was safe for a broader deployment model.

The source is repository-wide Codex Security scan
`484dfa30-85d2-4059-b39b-2c52c9d0f5ed` of immutable commit
`2c714a6d4df75a1faab422055593fc50a2061a03`. All four findings are **Low** and
are resolved on `main` for the next `1.2.0` release. Risk owner:
[@wa-pis](https://github.com/wa-pis). The original disposition was product-risk
acceptance, not proof that broader deployment models are safe. The separate
AI-assisted independent review of the exact RC6 commit is recorded in the
[RC6 security evidence](https://github.com/wa-pis/agent-paranoid-android/blob/main/openspec/changes/archive/2026-08-14-1-0-0-rc6-final-release-candidate/security-review-evidence.md)
and [issue #397](https://github.com/wa-pis/agent-paranoid-android/issues/397).

## AG-04: Provider Response Pre-Parse Bounds

**Status:** resolved on `main` for the next `1.2.0` release.

Resolution contract: [archived OpenSpec change](https://github.com/wa-pis/agent-paranoid-android/blob/main/openspec/changes/archive/2026-08-14-1-2-0-provider-response-preparse-bound/proposal.md).

- Finding: `csf_83170308250423cefd103d0d`
- Occurrence: `occ_9873a9a253a90382015b81c6`
- Fingerprint:
  `codex-security/v1:sha256:154204f45b99b73f72dc88274da62359310ee2361b851b29428b234cd133bc96`
- Rule: `resource-exhaustion.provider-response-preparse`

The OpenAI advisor previously passed provider output text into application JSON
parsing before applying a local response-byte limit. The typed provider settings
now impose a bounded UTF-8 response budget and reject oversized output with a
fixed redacted error before application JSON/Pydantic parsing. GigaChat already
enforced the equivalent boundary.

The SDK still materializes its own response envelope before the application can
inspect `output_text`; revisit transport streaming before operating an advisor
as a shared multi-tenant service.

## FS-11: JSON Depth After Materialization

**Status:** resolved on `main` for the next `1.2.0` release.

Resolution contract: [archived OpenSpec change](https://github.com/wa-pis/agent-paranoid-android/blob/main/openspec/changes/archive/2026-08-15-1-2-0-json-depth-preparse-bound/proposal.md).

- Finding: `csf_d7760aedb0596e6d0998da23`
- Occurrence: `occ_9d4d5c81982172b3c0e0bde5`
- Fingerprint:
  `codex-security/v1:sha256:31c3e170ade78db51d05d695d3b574b8ee50eec060702cdfb03a4d8706de55dd`
- Rule: `resource-exhaustion.json-depth-after-parse`

JSON datasets, JSON profile/spec imports, and profile-cache documents now pass
through one non-recursive structural-depth scan before `json.loads` or Pydantic
can materialize nested objects. The scan ignores brackets inside JSON strings,
uses the existing typed environment budget, and fails closed without publishing
a partial dataset, profile, or spec.

Input byte, row, cell, and typed-model limits remain independent defenses.

## MT-02: Same-Caller MCP Argument Reflection

**Status:** resolved on `main` for the next `1.2.0` release.

Resolution contract: [archived OpenSpec change](https://github.com/wa-pis/agent-paranoid-android/blob/main/openspec/changes/archive/2026-08-15-1-2-0-mcp-argument-redaction/proposal.md).

- Finding: `csf_7b1cee56a15d9ea40705a6e0`
- Occurrence: `occ_3490f19b25f4117b792cdbca`
- Fingerprint:
  `codex-security/v1:sha256:da37d59b6b33173a5b0db72ecceef92694ad6ce0c7f942180e9478266e45aedf`
- Rule: `error-disclosure.mcp-argument-reflection`

Generator and Trino MCP servers now catch the typed FastMCP/Pydantic validation
failure before tool execution and replace it with the fixed
`Tool arguments failed validation` error. The rejected value and nested
validation exception are detached and do not enter the MCP result.

Tool schemas and non-validation application errors are unchanged.

## MT-03: Malformed MCP Value In Local Logs

**Status:** resolved on `main` for the next `1.2.0` release.

Resolution contract: [archived OpenSpec change](https://github.com/wa-pis/agent-paranoid-android/blob/main/openspec/changes/archive/2026-08-15-1-2-0-mcp-malformed-log-redaction/proposal.md).

- Finding: `csf_afe00adf1fc2884d910eea07`
- Occurrence: `occ_a29278197dd63475ead2653e`
- Fingerprint:
  `codex-security/v1:sha256:b118d28265c9382250b940dda7d9027ad9ed96c4053d66a98797a5c19061c794`
- Rule: `log-disclosure.malformed-mcp-payload`

The shared bounded stdio transport now validates typed MCP client messages
before SDK dispatch. Malformed requests receive the fixed
`Invalid request parameters` response, while malformed notifications remain
response-free. Rejected values are not passed to the SDK and therefore cannot
enter its local validation logs or retained exception state.

Valid requests, notifications, tool schemas, and non-validation application
errors are unchanged.
