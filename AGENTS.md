# Agent Paranoid Android project instructions

This repository builds a safe, deterministic synthetic test-data agent. It can
profile schemas and source metadata, infer generation specifications, generate
synthetic datasets, validate them, and export them.

These rules are always active. Task-specific detail lives in the guides below;
read only the guide that matches the files or behavior being changed.

## Non-negotiable safety

- Never copy source rows into generated output or fixtures.
- Never expose raw PII, credentials, tokens, secrets, or production data in
  artifacts, logs, exceptions, tests, or MCP responses.
- All external database access is read-only, allowlisted, and resource-bounded;
  never add arbitrary unrestricted SQL.
- Treat possible PII as sensitive by default. Prefer metadata, aggregates,
  distributions, and masked values over source rows.
- Generated data is synthetic and reproducible when an explicit seed is used.
- Default profiling and generation tools return metadata and summaries. Any
  explicit row-returning capability is a separate opt-in surface and must never
  feed generated output.

Do not weaken these guarantees without executable tests and, for a public
behavior change, a matching OpenSpec/roadmap update.

## Gated selective transformation (not active)

The separate opt-in transformation proposed for 1.6.0rc1 is not synthetic
generation. It may eventually produce a labelled mixed-origin, one-to-one
dataset, but these instructions do not enable that execution path. Existing
generation, profiling, advisors and default MCP remain source-free.

Before any source value may be retained by `preserve` or a preserve fallback, require an
explicit per-field non-sensitive decision, no positive/conflicting sensitivity
evidence, a bounded operator comment, and fresh interactive local-CLI approval
of the exact displayed plan, source bytes, classification and mapping bytes.
Agents and MCP may not create that approval. Sensitive, unknown and disputed
fields remain blocked; DECIMAL preservation remains blocked by default.
No implicit source-row copy is permitted; the explicit replacement exception
below is separate from synthetic generation and transport disclosure.

Owner amendment 2026-10-02 (ADR-0029): explicit `substitute`/`replace_text`
mappings have one contract for every field. A mapped replacement is not
preservation merely because it equals another value in the fixed source,
including a sensitive field. Sensitivity remains a value-free field note,
not a mapping-membership prohibition. This permits explicit mapped permutations,
not implicit copying, source-free generation reuse, `preserve`, secrets in logs,
errors, summaries, providers or MCP responses. Public activation still requires
matching specifications, executable tests and independent exact-SHA safety review.

This proposed exception remains disabled until matching baseline/OpenSpec
amendments, executable end-to-end safety tests, and independent safety review
are complete. A policy declaration or private receipt helper is not execution
authority. Do not route this behavior through source-free generation.

Development and activation are separate gates. Private implementation and
isolated tests using only fictional inputs may be written and exercised before
the final safety review; otherwise end-to-end evidence cannot be produced.
Keep that implementation unavailable through public CLI/Python/MCP execution
surfaces. Test outputs stay in bounded temporary test locations, never user
destinations. This permits no real data access or dataset approval. Passing
end-to-end tests and independent review of the implementation are prerequisites
for activation, not prerequisites for writing the implementation and its tests.

The activation amendment under review is defined in
`openspec/changes/selective-source-transformation/safety-boundary.md`.
Its separate local-file execution contract permits only local controlling-TTY
receipt issuance and matching-receipt consumption by noninteractive/workspace
execution. Private `derive`, database capture and external APIs are not enabled
by that contract. Preserve source-free entrances and disclosure budgets;
enforce complete snapshot totals and identity-limited publication cleanup.
These instructions still do not activate execution: registration must wait for
matching baseline amendments, executable interface evidence and independent
safety review of the exact activation SHA. A review of private code alone does
not satisfy review of the policy amendment or public registration.

The concrete inactive candidate names `transform-approve` as the local-only
issuer, `transform-execute` as the CLI consumer and `execute_transformation`
as the workspace-confined MCP consumer. Execution requires the exact reviewed
snapshot digest; a new review digest does not validate an old receipt after
any bound input changes. Never register an MCP issuer or accept an agent
approval boolean. The unapplied registration patch and isolated installed
acceptance are evidence for review, not permission to enable these entrances.

## Engineering contract

- Target Python 3.11+ and use typed Pydantic or dataclass models at module
  boundaries.
- Keep deterministic generation and validation separate from I/O, MCP,
  provider, filesystem, and CLI adapters.
- The LLM/agent may propose plans, specifications, or hypotheses; deterministic
  code must enforce safety, constraints, relationships, and validation.
- Pass seeds, limits, configurations, and dependencies explicitly. Avoid
  global mutable state and wildcard imports.
- Raise specific exceptions and convert them to user-facing errors only at the
  CLI or transport boundary.
- Prefer the smallest clear change and avoid dependencies that do not simplify
  safe, testable behavior.

## Task-specific guides

- Trino, MCP, SQL policy, masking, or database budgets: read
  `docs/agent-guides/trino-security.md`.
- CSV, Parquet, file profiling, samples, or profile caching: read
  `docs/agent-guides/profiling.md`.
- Generation, validation, foreign keys, formulas, scenarios, or business
  rules: read `docs/agent-guides/generation-and-rules.md`.
- Agent planning, advisors, OpenAI providers, confidence, or relationship
  discovery: read `docs/agent-guides/advisors.md`.
- Architecture or module ownership: use `docs/implementation_map.md` and
  `docs/reference/application-boundaries.md`; do not infer module names from
  this file.
- Architectural decisions: read the relevant record in `docs/adr/index.md`
  and its cited contract. Distinguish accepted decisions, gated implementation
  and open questions; do not reopen an accepted choice through a progress-note
  edit. A changed decision needs an explicit successor ADR and the existing
  approval/test gates. ADRs do not grant data access or activate public behavior.
- Release candidates, versioning, tags, PyPI, or release checks: read
  `CONTRIBUTING.md` and `docs/release.md`.

Do not load all guides for an unrelated task. When a public CLI, MCP, artifact,
or Python API contract changes, update the relevant documentation, OpenSpec,
and focused tests.

## Change and test workflow

- Keep commits focused and do not include unrelated worktree changes.
- Use conventional commit messages and run the smallest relevant checks before
  committing; document checks that could not run.
- Add or update tests for safety, generation, validation, CLI, or provider
  behavior. Normal unit tests must not require live Trino access.
- Use synthetic fixtures only. Never send production data or secrets to an
  external AI provider.
- Larger behavior, security, compatibility, or supply-chain changes require
  an OpenSpec change and should be treated as a release candidate when
  appropriate.
