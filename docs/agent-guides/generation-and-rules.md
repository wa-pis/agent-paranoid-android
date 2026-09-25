# Generation, validation, and business-rules guide

Read this guide for generation models, validators, foreign keys, formulas,
scenarios, invalid cases, or cross-table behavior.

Represent business logic as structured YAML or JSON and give it executable
semantics. The LLM may draft or infer a rule, but deterministic code must
enforce and validate it.

Supported rule categories include:

- field and row rules;
- cross-table and foreign-key rules;
- conditional and temporal-ordering rules;
- formula and aggregate-formula rules; and
- scenario-distribution rules.

The generator must:

- produce records satisfying requested rules;
- preserve referential integrity when requested;
- generate invalid records only when explicitly requested;
- label or report controlled invalid cases;
- validate every rule after generation; and
- produce a business-validation report.

Reviewed DatasetSpec `1.1` can generate exact `decimal_range` fields with
precision at most 38 and explicit base-ten bounds. This source-free path uses
integer units and exports Parquet `decimal128`, never binary FLOAT. It does not
make automatic profiling or formulas exact: active constraints on entities
containing DECIMAL currently fail closed pending a separately tested formula
rounding contract. Sensitive DECIMAL ranges remain disallowed.

After constraint solving, valid-mode generation also performs unconditional
schema/type and recognizable-PII checks before returning rows to any export or
publication adapter. These safety checks are not disabled by validation-report
settings. Controlled negative generation may violate schema rules by design,
but it must still pass the privacy check.

Important rules must be represented by typed models and executable validators,
not only by free-form LLM reasoning. Keep generation deterministic with an
explicit local seeded random source. Do not introduce source-row reuse,
identity preservation, or implicit real-value dictionaries as a shortcut.
Entity names reserved for generated control artifacts are rejected by the
dataset specification and writer before any output file is created.

Review-first plans warn when date/time ranges lack endpoints: default generation
uses 2020-01-01 for a missing minimum and 2025-01-01 for a missing maximum.
These are fallback assumptions, not observed source bounds or measured fidelity.
Set explicit bounds in the reviewed specification when a particular period is
required. This warning does not change generation or certify source-period utility.

Repeated identifier fields inferred from CSV profiles use a fixed synthetic key
pool: four distinct source keys yield four synthetic keys even when output grows.
Only the count is carried forward, never source identifiers or row mappings.
The typed `synthetic_identifier` distribution accepts positive integer `pool_size`;
without it, identifiers retain their existing per-row generation behavior.
Pools cycle deterministically and unrelated identifier domains remain disjoint.
Fewer output rows or nulls can leave some pool members unused. Source frequencies
are not reproduced, and declared relationship constraints still take precedence.
Repeated-key pools are not nominated as primary keys; an explicit primary key
cannot have a pool smaller than its requested row count.
Folder overflow and censored single-CSV counts cannot infer a fixed pool.
Other aggregate profiles may supply approximate counts: these define the requested
synthetic pool, not proof of exact source cardinality. Reprofile older artifacts
to obtain pool metadata; no source-preservation permission is implied.
