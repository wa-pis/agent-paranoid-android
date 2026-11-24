# Design: Privacy Signal Strength

## Preserve Detection, Retain Its Reason

`core/privacy.py` exposes an internal fixed-enum signal classifier through
`infer_sensitive_value_signal`. It follows the original stripping, exclusions,
regexes, helper calculations, match priority and failure behavior. The existing
`infer_sensitive_value_type` maps the signal back to its previous `ssn`, `secret`,
`phone` or `email` tag. Existing safety consumers continue using that compatible
surface; the richer result is for semantic evidence, not declassification.

Static enum outcomes contain no source spelling and require no per-match value
object. Whole-column counters retain only fixed signal categories and counts.
Neither signal reasons nor counters become new serialized artifact fields.

## Strong And Weak Evidence

| Signal | Semantic support |
| --- | --- |
| Known credential prefix, private-key marker, explicit Bearer or secret assignment | Strong credential context; any occurrence retains secret priority |
| SSN shape with both expected ASCII hyphens | Structured SSN evidence; at least 80% of nonempty column values and no conflicting name hint |
| Bare or partially hyphenated SSN-shaped digits | Weak; compatible SSN or `tax_id` name context and at least 80% support |
| Luhn match | Weak; complete-word card, `cc` or PAN context and at least 80% support; resulting semantic remains `secret` |
| Entropy or JWT shape | Weak; compatible secret/token/password/credential or explicit key-phrase context and at least 80% support |

Structured SSN formatting is evidence of purpose, not proof of an assigned or
valid identity. A Luhn checksum or token-like shape alone likewise proves no
field purpose. Generic `key`, identifier and hash names do not supply credential
context. Context uses the existing word tokenizer, including complete phrases
such as `api_key`, `access_key` and `client_secret`; substring collisions such as
`cardinality` do not qualify. Numeric role handling and fixed conflict rules
remain part of the unified resolver.

All contextual thresholds use integer comparisons over all nonempty values.
Email and phone policy remains unchanged. Strong credential evidence retains
its existing rare-value priority even when ordinary rows dominate the column.

## Reuse Weighted Aggregate Evidence Safely

Trino profile completion and legacy aggregate-profile adaptation apply the same
signal-strength policy to their existing `top_values`. Reuse available value
counts as weights; do not repeat a detector once per counted row or add a query,
sample, row-returning operation or expanded database permission.

Threshold inference requires strictly validated integer count metadata and a
known strict-integer full non-null population. That denominator must be at
least the sum of observed category counts. Compare weighted support with the
full denominator, including values outside the bounded top-value list; a small
observed subset cannot certify 80% column support.

Unknown or malformed coverage cannot support contextual or threshold-based
semantic inference. Only the existing strong-credential priority can establish
new inferred semantics in that case. Independently inspect recognized content
for privacy even when an item's count or coverage metadata is invalid: a bad
count must not make a possibly sensitive value publishable. Weak signals still
require suppression and generic masks when they do not establish semantics.

Preserve existing explicit semantic metadata in saved profiles. Its presence
is a distinct input contract, not permission to bypass sensitive-content checks.
Missing inferred semantics does not remove source sensitivity, and adapter
conversion must not recreate a coarse secret/SSN promotion rejected by the
shared resolver. No new aggregate field or database operation is introduced.

## Carry Signals Through Numeric Normalization

The single-file and folder CSV paths share the existing finite, magnitude and
expansion-bounded numeric-content policy. Preserve the signal detected in an
allowed canonical or retained-float representation. Reclassifying only the
original exponent spelling would lose the reason for a possible card or SSN.
Keep existing type-tag priority and the narrow negative-fraction exception;
the strength split adds no new content exemption.

An uncorroborated weak signal continues setting the sensitive flag and
suppressing exact extrema, percentiles and raw categories. Its masked evidence
uses generic length labels rather than claiming SSN or secret semantics. The
shared strict detector, masking authority and local-category rejection remain
conservative regardless of that presentation change.

## Accuracy Evidence And Compatibility

The synthetic accuracy corpus is labeled independently of the implementation.
Include positive and hard-negative columns for SSN, cards, entropy/JWT and
strong credential formats, plus unchanged benign/email/phone cases. Measure
semantic precision and recall separately from conservative privacy protection:
an ordinary opaque identifier may correctly remain sensitive with unknown
semantics. Publish aggregate counts/metrics and case identifiers only, never
matched source spellings. Results describe this bounded corpus, not general
recognition accuracy or real-world prevalence.

Check all four CSV profiling views, reverse and fixed-seed shuffled orders,
late values, threshold boundaries, safe profiles/specs and seeded generation.
Aggregate adapter regressions cover weighted 79/80% support, partial top-value
coverage, unknown/malformed denominators or counts, retained privacy, explicit
semantic metadata and strong-credential priority without added database access.
Existing strict classifier equivalence tests remain authoritative for legacy
tags and failures. Semantic/type/sensitivity invariance does not extend to
existing reservoirs, category ties or full profile serialization.

Folder cache format 8 rejects version 7 and earlier entries and recomputes
inference under the existing budgets. Saved profiles/plans are not silently
migrated. No dependency, CLI option, generator seed algorithm or public artifact
field changes. Historical OpenSpec and benchmark JSON/Markdown stay immutable.

## Verification

Executed verification is recorded in [validation.md](validation.md), with source
hashes and aggregate corpus metrics in [accuracy-results.json](accuracy-results.json).
The full suite passed 2402 tests with 10 skips; the 67-case corpus reduced
semantic false positives from 24 to zero without additional semantic misses or
privacy-label regressions. These are synthetic-corpus results, not real-world
accuracy guarantees.
