# Project Context

## Purpose

Agent Paranoid Android generates safe, deterministic synthetic test datasets
from CSV files and safe database profile metadata. The project is safety-first:
generated data must be synthetic, reproducible by seed, and reviewable through
explicit artifacts.

## MVP Boundary

The MVP SHALL support:

- profiling CSV files and CSV folders into safe metadata;
- inferring a reviewable `DatasetSpec`;
- generating deterministic synthetic CSV, JSON, or Parquet outputs;
- validating generated datasets against schema, relationship, privacy, and
  constraint expectations;
- exposing MCP workflows that return metadata and reports, not dataset rows.

The MVP SHALL NOT require:

- unrestricted SQL execution;
- copying or transforming source rows into output rows;
- free-form LLM reasoning as the only validation mechanism;
- broad workflow automation beyond explicit profile, infer, generate, validate,
  and export steps.

## Safety Principles

- Treat possible PII as sensitive by default.
- Prefer schema metadata, aggregates, distributions, ranges, and masked patterns
  over raw samples.
- Keep Trino access read-only, allowlisted, and bounded.
- Keep deterministic generation separate from I/O and agent orchestration.
- Record generation inputs, seed, output format, row counts, validation status,
  and provenance in artifacts.

## Change Policy

Use `openspec/changes/<change-id>/` for larger behavior changes before coding.
Small documentation, test, and bug-fix changes may update `openspec/specs/`
directly when they only clarify current behavior.
