# Domain-Agnostic Refactoring Plan

This plan captures the current architecture review and the migration path toward
a domain-agnostic `DatasetSpec` architecture.

## 1. Repository Overview

The repository currently has two architectures living side by side.

The legacy single-table path uses:

- `src/test_data_agent/spec.py`
- `src/test_data_agent/generator.py`
- `src/test_data_agent/validator.py`
- `src/test_data_agent/csv_profiler.py`

It is centered on `GenerationSpec`, `TableSpec`, `ColumnSpec`, and
`MultiTableGenerationSpec`.

The newer domain-agnostic path uses:

- `src/test_data_agent/core/`
- `src/test_data_agent/profiling/`
- `src/test_data_agent/generation/`
- `src/test_data_agent/validation/`

It is centered on `DatasetProfile` and `DatasetSpec`, with entities, fields,
relationships, and constraints.

The CLI currently bridges both worlds. JSON specs and single-table CSV flows use
the legacy path, while YAML specs and example-folder flows use `DatasetSpec`.

## 2. Current Problems

### DatasetSpec Is Too Thin

`DatasetSpec` currently contains only:

- `entities`
- `relationships`
- `constraints`

It does not explicitly model:

- distributions
- aggregate rules
- privacy rules
- generation settings
- validation settings

### Domain Concepts Are Split

The legacy rule layer uses `table` terminology, while the newer core uses
`entity`. This creates a persistent leak of table-shaped assumptions into the
domain-agnostic engine.

### Distribution Modeling Is Untyped

`FieldProfile.distribution` and `FieldSpec.distribution` are raw dictionaries.
Generation dispatches on string keys such as `kind`, which makes validation,
migration, and plugin behavior brittle.

### Privacy Rules Are Scattered

Sensitive-field detection, masking, safe enum handling, CSV privacy behavior,
and Trino SQL safety are spread across multiple modules. There is no central
privacy policy boundary.

### CSV Input Has Two Profilers

Single-file CSV profiling returns `CSVProfile`, while CSV-folder profiling
returns `DatasetProfile`. They duplicate type inference, semantic detection,
masking, and numeric statistics.

### Business Logic Is Coupled To Core Generation

The new constraint solver imports condition and expression helpers from the old
business-rule validator. The core engine should not depend on business-specific
YAML rule implementation details.

### Source Adapters Are Not First-Class

CSV folders, single CSV files, Trino profiles, JSON profiles, and Parquet data
are handled in command-specific paths. The target architecture requires every
input source to normalize into a common `DatasetSpec`.

### Safety Boundary Around Row Samples Is Implicit

The CSV-folder profiler uses bounded raw rows for relationship and constraint
mining. This is acceptable as temporary in-memory profiling data, but it should
be represented as an explicit sensitive sample boundary that cannot be cached or
exported.

### CLI Owns Too Much Orchestration

`cli.py` currently parses arguments, profiles inputs, infers specs, generates
data, validates data, writes outputs, and writes artifacts. This makes it hard
to test the application workflow independently from command-line behavior.

### Migration Tests Are Missing

Existing tests cover legacy and newer paths separately, but there are no strong
contract tests proving that all source inputs normalize into equivalent
`DatasetSpec` shapes.

## 3. Proposed Target Module Structure

```text
src/test_data_agent/
  core/
    dataset.py
    entity.py
    field.py
    relationship.py
    constraint.py
    distribution.py
    privacy.py
    settings.py

  adapters/
    __init__.py
    csv_file.py
    csv_folder.py
    trino_profile.py
    json_profile.py
    parquet_dataset.py
    legacy_generation.py

  profiling/
    schema.py
    distributions.py
    relationships.py
    constraints.py
    sampling.py
    cache.py

  generation/
    engine.py
    fields.py
    constraints.py
    invalid_cases.py

  validation/
    engine.py
    schema.py
    relationships.py
    constraints.py
    privacy.py

  rules/
    expressions.py
    conditions.py
    business_config.py
    scenarios.py

  io/
    readers.py
    writers.py
    artifacts.py

  cli.py
  mcp_trino_server.py
```

