# Design: Privacy Detector Performance

## Necessary Characters Before Existing Patterns

Keep `infer_sensitive_value_type` in `core/privacy.py` and change only dispatch
to two original expressions:

1. `SECRET_ASSIGNMENT_RE` requires the literal character class `[:=]` between
   its existing keyword and value. If neither character occurs anywhere in the
   stripped text, its search cannot succeed. Otherwise invoke the same search.
2. `EMAIL_RE` requires a literal `@`. If that character is absent, its full match
   cannot succeed. Otherwise invoke the same full match.

For each pattern, the guard being false proves the original match was false;
when the guard is true, the original expression decides the result. The guards
therefore preserve every recognition and rejection. They do not lowercase text,
restrict the input alphabet, reinterpret punctuation, or replace search with a
prefix test. Unicode case-insensitive keyword matches, embedded assignments,
whitespace, anchors and newline behavior remain the original regex engine's
responsibility.

Use `str.__contains__(text, literal)` for the three literal checks, matching the
underlying string content seen by the regex engine. The `in` operator can invoke
an overridden `__contains__` on a string subclass returned by its overridden
`strip`; a false result there must not hide a real assignment or email. Keep the
original stripping call and regex input unchanged while bypassing that new
membership-dispatch surface.

## Preserve The Whole Classifier

Keep non-string handling, stripping, blank handling and ISO-date exclusion in
their current order. Keep private-key, bearer, known-secret, assignment, JWT,
entropy, email, SSN, payment-card/Luhn and phone decisions in their current
priority. Do not alter any regular expression or flag. Keep entropy's alphabet
check, character classes, `Counter` insertion order, mathematical operations and
threshold unchanged. Neither guard uses a random generator or mutates text.

Do not cache values, detector results or caller policy, introduce a synthetic
prefix shortcut, skip strings based on declared field type, or retain inputs in
diagnostics. The only added work is literal membership testing of the
already present local string. All other detector calls keep their old inputs
and order; the guarded expressions run whenever a match remains possible.

## Shared Consumers And Policy Boundaries

This classifier also serves CSV normalization/profiling, schema profiling, Trino
masking, local-category validation, semantic-provider value validation and
business-rule contracts. Their existing classification, masking and rejection
decisions must remain equivalent; the change adds no adapter or consumer-specific
exception. Read-only database access, masking, source-row isolation and safe
provider boundaries remain enforced by their existing callers.

Mandatory generated-row privacy still classifies raw strings, including strings
in declared numeric fields, independently of disabled report sections. Existing
report validation may decode numeric strings under its separate explicit policy.
Neither policy changes. Composite errors, first-error order, synthetic namespaces,
callback rechecks and independent revalidation keep their existing boundaries.

## Evidence And Historical Baseline

Freeze the original classifier for differential comparisons, with synthetic-only
corpus, Unicode, newline, priority and seeded mixed-input cases. Cover shared
consumers and strict/report boundaries with focused tests, then run full project
checks. The [verification record](validation.md) contains the bounded profile's
metadata and immutable baseline fingerprints.

Use the existing public CSV fixture, policies, environment and audit assertions
for three fresh runs per size and path: 100,000 / 750,000 rows, ordinary serial /
four-worker streaming, twelve attempts in total. Write new evidence only under
this change. Every byte count and CSV hash must match the corresponding latest
privacy-validation reference. Retain all mandatory checks, concrete validator
coverage, report and manifest audits, budgets, private permissions, atomic
publication and cleanup. Do not infer export speed or memory improvements from
the classifier microprofile; completed public runs provide that evidence.
