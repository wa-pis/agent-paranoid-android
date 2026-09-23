# Change Proposal: selective-source-transformation

## Status

Implementation authorized in the product discussion of 2026-09-23/24.
Target: 1.6.0rc1, not stable. Signed commits, push, sequential reviewed PR merges
after green CI/CD, and candidate publication are authorized. Release procedures
and independent review remain mandatory. This document does not authorize
production-data access or itself change current runtime guarantees.

## Summary

Add a separate, explicitly opted-in local transformation mode: exactly one
output row per input row. Preserve explicitly permitted reference fields in
their original combinations, replace selected financial or sensitive values,
and recompute declared dependent values. Support CSV and bounded, authorized
SQL-result inputs under the same field-policy contract.

This is not fully synthetic generation or an anonymity guarantee. The existing
aggregate-only profiling and source-free generation modes remain unchanged.

## Motivation

Financial development and testing need the same product codes, portfolios,
segments, reference keys and territorial-bank classifications that applications
already consume. Replacing all labels independently destroys those semantics;
retaining amounts unchanged exposes information that should be replaced.

The user confirmed one-to-one row correspondence and permits replacement values
to coincide with input values for zeros and rounded amounts.

## Scope

In scope:

- Explicit per-field preserve, synthesize, substitute, derive or drop decisions.
- User-declared sensitivity, including business confidentiality beyond PII.
- Explicit typed substitution dictionaries scoped to selected fields/domains.
- Substitution and mapping references in the editable data behavior profile,
  preserved through profile-to-specification conversion.
- A field-policy wizard and repository-wide documentation reconciliation.
- Preserved reference combinations, consistent key replacement and declared
  relationships/formulas.
- Explicit financial scale, precision, sign, null and equality policies.
- Local bounded processing, honest provenance and separate validation outcomes.
- CSV and approved SQL-result contracts; staged adapter delivery is permitted.

Out of scope:

- Implementation in this documentation change.
- Automatic declassification, implicit source copying, or external AI access
  to source rows.
- Dataset scaling, unrestricted SQL, automatic JOIN support, universal
  relationship inference, automatic anomaly reproduction or formal anonymity.
- Treating replacement of amounts as sufficient protection for retained rows.

## Safety Impact

Current AGENTS.md and project rules prohibit source-row reuse. Implementation
is blocked until an explicitly reviewed policy amendment scopes this new
surface and executable tests protect both it and the existing source-free mode.
Do not silently reinterpret the existing generate command or safety switches.

Only explicitly authorized non-sensitive reference values may be preserved.
User-declared sensitive fields must be synthesized or dropped; sensitivity
conflicts fail closed pending a separately reviewed policy, not an AI override.
Even permitted field combinations may identify people or disclose confidential
facts. Review and report that residual risk; never claim anonymization.

Source reads remain read-only, allowlisted and bounded. Source values, mappings
and original/replacement pairs must not enter logs, error messages, reports,
external providers or default MCP responses. Only the explicitly authorized
local output may contain preserved source values.

## Compatibility

Use a distinct versioned transformation contract; final API and CLI names
remain a design decision. Existing DatasetSpec and source-free manifests must
not be silently repurposed. Transformed outputs must explicitly disclose
preserved source data and must not claim fully synthetic/source-free output.
