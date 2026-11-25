# Privacy Detector Performance

## Status

Implementation and verification completed, unreleased, 2026-11-22. This
internal execution change selects no version, tag or publication.
See [verification](validation.md) and the [public CSV benchmark](benchmark.md).

## Why

The [privacy-validation benchmark](../privacy-validation-performance/benchmark.md)
left strict row privacy as the largest coordinator stage. A bounded synthetic
profile identifies unproductive secret-assignment regular-expression searches
and email matches as useful remaining work to remove. Every successful match
already requires a literal separator that a string membership check can test.

## What Changes

- Search the existing secret-assignment expression only when text contains
  `:` or `=`; match the existing email expression only when text contains `@`.
- Preserve the complete original expressions, flags, recognition priority,
  Unicode behavior, stripping, scalar handling and entropy calculation.
- Verify equivalence at the shared classifier and its existing consumers, then
  record fresh public CSV measurements against the latest privacy-validation
  baseline without replacing historical evidence.

## Safety And Compatibility

Both guards are necessary conditions of their original patterns, not new
recognition policy. No recognizable value may change classification. Strict
generated-value and report-only numeric-string policies, synthetic namespaces,
all generation modes and callback boundaries remain unchanged. No value cache,
raw-value retention, random calls, public signature, option, dependency,
artifact schema, generator algorithm or seed behavior changes.
