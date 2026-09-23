# Behavior Policy Contract — Review Draft

Internal design for implementation; not a supported CLI/API or permission to
execute source-preserving transformations. Existing DatasetProfile/DatasetSpec
schemas and source-free generation remain unchanged.

## Separate Evidence And Decisions

A versioned private behavior policy references a source schema fingerprint and
contains one explicit decision per `(entity, field)`. Profiling observations
remain evidence, not mutable declarations of permission. Duplicate decisions,
unknown fields, missing fields and schema drift fail preflight. Postponed wizard
decisions are incomplete and cannot produce an executable specification.

The shared core parses and validates decisions without reading a source, opening
a mapping file, executing a formula or generating data. CLI, wizard and agent
adapters must use this same core rather than independently interpreting YAML.
Parsing a valid policy is not approval to execute it.

## Action Variants

Use a discriminated union rather than a bag of optional, ignored settings:

| Action | Required configuration | Reject |
| --- | --- | --- |
| preserve | Explicit user authorization and non-sensitive declaration | Mapping, generator or formula settings; unresolved sensitivity conflict |
| synthesize | Reviewed generation policy reference | Preservation or mapping settings |
| substitute | Exactly one inline mapping or local CSV reference; unmatched policy | Generator settings unless unmatched synthesis is explicitly configured |
| derive | Supported formula and declared dependencies | Mapping or preservation settings |
| drop | No execution settings | Mapping, formula or generator settings |

Names here describe semantics; serialized model names/version identifiers remain
subject to independent design review. No wildcard preserve action. Unknown
configuration keys and unknown versions are errors, not silently ignored input.
Sensitive preservation cannot be authorized by an agent. A declaration alone
does not override detected sensitivity or represent privacy certification.

## Private Mapping Representation

Inline mappings are lists of typed source/replacement pairs, not YAML object
keys: object keys can conflate `true`, `1` and strings during parsing. CSV
references name source/replacement columns and use the field's declared type.
Both inputs normalize through one type-aware validator. Duplicate source keys
are rejected, including duplicates with identical replacements; ambiguous
configuration is not resolved by first/last-wins ordering.

Null is distinct from empty string. Exact decimal values are text plus declared
precision/scale; never parse them through binary float. Dates and timestamps are
distinct types; no implicit timezone conversion or timestamp truncation. Actual
CSV null tokens, encoding and timezone policy must be explicit before execution.

Unmatched values default to rejection. Explicit preserve fallback requires the
same permission as preserve action; synthesis fallback requires its own complete
generation policy. Apply the mapping once, never cascade replacement values.
Uniqueness and relationship constraints decide whether an explicitly declared
many-to-one map is compatible; no automatic key-collision repair.

Mapping loaders must reuse bounded local-file/path controls. External scripts,
network URLs and API callbacks are unsupported, not dynamically loadable hooks.
Inline policies and mapping files are restricted inputs. General logging, model
repr, validation exception chains and machine-readable errors must not expose
their contents. Safe summaries contain action counts and opaque references only.
Private save/load must preserve mappings; public summaries must omit entries.

## Validation Layers And Tests

1. Structural parsing: reject unknown versions/actions/keys, conflicting action
   settings, duplicate field decisions and both/neither mapping sources.
2. Schema binding: require every field decision, matching types and exact source
   identity; do not infer authorization from evidence.
3. Semantic preflight: check sensitivity, mapping types/duplicates, null policy,
   dependency cycles, financial precision, declared uniqueness and budgets.
4. Execution approval: bind reviewed policy and fixed source identity; mutation
   invalidates approval. Approval transport and authority need separate review.
5. Post-execution validation: one-to-one rows, source-free fields, permitted
   preserved combinations, formulas and privacy; publish atomically only on pass.

Initial implementation tests should exercise layers 1–2 without file reads or
generation, plus private round-trip and redacted failure behavior. Do not mark
layers 3–5 implemented merely because a policy parses or serializes successfully.