The important architectural rule: every supported input source should become a
`DatasetProfile` or `DatasetSpec` before generation and validation.

## 4. Refactoring Phases

### Phase 0: Preserve The Plan And Automation

Add the plan file and local automation script. This phase should not alter
runtime behavior.

Expected files:

- `docs/domain_agnostic_refactoring_plan.md`
- `scripts/domain_agnostic_refactor.py`

### Phase 1: Stabilize The DatasetSpec Contract

Add explicit core models for:

- typed distributions
- privacy rules
- generation settings
- validation settings

Extend `DatasetSpec` with defaulted fields so existing specs remain compatible.

Expected files:

- `src/test_data_agent/core/distribution.py`
- `src/test_data_agent/core/privacy.py`
- `src/test_data_agent/core/settings.py`

### Phase 2: Centralize Privacy And Masking

Move shared PII detection, masking, and safe distribution exposure rules into a
single privacy module. CSV, CSV-folder, Trino, generation, and validation code
should use that module.

Expected outcome:

- no duplicated sensitive-name logic
- sensitive columns never emit raw top values
- rare free-text values are suppressed or converted to safe patterns
- profile caches remain metadata-only

### Phase 3: Introduce Source Adapters

Create adapters that convert inputs into `DatasetProfile` or `DatasetSpec`:

- CSV file
- CSV folder
- Trino safe profile
- JSON profile/spec
- Parquet dataset
- legacy `GenerationSpec`

Expected package:

- `src/test_data_agent/adapters/`

### Phase 4: Migrate CSV Flows To DatasetSpec

Update `profile-csv` and `generate-from-csv` so they use the same one-entity
`DatasetSpec` path as the multi-table CSV-folder flow.

Compatibility rule:

- existing CLI commands should continue to work during the migration.

### Phase 5: Decouple Business Rules From Core Engine

Move safe expression evaluation and conditions into a neutral `rules/` package.
Convert business YAML into `DatasetSpec` constraints and settings before
generation.

Expected outcome:

- generation and validation no longer import from `business_validator.py`
- business-specific behavior lives in config, specs, examples, or plugins

### Phase 6: Thin The CLI

Move workflow orchestration, readers, writers, and artifact writing out of the
CLI.

Expected packages:

- `src/test_data_agent/io/`
- application-level orchestration helpers, if needed

### Phase 7: Deprecate Legacy Spec Path

Keep the legacy spec path through an adapter while tests and docs migrate. Then
remove old modules only after compatibility tests prove the new path is stable.

Candidate modules to delete later:

- `src/test_data_agent/spec.py`
- `src/test_data_agent/generator.py`
- `src/test_data_agent/validator.py`
- `src/test_data_agent/csv_profiler.py`
- `src/test_data_agent/business_rules.py`
- `src/test_data_agent/business_validator.py`
- `src/test_data_agent/rules_engine.py`

### Phase 8: Isolate Deprecated Compatibility Surface

Keep deprecated `GenerationSpec` behavior available through an explicit
`compat/` package so CLI and external callers have a narrow boundary while the
domain-oriented packages stay focused on `DatasetSpec`.

Expected files:

- `src/test_data_agent/compat/__init__.py`
- `src/test_data_agent/compat/legacy_generation.py`
- `src/test_data_agent/compat/legacy_workflows.py`

### Phase 9: Tighten Dataset Adapter Exports

Keep the dataset-oriented `adapters/` package focused on source normalization.
Deprecated `GenerationSpec` conversion helpers should stay importable from
`adapters.legacy_generation` and `compat/`, but not from the adapter package
root.

Expected outcome:

- `test_data_agent.adapters` exports only dataset/profile normalization helpers
- deprecated `GenerationSpec` conversions live behind explicit legacy modules

