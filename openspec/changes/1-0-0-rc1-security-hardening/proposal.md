# Change: 1-0-0-rc1-security-hardening

## Summary

Make the safety contract a mandatory property of every supported generation
and Trino access entry point before `1.0.0rc1`. The release candidate must not
rely on a particular CLI, agent, or MCP workflow to perform checks that can be
bypassed through a direct Python call.

This change is the release-candidate hardening plan for the findings recorded
in `docs/security-review-2026-07-31.md`. It is a prerequisite for the RC, not
a new feature release.

## Motivation

The current project has strong safety-oriented infrastructure, but two
release-blocking boundary gaps remain:

- direct generation from a manually constructed or loaded `DatasetSpec` can
  emit raw categorical values without a spec-level privacy gate;
- the low-level Trino `execute_query()` path executes caller-provided SQL
  without the safe-query validator used by the MCP safe-select path.

These gaps contradict the project's core promises that generated output never
exposes raw PII and Trino access remains read-only, allowlisted, and bounded.
They must be fixed and covered by direct API tests before publishing the
release candidate.

## Scope

In scope:

- Add one fail-closed `DatasetSpec` safety boundary shared by Python, CLI, MCP,
  and agent generation paths.
- Remove or privatize unrestricted Trino execution and expose only validated,
  bounded read-only operations to callers.
- Add adversarial tests for direct Python, CLI, and MCP entry points.
- Make declared validation settings and generation locale either executable or
  explicitly remove them from the supported contract.
- Define the reproducibility and manifest evidence required for the RC.
- Close or disposition the remaining privacy, typing, container-version,
  JSON-input, documentation, and OSS-governance findings.
- Update the release gate and RC checklist so the evidence is repeatable from
  published-style artifacts.

Out of scope:

- New generation modes, providers, output formats, or MCP tools.
- Differential privacy, anonymization certification, or a claim of statistical
  protection against re-identification.
- A broad rewrite of the agent or Trino modules beyond the decomposition needed
  to make safety enforcement central and testable.
- Creating an intermediate `0.13.x` release solely for this hardening work.

## Safety Impact

- Raw sensitive values in profiles, specs, generated rows, logs, errors, and
  MCP responses remain forbidden.
- Every generation entry point rejects unsafe specs before generation or file
  publication.
- Every external Trino query is parsed, allowlisted, bounded, and read-only;
  internal aggregate profilers may retain dedicated trusted query builders.
- Existing path, resource, audit, and source-row protections remain in force.
- Privacy detection remains heuristic and must be documented as such; this
  change does not create a privacy certification.

## Compatibility

- Unsafe specs and unsafe SQL previously accepted by low-level APIs will be
  rejected. This is an intentional security fix and may require a migration
  note, but it is not a reason to preserve unsafe behavior.
- Supported CLI and MCP contracts remain stable except for stricter rejection
  of unsafe inputs and clearer error categories.
- `DatasetSpec` and generation manifests may gain optional fields for safety
  evidence and reproducibility. Breaking schema changes require the existing
  versioning and compatibility fixtures.
- Existing valid synthetic workflows, output formats, and deterministic seeds
  must remain compatible.
