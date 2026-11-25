# Design: Numeric CSV Fields And Phone Inference

## Separate Representation From Sensitive Content

The existing phone regex is intentionally conservative for isolated strings.
It is also used by strict generation safety, content masking, local categories
and provider checks. Keep that classifier and every detector priority unchanged.
An ambiguous digit string alone is insufficient evidence to declare a whole
neutral numeric column a phone field.

During CSV profile finalization, use the existing full-column numeric evidence:
every nonempty value must parse as a finite integer or float. If that column has
no explicit phone-name hint and the only proposed sensitive semantic is phone,
retain its numeric data type and clear the inferred phone semantic. Empty or
mixed columns do not qualify. Known phone names and formatted phone values that
do not parse as numbers keep their existing phone inference. Stronger SSN,
payment-card and secret detections retain their existing priority.

Keep the conservative content-sensitive flag independently of this semantic
decision. Ambiguous numeric columns remain sensitive, retain masked evidence
and suppress exact minima, maxima and percentiles. They gain no authorization
to preserve local categories or source values. Numeric generation follows the
numeric field type rather than the erroneous phone semantic. No raw input is
copied into generated output.

## Share The Existing CSV Numeric Policy

Single-file CSV already checks numeric content through
`_csv_sensitive_value_type`. Use that same policy in folder profiling rather
than reimplementing or broadening it. It checks original and canonical numeric
representations, including the float representation retained by statistics,
with finite-value and expansion bounds. Stronger content signals remain
sensitive even when a source spelling initially hides them.

Retain the existing exemption only for negative non-integral decimal measures
whose retained representation also stays fractional. Positive dotted values
and integral decimal identifiers remain potentially sensitive. The semantic
correction does not add an exemption to those content checks. Type and
sensitivity inference still inspect every nonempty value; a late sensitive
outlier must not be hidden by the bounded semantic sample.

Keep the profile accumulator's existing streaming pass and bounded retained
evidence. Set and DuckDB distinct counting must produce the same complete
profile; neither backend decides phone semantics.

## Cache And Compatibility

Set `PROFILE_CACHE_FORMAT_VERSION` to 6. Matching version-5 cache entries become
misses and are recomputed from the bounded input path. Keep metadata-only cache
contents, source binding, private publication and error behavior unchanged.
Existing saved profile or plan files are not migrated in place; reprofile to
obtain corrected inference. The profile fingerprint can change because its
field type or semantic metadata changes intentionally.

Historical OpenSpec and benchmark JSON/Markdown evidence remains immutable.
The correction adds no dependency, CLI flag, public signature or generation
seed algorithm. Determinism is verified for the corrected inferred specification;
output is not required to match a specification that previously generated the
wrong phone field.

## Verification

Completed verification covers single-file/folder and batch/accumulator inference,
numeric and mixed columns, explicit phone evidence, stronger sensitive detectors,
late outliers, normalized numeric representations, cache invalidation and
deterministic numeric generation. Ambiguous exact statistics and raw categories
remain suppressed. Executed regression gates are in [validation.md](validation.md).
