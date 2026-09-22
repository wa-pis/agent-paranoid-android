# Design: generation-contract-hardening

## Approach

1. Filter rejected constraints and relationships in both execution and validation.
   Order formula assignments using stdlib topological sorting and the existing
   bounded expression parser. Reject cyclic or duplicate formula targets safely.
   Other interacting constraints must pass final validation; this is not a
   general-purpose constraint solver.
2. Preserve nullable non-primary-key foreign-key nulls, including identifier
   fields; wire only present child keys. Validate nulls against field nullability.
3. Reuse generated-row privacy validation below adapters. Enforce complete
   schema, relationship and constraint checks for non-negative generation,
   independently of optional report settings. Recheck after business-rule
   mutation and before publishing every bundle, including single-file output.
4. Required identifiers follow normal nullability. String-pattern bounds count
   the entire output; retain a synthetic prefix where it fits, generate random
   characters for shorter non-sensitive strings. Empty strings remain interpreted
   as missing by the existing CSV contract, so non-nullable fields need positive
   length. Sensitive fields continue to use their dedicated synthetic namespace.

## Failure Modes

Errors are value-free and occur before publication. Existing output is unchanged
on rejection. Mixed/negative cases may violate schema or business rules but must
always pass row privacy. Unsupported interacting rules fail explicitly rather
than publishing a falsely valid dataset.

## Alternatives

Do not add an iterative solver or a new dependency. Ordering formula dependencies
and rejecting remaining unsatisfied contracts is bounded and reviewable. Do not
rename existing validation sections; make the privacy section check its input.

## Release-validation correction

Stable preparation after accepted RC1 generated the reserved SQL keyword `AS`
as an unquoted catalog in an existing property test. SQL parsing correctly
rejected it before allowlist checking; the test expected only AllowlistError.
RC2 prefixes unquoted generated identifiers with `outside_`, retains arbitrary
quoted identifiers, and explicitly exercises the failing example. Production
SQL enforcement and the strict allowlist-error assertion are unchanged. This
safety-test correction requires a new RC under the release contract.
