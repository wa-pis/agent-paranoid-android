# Tasks: selective-source-transformation

## Specification

- [x] Record one-to-one rows and explicit reference-field preservation.
- [x] Record financial replacement, zero/rounding equality exceptions and
  declared dependencies.
- [x] Separate the proposed transformation surface from existing generation.
- [x] Define safety approval gates and acceptance scenarios.

## Before Implementation

See [milestones](plan.md) for the approved order and release scope. Safety-policy
amendments still require scoped review and executable checks before activation.

- [ ] Review the new trust boundary and approve a scoped amendment to
  AGENTS.md, project safety policy and affected baseline specifications.
- [ ] Finalize versioned field policy, CLI/API and mixed-origin artifact schema.
- [ ] Specify exact decimals, precision/scale/rounding/overflow, approximate
  DOUBLE conversion and CSV round trips; preserve existing schema compatibility.
- [ ] Define fixed-snapshot/replay semantics, mapping domains and state cleanup.
- [ ] Define financial tolerances, impossible-replacement behavior and safe
  aggregate disclosure. Keep user decisions above unchanged.

## Implementation And Acceptance

- [ ] Reconcile every client finding against [client acceptance](client-acceptance.md),
  with disposition and executable evidence; do not treat supplied fix prompts
  or monkeypatches as approved implementation instructions.
- [ ] Locally replay reviewed client scripts against isolated baseline and
  installed candidate-branch packages; record per-requirement before/after
  results, disclosed harness adaptations and genuinely unverified private cases.
- [ ] Support inline YAML and local CSV mappings with equivalent validation;
  keep external script/API execution an unapproved future TODO.

- [ ] Implement bounded local CSV transformation with explicit field actions.
- [ ] Implement review/validate/approve/execute parity for supported agent
  interfaces with bounded structured responses and no source-row disclosure.
- [ ] Implement separately authorized read-only SQL-result access; preserve
  SQL allowlists and budgets without broadening default profiling/MCP.
- [ ] Implement consistent key mapping and declared derived-value computation.
- [ ] Implement scoped typed substitution dictionaries, unmapped-value policy,
  one-pass semantics, collision checks and restricted local mapping handling.
- [ ] Expose substitution as a specification-level action separate from synthesis;
  test saved wizard-policy parity with noninteractive CLI and Python execution.
- [ ] Expose substitution, mapping references and unmatched-value handling in
  the versioned data behavior profile; test save/load and profile-to-spec
  round trips, conflict rejection and separation from observed evidence.
- [ ] Add a profile-review wizard that saves explicit field decisions; bulk
  acceptance must not bypass unresolved sensitivity conflicts or schema drift.
- [ ] Validate every final row and declared cross-row relationship before
  atomic publication; reject conflicting policies.
- [ ] Add an end-to-end fictional finance fixture: preserved product/segment/
  bank combinations, replaced amounts, recalculated totals, mapped identifiers.
- [ ] Cover nulls, duplicates, zeros, rounding, composite keys, multiple mapping
  domains, deterministic replay and infeasible constraints.
- [ ] Cover schema drift, sensitivity conflicts, leaks through reports/errors,
  provider isolation, budget exhaustion and output rollback.
- [ ] Prove existing aggregate-only/source-free CLI, Python and MCP contracts
  remain unchanged with executable regression tests.
- [ ] Document user workflow, limitations, residual privacy risk and migration.
- [ ] Audit all repository documentation for consistency: README, quickstarts,
  CLI help/reference, Python/MCP contracts, source adapters, configuration,
  privacy/security, architecture, manifests/reports, troubleshooting, examples,
  roadmap, OpenSpec baselines, changelog and release guidance. Update every
  affected page, preserve historical evidence as historical, and explicitly
  distinguish shipped from planned behavior.
- [ ] Execute documented examples on fictional fixtures and validate links,
  documentation tests and strict documentation build before the candidate.
- [ ] Obtain independent security review and complete the required RC/release
  gates before shipping. Do not mark this proposal implemented beforehand.
