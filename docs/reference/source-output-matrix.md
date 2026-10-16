# Source and output matrix

Every supported source supplies safe evidence for the same reviewed DatasetSpec.
The source and output format do not select different field, setting or business-rule
languages. Profile what is available, review or author the full specification,
then generate and validate through the common engine.

| Input route | CSV | JSON | Parquet | SQL INSERT bundle |
| --- | --- | --- | --- | --- |
| CSV file → safe profile → reviewed spec | Yes | Yes | Yes | Yes |
| CSV folder → safe relational profile → reviewed spec | Yes | Yes | Yes | Yes |
| Parquet file → safe profile → reviewed spec | Yes | Yes | Yes | Yes |
| Saved JSON DatasetProfile → reviewed spec | Yes | Yes | Yes | Yes |
| Trino aggregate table profile → reviewed spec | Yes | Yes | Yes | Yes |
| PostgreSQL aggregate table profile → reviewed spec | Yes | Yes | Yes | Yes |
| Reviewed PostgreSQL query → aggregate profile → reviewed spec | Yes | Yes | Yes | Yes |
| Reviewed Trino query → aggregate profile → reviewed spec | Yes | Yes | Yes | Yes |
| Reviewed YAML DatasetSpec | Yes | Yes | Yes | Yes |
| Reviewed JSON DatasetSpec | Yes | Yes | Yes | Yes |

These are generation transitions, not source-row conversion. A JSON profile is
metadata, not a raw JSON row dataset. Database acquisition retains configuration,
read-only allowlists and budgets; no output cell authorizes database writes.
Query profiling retains its existing query policy and dependency checks.

## One reviewed contract

All seven field types are available: `integer`, `float`, `decimal`, `boolean`,
`string`, `date`, `datetime`. All accepted DatasetSpec properties pass unchanged
to the common generator: field distributions, nullable/null ratio, semantic and
identifier settings, relationships, constraints, privacy rules/settings, business
rules, generation settings and validation settings. A source adapter must not
remove a reviewed option because of its source type. Output adapters preserve
logical values rather than reassigning formulas or choosing different rules.

The same contract supports `valid`, `edge`, `load_test`, `mixed`, `negative`,
explicit seeds, locale, invalid ratio and load multiplier. Load defaults to ×10;
an explicit count remains exact. Validation toggles control optional reporting;
mandatory privacy, constraints and business checks retain their existing safety
contract. Contradictory specifications, incompatible rules and resource-limit
violations fail consistently before publication.

Profiles contain different evidence. Missing exact DECIMAL bounds, unknown null
statistics or unsupported query dependencies still require an independently
reviewed specification. This does not reduce which field types or options that
specification can use. No source extrema, row identities or source categories
become permission to copy values. DECIMAL retains exact base-ten arithmetic,
precision/scale and the existing sensitivity vetoes.

The regression matrix exercises all ten routes, four outputs and five modes
with all seven field types, native constraints and embedded business rules.
Database fixtures supply fictional metadata and aggregates; these tests do not
claim acceptance against a live database. Separate regressions cover exact
arithmetic, rules, relationships, nullable values, limits and interface contracts.
This is executable coverage of the shared contract, not an exhaustive Cartesian
product of every possible option value or rule combination.

## Output representations and revalidation

Generated bundles retain their reviewed specification and manifest. Use those
artifacts together when revalidating; physical representations differ between
formats, while schema-aware operands retain the same rule semantics. Validation
normalizes operands without modifying the supplied rows.

- **CSV:** the manifest declares `csv_encoding: backslash-null-v1`. `\N` represents
  null; an empty cell remains empty text. A literal leading backslash is doubled.
  Formula-capable strings and headers start with `\F`, keeping them inert in
  spreadsheets and reversible on reload. Only marked bundles use this decoding;
  old unmarked CSV artifacts retain their previous interpretation. Do not remove
  the manifest and expect reversible decoding.
- **JSON:** native scalar values and exact decimal text remain supported.
- **Parquet:** ordinary fields retain native Arrow types, including exact
  `decimal128`. Wide integers that exceed int64 use explicitly marked decimal
  text; mixed timestamp offsets use explicitly marked scalar text. Malformed
  cells in explicitly requested mixed/negative generation use marked JSON scalar
  columns where a native Arrow type cannot represent them. The reader restores
  the logical cells and validation reports the intended violations. Such columns
  are physically strings: consumers reading Parquet directly must inspect
  `apa.scalar_encoding` field metadata or use the bundle reader. Valid generation
  still rejects values incompatible with its declared types.
- **SQL:** the bundle contains quoted, per-entity `INSERT ... VALUES` statements.
  Revalidation decodes only this generated data grammar under input budgets; it
  never executes SQL or connects to a database. Arbitrary SQL, DDL, functions,
  comments and inconsistent table/column declarations are rejected. The separate
  PostgreSQL DDL exporter continues to require valid datasets.

Single-entity profile generation can retain its chosen filename. Its manifest
records `entity_artifacts`, mapping the logical entity to the filename.
Multi-entity profile generation writes a complete folder in any of the four
formats. Neither route discards entities or applies load scaling twice.

See [CLI workflows](cli-workflows.md), [generation modes](generation-modes.md),
and [profiles and specs](../concepts/profiles-and-specs.md).
