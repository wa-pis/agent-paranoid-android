# Generation Contract Corrections

English · [Русский](../ru/reference/generation-contract-migration.md)

These corrections are included in stable `1.6.0`. Regenerate affected fixtures
and review differences when upgrading. Package version and DatasetSpec schema
version are separate; the current specification schema is `1.1`.

## Changed Results

- Formula dependencies are computed before their consumers, regardless of list
  order. Cycles and multiple assignments to the same formula target fail early.
- Constraints and relationships marked `rejected` are ignored by generation and
  validation. Existing `inferred` rules in an explicitly supplied specification
  remain executable; the agent workflow still requires fingerprint approval.
  Remove or revise active aggregate mappings that depend on a rejected link;
  they fail validation instead of being silently skipped.
- Nullable foreign keys preserve generated nulls. One-to-one capacity counts
  only non-null child references. Required identifiers cannot be empty or null.
- String-pattern lengths describe the entire string, including any synthetic
  prefix. Short non-sensitive strings use random characters where a prefix does
  not fit. A required string cannot have a zero maximum length.

Regenerate affected fixtures and review resulting differences. A fixed seed
remains reproducible within the recorded generator version and environment;
it does not promise identical bytes across this upgrade.

## Publication And Validation

Valid, edge, and load-test generation must pass all core schema, relationship,
constraint, and privacy checks before returning rows or publishing output.
Turning off report sections does not disable these generation checks. Business
rule mutations are checked again before publication. Failures preserve existing
output and do not publish a new successful bundle.

Explicit mixed and negative generation still publish controlled-invalid data
with validation evidence. Parquet uses explicitly marked scalar columns
when intentionally malformed cells cannot fit native Arrow types. The bundle
reader restores those cells for validation; consumers reading Parquet directly
must inspect the `apa.scalar_encoding` field metadata. Ordinary valid-mode
values incompatible with declared types still reject the whole export without
partial publication. Row privacy remains mandatory in every mode.
The RC5 CLI reports `validation_failed` with exit 1 for intentionally
invalid results while retaining the representable output, manifest and report.
Explicit mode/ratio overrides must be reflected in effective execution evidence;
an invalid artifact is not a successful validation.
Standalone `validate` now inspects row values when its privacy section is
enabled, in addition to checking specification safety. CSV numeric values are
interpreted using their declared numeric type before privacy classification.
This decoding exception applies to revalidation only; generated formula and
business-rule strings retain the strict pre-export privacy check.

These checks detect recognizable sensitive strings using the existing synthetic
namespace policy. They do not certify anonymity or prove that data has never
come from a source. Keep the source-row checks and organization-specific review.

The solver does not search for a solution to arbitrary interacting rules. If
later temporal, conditional, or aggregate changes invalidate an earlier rule,
the operation fails; revise the specification rather than consuming partial
output. Numeric sampling remains uniform between configured bounds and foreign
key assignment remains round-robin among non-null child rows. These are not
claims of preserving correlations or source fan-out distributions.

## Additive validation utility evidence

New reports add `utility` with the canonical effective-spec hash, active native
relationship/temporal declaration counts and executed/not-declared/not-run status.
Temporal metrics add generated checked/failing row counts. Existing validity,
settings, section errors and relationship metrics retain their semantics. Old
saved reports without `utility` remain accepted. JSON consumers that enforce
exact keys must admit this new optional field.

Generated row values, DatasetSpec versions and existing profile/spec hashes are
unchanged. Serialized validation reports and their manifest output digests do
change. Compare replayed rows separately from report byte identity across this
upgrade; the new contract fixtures record the intentional report changes.
Unknown source fidelity, fan-out and missing relationship coverage remain
unknown. No source queries, new authorization, dependency, package publication
or completed release-candidate acceptance is implied.


### Parquet distinctness evidence

Reprofile Parquet sources to obtain bounded non-null distinctness. Old profiles
retain unknown values. Newly profiled scalar columns may have `exact` or
`lower_bound` unique-ratio evidence using existing schema fields; changed profile
fingerprints require fresh plan review. This adds no primary-key nomination,
identifier pool or source key reuse. Missing null metadata still blocks automatic
spec inference. Existing dataset/profile schema versions remain unchanged.


### Long fractional datetime intervals

Datetime range sampling now computes its whole-second span with integer
arithmetic. Very long fractional intervals previously could round the maximum
admissible offset up and exceed the upper bound by a microsecond. Replaying such
an affected specification may produce different values after upgrading; compare
the manifest's generator version. The existing second-resolution policy,
missing-bound fallbacks and schema version are unchanged. This does not add
monthly/calendar inference or certify source-period fidelity.


A partial date/time bound must also be compatible with the existing missing
endpoint defaults (minimum 2020-01-01, maximum 2025-01-01). A maximum before
2020 or minimum after 2025 now rejects instead of silently clamping an inverted
interval. Supply both ordered bounds for earlier or later periods. Failure leaves
previous dataset artifacts unchanged and publishes no new manifest.
