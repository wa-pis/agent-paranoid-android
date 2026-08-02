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

Important rules must be represented by typed models and executable validators,
not only by free-form LLM reasoning. Keep generation deterministic with an
explicit local seeded random source. Do not introduce source-row reuse,
identity preservation, or implicit real-value dictionaries as a shortcut.
