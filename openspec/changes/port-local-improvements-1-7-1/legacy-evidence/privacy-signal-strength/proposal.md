# Privacy Signal Strength

## Status

Implemented and locally verified, unreleased, 2026-11-22. The synthetic accuracy
corpus, safety and deterministic behavior pass focused and full regressions;
see [verification](validation.md). This change selects no version, tag, release
or publication.

## Why

Conservative privacy detection intentionally flags nine-digit strings, Luhn
matches and high-entropy identifiers. Those signals can protect possible PII
without proving that a column represents SSNs, payment cards or credentials.
Whole-column CSV and aggregate top-value inference can promote coarse secret
or SSN matches without distinguishing this ambiguity. Aggregate adapters must
also avoid treating a small observed category subset as the full population.

## What Changes

- Retain a fixed reason for each existing content-classification outcome,
  without retaining the matched value or changing strict privacy decisions.
- Require compatible name context and whole-column support before weak SSN,
  card, entropy or JWT-shape signals assign semantics.
- Apply the same policy to Trino and legacy aggregate adapters using existing
  top-value counts and a validated full non-null denominator, without new SQL
  or row-returning access.
- Keep strong credential formats decisive and structured SSN formatting subject
  to the existing column-dominance threshold.
- Preserve conservative sensitivity and summary suppression, using generic
  masked lengths for weak evidence that does not establish semantics.
- Add an independently labeled synthetic accuracy corpus with hard negatives,
  separate semantic precision/recall from privacy protection, and refresh old
  inferred profiles through cache format 8.

## Safety And Compatibility

`infer_sensitive_value_type` retains its exact prior tags, match priority and
exception behavior. Masking, local-category checks, mandatory generated-row
privacy and bounded numeric normalization keep their existing safety decisions.
Unknown semantics never authorize disclosure. Weak signals remain sensitive
and cannot publish raw categories or exact numeric summaries.

The internal reason enum and aggregate counters add no artifact field, raw
value retention, random call, dependency or CLI option. Semantic/type/sensitivity
decisions remain independent of row order; existing bounded distributions do
not promise byte-identical complete profiles. Corrected specifications remain
reproducible with an explicit seed. Saved profiles/plans are not rewritten;
reprofile them to obtain the new inference. Existing explicit semantic metadata
is preserved rather than silently re-inferred. Historical evidence is unchanged.
