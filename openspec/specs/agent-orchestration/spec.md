# Agent Orchestration Specification

## Purpose

Provide a safe AI-agent-ready orchestration layer that plans synthetic data
generation, requires review before generation, and delegates all deterministic
work to existing profile, spec, generation, validation, and safety code.

## Requirements

### Requirement: Agent Planning Stops Before Generation

The agent orchestration layer SHALL create review artifacts and stop before
writing generated datasets unless an explicit approval step is invoked.

#### Scenario: CSV folder is planned

- **GIVEN** a folder of source CSV files
- **WHEN** `agent-plan` runs
- **THEN** it writes `profile.json`, `dataset_spec.yaml`, `agent_request.json`,
  and `agent_plan.json`
- **AND** it does not write a `generated/` dataset folder

### Requirement: Approval Uses Reviewed DatasetSpec

The approval step SHALL load the prepared workspace and generate from the
reviewed `dataset_spec.yaml`.

#### Scenario: Workspace is approved

- **GIVEN** an agent workspace created by `agent-plan`
- **WHEN** `agent-approve` runs
- **THEN** generation uses the workspace `dataset_spec.yaml`
- **AND** generated artifacts are written under `generated/`
- **AND** `validation_report.json` and `generation_manifest.json` are written

### Requirement: Agent Does Not Return Rows

Agent orchestration SHALL return summaries and artifact paths instead of raw
source rows or generated rows.

#### Scenario: Agent plan or approval completes

- **GIVEN** an agent operation succeeds
- **WHEN** the CLI or API returns a result
- **THEN** the result contains phase, steps, artifact paths, counts, seed, and
  validation status
- **AND** it does not include dataset rows

### Requirement: Source Reuse Checks Remain Deterministic

Approved generation SHALL reuse the existing deterministic source-row safety
checks when source CSV data is available.

#### Scenario: CSV source is approved

- **GIVEN** the agent source is a CSV file or CSV folder
- **WHEN** generated rows are produced
- **THEN** source-row reuse checks run before output is committed
- **AND** the manifest reports `source_rows_copied: false`

### Requirement: LLM Is Planner Only

An LLM client SHALL be treated as a planner and reviewer, not as the generator
or validator.

#### Scenario: LLM client orchestrates the workflow

- **GIVEN** an LLM client is connected to the project
- **WHEN** it needs synthetic data
- **THEN** it may call `agent-plan`, summarize the `DatasetSpec`, request
  approval, and call `agent-approve`
- **AND** deterministic Python code performs generation and validation
