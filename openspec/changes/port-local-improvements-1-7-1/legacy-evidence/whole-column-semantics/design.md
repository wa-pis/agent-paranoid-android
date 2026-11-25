# Design: Whole-Column CSV Semantics

## One Bounded Evidence Model

`core/semantics.py` owns the pure semantic policy. A typed dataclass retains a
nonempty-value count and fixed-category detector counts. CSV adapters supply
the already computed outcome of the existing bounded numeric-content policy;
the evidence model receives no source values and performs no I/O. Each value
is counted in the existing profiling pass, including values after the bounded
sample. There is no new value cache, second source read or serialized evidence
field.

Single-file/folder accumulators and their batch helpers use this same resolver.
Email, phone and SSN candidates require `matches * 5 >= nonempty * 4`, preserving
an exact inclusive 80% boundary. Any secret retains its existing priority. A
dominant candidate conflicting with a single incompatible name hint yields no
semantic. Missing, insufficient or otherwise ambiguous evidence also yields no
semantic; all-null columns do not gain content semantics.

## Word-Based Name Hints And Representation

Split snake case, camel case and other separators into case-normalized tokens.
Use complete words or phrases rather than substring matches. Numeric role words
such as `count`, `amount` and `rate` suppress incompatible numeric name hints;
`number` is not a blanket exclusion because `phone_number` is a valid phone hint.
Numeric phone candidates require a compatible explicit phone hint. Nonnumeric
name/address hints may supply semantics only when no sensitive content match is
present. Conflicts have a fixed outcome rather than first-row precedence.

The semantic decision is authoritative for CSV type inference. Do not run the
old substring name fallback after the resolver returns no semantic, because it
would turn `email_count` and `headphone_count` back into contact types.
Recognized SSN fields use string representation in every CSV path. Name and
address semantics likewise normalize to strings, even when their values could
otherwise be parsed as dates, timestamps or booleans.

## Preserve Privacy Independently

Any content match keeps the field sensitive even when it supplies too little
support for a semantic type. Suppress raw categories, exact extrema and
percentiles under the existing sensitive-field policy. One late secret must
still trigger the existing secret treatment. Numeric canonicalization, its
bounded expansion and the existing narrow negative-fraction exception remain
unchanged across both CSV paths.

Keep the shared raw content classifier, conservative `infer_sensitive_from_name`,
strict generated-row privacy, masking and local-category validation unchanged.
Tokenized semantic hints are not permission to disclose a field whose old
privacy guard considers sensitive. No row, matched spelling or secret is added
to diagnostics, exceptions, profiles, caches or provider inputs.

## Determinism And Cache Compatibility

Counters and fixed conflict rules make semantic/type/sensitivity decisions
independent of row order. This does not promise full profile byte equality:
existing numeric reservoirs, bounded category samples, tied pattern ordering
and synthetic-category label order are outside this semantic policy change.
Generation remains reproducible for a corrected specification and explicit seed.

Folder cache format 7 invalidates version 6 and earlier entries. Reprofiling
recomputes changed semantic/type metadata under existing input/work budgets;
saved profile and plan files are not migrated in place. Profile fingerprints
can intentionally change. Historical OpenSpec and benchmark JSON/Markdown
evidence is immutable.

## Verification

Completed checks cover false positives from numeric role names and substrings,
exact threshold boundaries, rare/mixed content, late evidence, compatible and
conflicting names, nulls, row permutations and corrected seeded generation.
Privacy suppression, strict detector equivalence, category guards, both
distinct-count backends and old-cache invalidation checks pass. Executed gates
and independent review evidence are in [validation.md](validation.md).
