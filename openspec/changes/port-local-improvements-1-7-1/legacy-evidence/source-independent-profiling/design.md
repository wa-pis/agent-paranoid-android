# Design: Source-Independent Profiling

## One Policy, Available Evidence

Shared core policy owns conservative name risk, bounded source-scalar
classification, semantic evidence and safety checks. Source adapters own
authorized I/O and forward the evidence they already obtain. `source_type` is
provenance, never a declassification permission.

| Source path | Available evidence and boundary |
| --- | --- |
| CSV file, byte snapshot and row-digest profiling | Full streamed scalar evidence, bounded distributions and complete distinct counts; no source reopening at handoff |
| CSV folder | Same field policy and exact counting, plus existing bounded relationship/constraint evidence |
| Parquet | File/schema metadata and Arrow physical types only; no row-group read or content-classification claim |
| PostgreSQL / Trino tables | Existing allowlisted aggregate queries and authorized bounded category evidence; no downloaded table rows |
| PostgreSQL / Trino query sources | Validated no-row schema and aggregate wrappers, exact count metadata and projection provenance; no query rows |
| Legacy profile JSON | Supplied aggregates and top-value evidence, normalized under the same safety and weighted semantic rules |
| Typed profile / specification JSON | Typed validation and shared safety gates; explicit reviewed metadata is preserved rather than silently re-inferred |

Missing evidence remains unknown. Shared policy does not imply equal full
profiles or complete content detection from schema/aggregate-only inputs.

## Source Scalars, Semantics And Privacy

`core/privacy.py` separates the original strict string classifier from bounded
source-scalar classification. Source categories and supplied numeric extrema
inspect accepted integer, floating-point and decimal representations using the
existing bounded canonical/retained-float policy. String source guards preserve
strict raw-string recognition as well. Boolean and unsupported composite values
do not become numeric shortcuts; existing local-category scalar/size limits
remain in force.

Any recognized source risk keeps sensitivity and blocks raw category or exact
sensitive-summary publication. It need not establish semantic purpose. Weak SSN,
Luhn, entropy and JWT evidence still requires compatible context and weighted
support over a validated full non-null denominator. Numeric extrema can reveal
risk, but do not prove whole-column semantic support. Adapters forward existing
exact counts rather than reconstructing them from rounded null ratios.

Typed profiles reject unsafe sensitive numeric summaries for every source label.
Legacy normalization suppresses those summaries while retaining safe numeric
shape, masked patterns and synthetic identifiers. A caller cannot override the
fixed `numeric_shape` discriminator with an embedded kind. Explicit reviewed
`DatasetSpec` non-identity numeric scaling keeps its separate existing contract.
Strict generated-row classification and the original raw-value type API are
unchanged by source normalization.

## Names And Query Provenance

Conservative name risk retains all earlier positive decisions and adds complete
words `cc`, `pan`, `passwd` and the phrases `tax_id`, `api_key`, `access_key` and
`private_key`, including supported separator/camel-case spellings. Semantic hints
remain distinct from sensitivity: numeric counters do not become contact fields
merely because their name contains a contact word.

SQL policy `1.1` records sensitive projected outputs when their output name or
any physical input is sensitive. Aliases and supported derived expressions
cannot discard that provenance. Local-category validation rejects such outputs
before the category-value query; exact-sensitive summaries and unsafe temporal
evidence remain suppressed. Existing schemas, AST subset, allowlists, aggregate
query families and resource budgets stay authoritative. The policy version is
part of the source-free query fingerprint.

## Exact CSV Distinct Counting

File, byte-snapshot, row-digest and folder workflows use the shared default
threshold of 1,000,000 tracked fingerprints across fields in a profile/entity.
Small or low-cardinality inputs stay on sets. Above the threshold the existing
DuckDB adapter drains accumulated sets and consumes the same iterator. It
receives only field ordinals and one-time keyed digests, never raw cells or field
names. Native deadlines, private scratch, fixed SQL, disabled external access,
bounded memory/spill and cleanup failures keep their existing enforcement.
The optional `profiling` extra is needed only when this handoff occurs; missing
dependencies fail with fixed installation guidance. There is no new distinct
ceiling and no hard total-process-memory claim.

New completed `CSVColumnProfile` counts explicitly carry
`unique_ratio_kind: exact`; the additive field defaults older payloads to
`unspecified`. Legacy adaptation carries the evidence into `FieldProfile`.
Lower-bound counts cannot nominate primary keys or define fixed identifier
pools. The historical single-CSV 99,999 boundary is treated as censored only for
older non-exact metadata; it does not constrain a new exact count. Approximate
database counts retain their existing meaning as requested synthetic pool
metadata rather than proof of exact source cardinality.

## Cache, Generation And Verification

Folder cache format 9 rejects older entries because the richer name policy can
change sensitive metadata. Saved artifacts remain explicit inputs and are not
silently migrated.

After normalization, all sources feed the same `DatasetSpec` generation,
validation, privacy and output code. Legacy and `tiled-v1` seed namespaces remain
distinct; worker-count determinism remains within the tiled engine. Explicit
eligible CSV bundle streaming can consume a spec from any source, while source
profile, review/approval and MCP routes keep their existing opt-in constraints.
No automatic streaming or source-row access is added for feature parity.

Executed source-matrix, no-row/query-count, privacy, backend equality and
deterministic verification is recorded in [validation.md](validation.md).
The full suite passed 2704 tests with 10 skips; source hashes and aggregate
audit counts are in [verification.json](verification.json). Historical evidence
remains unchanged.