### Phase 10: Detach Legacy Workflow Warnings

Keep deprecated `GenerationSpec` warnings inside legacy workflow modules
instead of dataset-oriented workflow helpers.

Expected outcome:

- dataset-oriented workflow helpers contain no deprecated warning logic
- legacy workflow warnings remain available only through explicit legacy modules

### Phase 11: Move Legacy Workflow Implementation To Compat

Keep deprecated `GenerationSpec` workflow implementation inside `compat/`
modules while `io/legacy_workflows.py` becomes a thin compatibility shim.

Expected outcome:

- `test_data_agent.compat.legacy_workflows` owns deprecated workflow behavior
- `test_data_agent.io.legacy_workflows` only re-exports that behavior
- dataset-oriented `io/` modules stay focused on `DatasetSpec` workflows

### Phase 12: Narrow Compat Workflow Imports

Keep deprecated workflow callers pointed at the dedicated
`compat/legacy_workflows.py` module instead of the broad `compat` package root.

Expected outcome:

- `cli.py` imports deprecated workflow helpers from `test_data_agent.compat.legacy_workflows`
- the `compat` package root remains a user-facing compatibility surface, not an internal workflow dependency

### Phase 13: Route Package-Root Legacy Shims Through Compat

Keep deprecated package-root symbols behind explicit `compat/` modules instead
of importing legacy implementation modules directly from `test_data_agent`.

Expected outcome:

- `test_data_agent.__init__` resolves deprecated `GenerationSpec` and row APIs
  through `test_data_agent.compat.legacy_spec`
- callers retain compatibility, but the package root no longer reaches directly
  into legacy implementation modules

### Phase 14: Move Business Rule Models Into Rules Package

Keep the neutral rule models and loaders inside `rules/` while
`business_rules.py` remains a deprecated compatibility shim.

Expected outcome:

- `test_data_agent.rules` owns business rule models and YAML parsing
- neutral rules modules no longer import `test_data_agent.business_rules`
- `test_data_agent.business_rules` remains importable for compatibility only

### Phase 15: Move Business Rule Application Into Rules Package

Keep business rule application inside `rules/` while `rules_engine.py` remains
only a deprecated compatibility shim.

Expected outcome:

- `test_data_agent.rules.engine` owns business rule application and invalid-case
  injection
- neutral rule helpers no longer import `test_data_agent.rules_engine`
- `test_data_agent.rules_engine` remains importable for compatibility only

### Phase 16: Extract Dataset Command Helpers From CLI

Keep dataset-oriented command detection and spec-path orchestration in `io/`
helpers so `cli.py` focuses on argument parsing and top-level command routing.

Expected outcome:

- dataset-spec path detection lives outside `cli.py`
- dataset-spec generate/validate orchestration is reusable without the CLI module
- legacy compatibility flows remain unchanged

### Phase 17: Extract Example-Dataset Commands From CLI

Keep example-folder profiling and review-bundle generation inside `io/`
command helpers so `cli.py` no longer orchestrates DatasetSpec example flows
directly.

Expected outcome:

- `profile-example` delegates to dataset-oriented command helpers
- `generate-from-example` delegates to dataset-oriented command helpers
- `cli.py` no longer imports example-folder profiling or DatasetSpec review orchestration directly

### Phase 18: Extract Single-Input Profiling Commands From CLI

Keep single-input profiling and spec-inference command orchestration inside
`io/` helpers so `cli.py` routes `profile-csv` and `infer-spec` without
inspecting profile payloads directly.

Expected outcome:

- `profile-csv` delegates to dataset-oriented command helpers
- `infer-spec` delegates to dataset-oriented command helpers
- `cli.py` no longer imports profile/spec loaders for these dataset-oriented commands

## 5. Files To Create, Modify, Or Delete

### Create

