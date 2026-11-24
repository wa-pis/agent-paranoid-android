# Design: Value Normalization Performance

## Remove Redundant Lookup, Preserve The Walk

Check every row structure and every value's scalar eligibility as before.
After that check, actual non-string values need no string parser lookup.
Only eligible strings may use the existing declared integer, float or boolean
parser. Preserve parser calls, nullable empty-string handling and failed-parse
behavior. Do not infer a new conversion from a source label or scalar value.

Prepare the scalar-type tuple and each field's parser/nullability metadata once
within the current call. Keep entries for every field, including fields without
a parser, preserving the existing last-entry behavior for mutable duplicate
names. Rebuild from the current specification. Retain no rows, conversion results
or mutable specification state globally. Do not reuse preparation across
callbacks or later calls.

Preserve error order, structural filtering, copy-on-write behavior and object
identities. Return the original dataset when no conversion or structural/scalar
error occurs; retain unchanged row objects when another row is copied. Never
mutate caller rows or specifications.

## Shared Safety Boundaries

The same normalizer serves report validation and checked generation workflows
for every source-derived specification. Raw generated-string privacy remains
separate and must not be replaced by decoded report values. No source-row reads,
broader SQL, weaker resource budgets, new backend or optional dependency is
needed. Schema, relationship, constraint, privacy and publication checks keep
their settings, order and mutation boundaries.

Ordinary and tiled generation retain their distinct seed namespaces. Each path
must reproduce its own prior output byte for byte.

## Evidence

Use bounded fictional data to identify redundant work. Compare a frozen previous
normalizer with the candidate for exact output values, errors, exceptions,
container/row identities and input non-mutation across supported scalars,
numeric/boolean strings, invalid structures, subclasses, unknown fields/entities
and specification edits.

Repeat the unchanged public CSV benchmark for 100,000 and 750,000 rows with 25
fields: three fresh subprocesses per path/size, alternating order, fixed seed
and existing limits, with no concurrent heavy verification. Record exclusive
stages, sampled process-tree RSS, actual validator coverage and artifact audits.
Compare output hashes with the latest schema-validation series and retain all
historical evidence, private permissions and cleanup checks.
