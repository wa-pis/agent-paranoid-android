# Design

First build a matrix of plain numeric measures, integer-like IDs, formatted
phones, exponent notation, mixed strings, nonfinite values and late secrets.
Exercise `CSVColumnAccumulator`, `profile_column`, profile-to-spec conversion,
generation and revalidation with newly constructed fixtures.

Do not reorder numeric parsing ahead of all privacy detection. Prefer reusing a
typed, exact field declaration with the existing numeric_measure checks; decide
whether profiling needs a new reviewed declaration only after that matrix.
Separate storage type from sensitivity so changing a type cannot erase privacy
classification. Bound both exact parsing and float-normalized representations.

Do not change `_is_synthetic_sensitive_value` to accept any prefixed string as a
phone: generated-value validation must still enforce the declared safe provider.


## Chosen declaration and enforcement

Reuse `infer-spec --decimal-fields` as an independently authored synthetic
replacement. Do not add a profiling permission flag or remove source phone
classification. Optional `numeric_storage_type` records complete non-null
integer/finite-float parse evidence for ambiguous phone-like fields in both CSV
paths and standalone helpers. It retains neither raw text, extrema nor declared
precision/scale. Late invalid content vetoes complete evidence; phone/secret
inspection still sees the entire admitted input.

The deterministic inference service accepts only matching non-sensitive,
non-identifier `numeric_measure` DECIMAL FieldSpecs with an existing validated
`decimal_range`. Name-based sensitivity and quasi-identifier vetoes reuse the
local-category field eligibility check, without granting category preservation.
CSV primary-key candidates and relationship endpoints are excluded from the
replacement domain. Native CSV numeric fields can use authored ranges too;
SQL/Parquet DECIMAL continues to require declared precision/scale agreement.
Source distributions are never used to infer exact synthetic decimal bounds.

Changed profile evidence is fingerprint-bound. Omit absent metadata to preserve
legacy hashes. Folder cache format 8 forces recomputation of older evidence;
old saved ambiguous profiles without storage metadata require reprofiling rather
than silent promotion. DatasetSpec has no new field/version. Provider requests
keep source sensitivity, and advisors cannot clear it automatically. For an awaiting-approval workspace, copy only the reviewed field into its
spec, preserve request-bound generation settings, and review/approve the new
fingerprint. Changed source/profile evidence requires a new plan; never rewrite
an already approved plan. Existing audit/publication contracts remain in force.
