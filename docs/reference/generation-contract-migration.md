# Generation Contract Corrections

These corrections are planned for `1.3.2rc1`, followed by stable `1.3.2` after
candidate acceptance. Until public release verification completes, use the
existing stable release for the published installation instructions.

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
with validation evidence. Row privacy remains mandatory in every mode.
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
