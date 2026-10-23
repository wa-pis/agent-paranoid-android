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
- Mypy passed for all 155 production source files with a disposable cache.
- Separate existing authentication/CLI/SQL-query regressions: 259 passed,
  one isolated registration-candidate test skipped; no live calls.


## Reviewed CSV numeric replacement verification

The shared finite parser and full-input sensitivity inspection remain enforced.
40 fictional cases cover standalone column/schema helpers and both streaming
CSV paths, late formatted phones/secrets/cards/nonfinite or nonnumeric outliers,
protected names, native numeric and exponent storage, old ambiguous profiles,
primary-key/relationship bindings, SQL authority exclusion, source-free CLI
artifacts, typed authored ranges, cache v7 recomputation, provider projection
and rejection of advisor declassification. The original profile remains
sensitive and unchanged; neither source ranges nor exact source precision are
copied into generation settings.

An end-to-end CLI agent test plans from CSV, infers an independently reviewed
numeric field into a separate file, copies only that field while preserving the
planned generation settings, rejects approval with the old spec hash, reviews
the new hash and generates with a persistent approval receipt. The source
profile stays byte-identical and the manifest asserts synthetic generation
without copied source rows. This is an awaiting-approval edit, not a mutation
of an already approved plan.

368 focused numeric, CSV adapter/cache, DECIMAL, CLI, contract fixture,
agent planning/review/approval, advisor, OpenAI/GigaChat fake-provider and
documentation tests passed. Mypy (156 source files), Ruff, strict MkDocs and
strict OpenSpec passed. Checked-in public contract fixtures remain current;
DatasetSpec schema/version is unchanged. Absent storage metadata remains
omitted, while present storage evidence changes the profile fingerprint.

Full candidate CI remains pending. No package publication, live database access,
source-fidelity claim or automatic phone declassification is established.


Merged checkpoint: #645 passed full green CI and merged as
`80145958b579540b6852c6860de27f41a591c79d`, superseding the pending CI statement
above. Main documentation deployment 39921070445 completed successfully.
The combined exact-source runtime candidate release gate subsequently passed
with 4603 tests and 91.90% coverage. N7 candidate verification is complete;
no package release or additional source authorization is implied.