- `src/test_data_agent/core/distribution.py`
- `src/test_data_agent/core/privacy.py`
- `src/test_data_agent/core/settings.py`
- `src/test_data_agent/adapters/__init__.py`
- `src/test_data_agent/adapters/csv_file.py`
- `src/test_data_agent/adapters/csv_folder.py`
- `src/test_data_agent/adapters/trino_profile.py`
- `src/test_data_agent/adapters/json_profile.py`
- `src/test_data_agent/adapters/parquet_dataset.py`
- `src/test_data_agent/adapters/legacy_generation.py`
- `src/test_data_agent/rules/expressions.py`
- `src/test_data_agent/rules/conditions.py`
- `src/test_data_agent/rules/models.py`
- `src/test_data_agent/rules/engine.py`
- `src/test_data_agent/io/readers.py`
- `src/test_data_agent/io/writers.py`
- `src/test_data_agent/io/artifacts.py`

### Modify

- `src/test_data_agent/core/dataset.py`
- `src/test_data_agent/core/field.py`
- `src/test_data_agent/core/constraint.py`
- `src/test_data_agent/profiling/schema_profiler.py`
- `src/test_data_agent/profiling/distribution_profiler.py`
- `src/test_data_agent/profiling/constraint_miner.py`
- `src/test_data_agent/generation/entity_generator.py`
- `src/test_data_agent/generation/constraint_solver.py`
- `src/test_data_agent/validation/constraint_validator.py`
- `src/test_data_agent/csv_profiler.py`
- `src/test_data_agent/spec.py`
- `src/test_data_agent/generator.py`
- `src/test_data_agent/business_rules.py`
- `src/test_data_agent/business_validator.py`
- `src/test_data_agent/rules_engine.py`
- `src/test_data_agent/mcp_trino_server.py`
- `src/test_data_agent/cli.py`
- `README.md`
- `docs/dataset_profile_and_spec.md`
- `docs/domain_agnostic_workflow.md`
- tests under `tests/`

### Delete Later

Only delete legacy modules after compatibility adapters and tests are in place.

## 6. Test Plan

Add or update tests for:

- `DatasetSpec` model shape
- typed distribution validation
- privacy-rule defaults
- CSV file to `DatasetSpec`
- CSV folder to `DatasetSpec`
- Trino profile JSON to `DatasetSpec`
- JSON profile/spec loading
- Parquet dataset to `DatasetSpec`
- legacy `GenerationSpec` compatibility adapter
- deterministic generation by seed
- relationship preservation
- aggregate mapping validation
- business config conversion to constraints
- controlled invalid generation
- PII masking and no raw sensitive values in profiles/caches
- unsafe SQL rejection
- CLI compatibility during migration

## 7. Automation Commands To Run

General test suite:

```bash
python3 -m pytest
```

Focused suites:

```bash
python3 -m pytest tests/test_domain_agnostic_pipeline.py
python3 -m pytest tests/test_csv_profiler.py tests/test_generator.py
python3 -m pytest tests/test_mcp_trino_server.py
```

Refactoring automation:

```bash
python3 scripts/domain_agnostic_refactor.py plan
python3 scripts/domain_agnostic_refactor.py check
python3 scripts/domain_agnostic_refactor.py next
python3 scripts/domain_agnostic_refactor.py test --phase phase0
```

Use strict checks in CI or before committing:

```bash
python3 scripts/domain_agnostic_refactor.py check --strict
```

## 8. First Safe Implementation Step

The first safe implementation step is Phase 1:

1. Create `core/distribution.py`, `core/privacy.py`, and `core/settings.py`.
2. Extend `DatasetSpec` with defaulted `privacy_rules`,
   `generation_settings`, and `validation_settings`.
3. Keep existing CLI behavior unchanged.
4. Add model-level tests proving existing specs still load.
5. Run the full test suite.

This creates the target contract without forcing the rest of the codebase to
migrate in the same commit.
