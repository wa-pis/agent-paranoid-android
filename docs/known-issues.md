# Known Issues

This page records security findings that are understood and accepted for the
`1.0.0rc6` and `1.0.0` product scope. They remain scheduled work; acceptance
does not mean that the behavior is safe for a broader deployment model.

The source is repository-wide Codex Security scan
`484dfa30-85d2-4059-b39b-2c52c9d0f5ed` of immutable commit
`2c714a6d4df75a1faab422055593fc50a2061a03`. All four findings are **Low**.
Risk owner: [@wa-pis](https://github.com/wa-pis). Target: the first post-1.0
security-hardening release. The RC6 disposition PR and its merge are the
attributable product-risk acceptance; they are not independent security
approval of the final release commit.

## AG-04: Provider Response Pre-Parse Bounds

- Finding: `csf_83170308250423cefd103d0d`
- Occurrence: `occ_9873a9a253a90382015b81c6`
- Fingerprint:
  `codex-security/v1:sha256:154204f45b99b73f72dc88274da62359310ee2361b851b29428b234cd133bc96`
- Rule: `resource-exhaustion.provider-response-preparse`

The optional advisor adapter can pass oversized provider output into JSON
parsing before applying local byte and structural limits. Provider output-token
hints, typed validation, and optional use reduce likelihood, but do not provide
a local pre-parse guarantee.

Revisit before accepting an untrusted provider or proxy, increasing provider
response limits, or operating the advisor as a shared multi-tenant service.

## FS-11: JSON Depth After Materialization

- Finding: `csf_d7760aedb0596e6d0998da23`
- Occurrence: `occ_9d4d5c81982172b3c0e0bde5`
- Fingerprint:
  `codex-security/v1:sha256:31c3e170ade78db51d05d695d3b574b8ee50eec060702cdfb03a4d8706de55dd`
- Rule: `resource-exhaustion.json-depth-after-parse`

Dataset JSON is materialized before its structural check, while profile and
spec importers do not uniformly apply that check. Input byte limits and typed
models bound common cases, but adversarial nesting can consume parser work
first.

Revisit before increasing JSON byte limits or exposing file importers through a
shared or multi-tenant service.

## MT-02: Same-Caller MCP Argument Reflection

- Finding: `csf_7b1cee56a15d9ea40705a6e0`
- Occurrence: `occ_3490f19b25f4117b792cdbca`
- Fingerprint:
  `codex-security/v1:sha256:da37d59b6b33173a5b0db72ecceef92694ad6ce0c7f942180e9478266e45aedf`
- Rule: `error-disclosure.mcp-argument-reflection`

FastMCP/Pydantic validation can echo a bounded rejected argument to the caller
before application diagnostics run. The reflected value originates from the
same caller; application errors remain fixed and source-free.

Revisit before a gateway can submit values for another principal or route tool
errors across principal boundaries.

## MT-03: Malformed MCP Value In Local Logs

- Finding: `csf_afe00adf1fc2884d910eea07`
- Occurrence: `occ_a29278197dd63475ead2653e`
- Fingerprint:
  `codex-security/v1:sha256:b118d28265c9382250b940dda7d9027ad9ed96c4053d66a98797a5c19061c794`
- Rule: `log-disclosure.malformed-mcp-payload`

Bounded malformed JSON-RPC values can remain in local MCP SDK logs. Client
errors are fixed and no server secret or log-forging path was demonstrated,
but caller text can persist in operator diagnostics.

Revisit before logs become broadly accessible or a gateway can submit values
belonging to another principal.
