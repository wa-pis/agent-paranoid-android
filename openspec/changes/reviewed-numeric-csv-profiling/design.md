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
