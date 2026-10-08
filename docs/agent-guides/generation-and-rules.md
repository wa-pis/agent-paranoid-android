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
Recognizable phone/card-like DECIMAL bounds and final values fail closed even
when optional validation reporting is disabled. Do not treat a declared numeric
type as permission to bypass content checks; ambiguous legitimate amounts may
require a later, separately approved field-scoped policy.

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
String identifiers retain the exact `synthetic_` plus ASCII integer namespace,
including when their field has email, phone or SSN semantics. Identifier generation
takes precedence over semantic formatting. Privacy validation recognizes only that
exact token on identifier fields, not arbitrary prefixed sensitive text; ordinary
non-identifier sensitive fields still use their semantic synthetic formats.
Fewer output rows or nulls can leave some pool members unused. Source frequencies
are not reproduced, and declared relationship constraints still take precedence.
Repeated-key pools are not nominated as primary keys; an explicit primary key
cannot have a pool smaller than its requested row count.
Folder overflow and censored single-CSV counts cannot infer a fixed pool.
Other aggregate profiles may supply approximate counts: these define the requested
synthetic pool, not proof of exact source cardinality. Reprofile older artifacts
to obtain pool metadata; no source-preservation permission is implied.

Batch transformation relationship validation distinguishes logical null from
empty text: only `None` is null, and empty strings participate in scalar foreign
key membership and one-to-one cardinality. The shared relationship validator
keeps its legacy generated-CSV default unless a caller explicitly selects
`empty_string_is_null=False`.

Ordinary formula evaluation enforces fixed per-operation resource caps independently of wall-clock checks: strings and bytes are limited to1,000,000elements; integers and Fraction components to16,384bits; Decimal coefficients, absolute exponents and arithmetic context precision to1,024. Sequence concatenation/repetition checks the prospective size before invoking the operator, including named operands and intermediate results. Built-in numeric arithmetic and bounded string/byte operations remain supported; list/tuple/bytearray and overloaded objects are not formula operands. Rejections contain no operand values. These caps complement dataset/output budgets rather than replacing them.

Common YAML loading rejects recursive aliases before construction. Expanded alias nodes share `TEST_DATA_AGENT_MAX_INPUT_CELLS`; expanded scalar bytes share `TEST_DATA_AGENT_MAX_INPUT_FILE_BYTES`. Ordinary bounded acyclic aliases remain supported. Physical alias/depth ceilings still apply, and errors contain no input values. These checks precede model construction and JSON serialization.

Every `generate_dataset` consumer performs the common output allocation estimate before Faker setup and row creation, including direct Python calls, PostgreSQL SQL export and transformation synthesis. Filesystem capacity checks remain in I/O workflows. String construction checks `TEST_DATA_AGENT_MAX_INPUT_CELL_CHARS` before random-character allocation. These conservative payload estimates and cooperative deadlines do not promise an exact peak-RSS ceiling.


Deterministic native constraints and business rules share an explicit
`GenerationBudget` through generation, solving, business application and
validation. Inner row, field, expression and relationship-graph loops check the
cooperative deadline and charge cumulative work against
`TEST_DATA_AGENT_MAX_BUSINESS_RULE_EVALUATIONS`. Direct Python entry points also
create a bounded budget when none is supplied. Native rule amplification is
estimated before row generation; business rule preflight uses actual supplied
row counts. Mixed/negative FK and aggregate estimates conservatively include
repeated parent/table scans for every possible selected row, even with a small
invalid ratio. Budget failures escape formula error reporting and abort the
workflow before trusted publication. Optional validation report settings do not
disable mandatory post-solve rule checks. Explicit keyword-only budget support
in business callbacks is optional; existing two/three-argument callbacks remain
supported. These operation allowances are conservative cooperative controls,
not CPU-instruction or peak-RSS guarantees.

Generation seeds are bounded before generator setup: persisted DatasetSpec seeds
remain nonnegative and at most 2**63-1; direct Python generation also permits
signed 64-bit negative seeds for compatibility. Oversized seeds fail closed
without truncation or hashing, bounding synthetic identifier width.

Business validation failure details contain rule location and condition only;
conditional allowed-values failures never embed the rejected cell value.
