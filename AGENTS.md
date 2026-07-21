# Agent Paranoid Android Project Instructions

You are working on a safe synthetic test data generation agent.

The project goal is to build an agent that can:

* inspect Trino-accessible database schemas through MCP
* profile source tables safely
* detect sensitive fields
* build generation specifications
* generate synthetic test data
* validate generated datasets
* export data as CSV, JSON, SQL, or Parquet

Core safety rules:

* Never copy production rows into generated output.
* Never expose raw PII.
* Never create tools that allow arbitrary unrestricted SQL.
* Trino access must be read-only.
* Prefer schema metadata, aggregates, distributions, and masked samples over raw rows.
* Treat possible PII as sensitive by default.
* Generated data must be synthetic and reproducible via seed.

Allowed database operations:

* list catalogs
* list schemas
* list tables
* describe table
* profile table
* profile column
* run safe read-only SELECT queries with LIMIT
* return masked samples only when needed

Forbidden database operations:

* INSERT
* UPDATE
* DELETE
* MERGE
* DROP
* TRUNCATE
* ALTER
* CREATE
* GRANT
* REVOKE
* unrestricted SELECT *
* exporting real production rows
* reading secrets, credentials, tokens, or raw PII

Implementation preference:

* Use Python.
* Use Pydantic for generation specs and validation models.
* Use Faker for synthetic values.
* Use deterministic random generation with an explicit seed.
* Keep the LLM/agent layer responsible for planning and spec creation.
* Keep actual data generation deterministic and testable.
* Keep Trino MCP tools small, explicit, and safe.

Python implementation guidelines:

* Target Python 3.11+ and use modern type hints.
* Prefer dataclasses or Pydantic models for structured data instead of untyped dictionaries at module boundaries.
* Keep pure deterministic logic separate from I/O, MCP, filesystem, and CLI wrappers.
* Use `pathlib.Path` for filesystem paths.
* Avoid global mutable state; pass seeds, configs, and dependencies explicitly.
* Keep random generation local to a seeded `random.Random` instance.
* Raise specific exceptions for safety violations and validation failures.
* Do not swallow exceptions silently; convert them to clear CLI errors only at the CLI boundary.
* Keep imports explicit and avoid wildcard imports.
* Add dependencies only when they materially simplify safe, testable behavior.

Expected modules:

* mcp_trino_server.py: MCP tools for safe Trino metadata/profiling
* spec.py: Pydantic models for generation specifications
* generator.py: deterministic synthetic data generation
* validator.py: dataset validation
* cli.py: local command-line interface

Testing expectations:

* Add unit tests for generator behavior.
* Add tests for PII masking decisions.
* Add tests that unsafe SQL is rejected.
* Add tests that generated datasets match requested schema.
* Do not require real Trino access for normal unit tests; mock Trino responses.

When implementing:

* Make the smallest working version first.
* Prefer clear code over clever abstractions.
* Add comments only where they clarify safety decisions.
* Do not add heavy dependencies unless necessary.
* Update README with usage examples after adding functionality.

Git workflow:

* Make regular commits at coherent checkpoints instead of one large end-of-session commit.
* Keep each commit focused on a single logical change.
* Use clear conventional commit messages, for example `feat: add csv profiling` or `docs: explain usage`.
* Before committing, run the relevant tests or document why they were not run.
* Do not include unrelated worktree changes in a commit.

## CSV Input Support

The agent may use CSV files as a source of schema and profiling information.

CSV files must be treated as potentially sensitive. The agent must not copy source rows directly into generated output.

Allowed CSV-derived information:

* column names
* inferred data types
* null ratios
* approximate distinct counts
* enum-like value distributions for non-sensitive fields
* numeric min/max/percentiles
* date/time ranges
* string length distributions
* masked patterns
* safe synthetic examples

Forbidden CSV-derived behavior:

* copying source rows
* exposing raw PII
* using real emails, names, phones, addresses, IDs, tokens, or secrets
* generating output by shuffling or duplicating input rows
* preserving unique sensitive identifiers
* leaking rare free-text values

CSV profiling requirements:

* detect delimiter
* detect encoding where practical
* detect header
* infer column types
* detect likely PII
* mask sensitive examples
* create a reusable profile JSON
* build generation specifications from the profile

For CSV input, the preferred flow is:

1. profile-csv
2. infer generation spec
3. generate synthetic data
4. validate generated data
5. export output


## Business Logic Support

The agent must support scenario-based synthetic data generation with explicit business rules.

Business logic must be represented as structured configuration, preferably YAML or JSON. The LLM may help infer or draft rules, but deterministic code must enforce and validate them.

Supported rule categories:

* field rules
* row rules
* cross-table rules
* conditional rules
* temporal ordering rules
* formula rules
* foreign-key rules
* aggregate formula rules
* scenario distribution rules

The generator must:

* generate valid records that satisfy business rules
* generate controlled invalid records only when requested
* label or report invalid cases clearly
* preserve referential integrity where requested
* validate every rule after generation
* produce a business validation report

The agent must not rely on free-form LLM reasoning as the only validation mechanism. All important rules must be executable and testable.
