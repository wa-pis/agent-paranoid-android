# Domain-Agnostic Dataset Workflow

This compatibility page retains existing section links. Current instructions
now have a single owner for each task, rather than a second copy of commands.

## Mental Model

Profile safe metadata, review a DatasetSpec, generate new values and validate the result. See [Profiles And Specs](concepts/profiles-and-specs.md).

## Folder Layout

Use one CSV per table. File stems identify entities. See [Related Tables](getting-started/related-tables.md).

## Commands

Follow the reviewed profile/spec/generate/validate flow. Commands live in one canonical reference. See [CLI Workflows](reference/cli-workflows.md).

## Large Inputs And Profile Cache

Profiling and inference are resource-bounded. Cache only safe metadata; use --no-cache when a fresh profile is needed. See [Configuration](reference/configuration.md).

## Large Trino Tables

Keep profiling aggregate-only, allowlisted and bounded. Never download source rows for generation. See [Profile Through Trino](how-to/trino.md).

## What Gets Written

Keep the specification, manifest and validation reports with the generated data. See [Review The Output](getting-started/review-output.md).

## How Relationships Are Preserved

Generated child references use generated parent keys. Review inferred links and ambiguous identifiers. See [Relational Synthesis Contract](concepts/relational-synthesis-contract.md).

## How Constraints Are Preserved

Typed, executable rules enforce formulas, temporal order and cross-table conditions. See [Business Rules](how-to/business-rules.md).

## Safety Notes

Generation uses the specification and seed, never a pool of source rows. Privacy review remains necessary. See [Safety Model](concepts/safety-model.md).
