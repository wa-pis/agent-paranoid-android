# Numeric CSV investigation and first fix

## Evidence

Fictional matrix in `tests/test_feedback_numeric_csv_matrix.py` covers standalone
columns, streaming single CSV and streaming folder fields. Positive decimal text,
integer-like text and exponent-normalized phone-like text remain protected.
Late formatted phones, SSNs, a test card number and a fictional credential after
the first 100 values still set sensitivity and never appear in serialized
profiles. Negative fractional measures retain current numeric behavior.

The new nonfinite matrix initially failed nine cases: NaN, infinity and exponent
overflow became FLOAT evidence in every route. The shared parser now requires
`math.isfinite`. Its callers include all three profiling paths, constraint mining,
string-backed schema validation, safety checks and PostgreSQL export. Existing
PostgreSQL finite checks remain in place. Native Python numeric validation is
outside this CSV-text correction.

Folder cache format advances to 7 so old numeric inference is not reused.
Persisted standalone profiles and approved plans are not silently rewritten;
users must reprofile affected sources and review the resulting specification.

## Checks

- 271 focused tests passed from a disposable source copy outside the managed
  worktree: CSV matrix/profiler, domain pipeline/cache, RC3/RC4 feedback, safety,
  constraint mining/validation, PostgreSQL SQL export/CLI, documentation,
  I/O workflows and runnable business-rule reference.
- The first managed-worktree run had six filesystem permission failures while
  creating the default profile cache. The identical source passes in the
  disposable copy; no path-policy relaxation was made.
- Ruff and strict OpenSpec validation passed. Strict MkDocs build passed.

## Still pending

A reviewed numeric CSV declaration remains a design decision. Existing
`infer-spec --decimal-fields` accepts declared DECIMAL profile fields only;
it must not be advertised as an override for a phone-like CSV field.
An independently authored, reviewed numeric DatasetSpec is an existing generation
route, not proof that a source field is safe. No new declassification flag or
source-derived exact bounds are introduced here. Candidate release gates and
external environment acceptance remain open.
