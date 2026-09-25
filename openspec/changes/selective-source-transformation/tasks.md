# Tasks: selective-source-transformation

## Specification

- [x] Record one-to-one rows and explicit reference-field preservation.
- [x] Record financial replacement, zero/rounding equality exceptions and
  declared dependencies.
- [x] Separate the proposed transformation surface from existing generation.
- [x] Define safety approval gates and acceptance scenarios.

## Before Implementation

Internal groundwork (not end-to-end feature acceptance): private action/mapping
models, column coverage/identity checks, strict inline primitives/dates, bounded
CSV snapshots/parsing and integer normalization have landed through PR #528.
The safety amendment and execution approval remain unimplemented. Review
[the boundary draft](safety-boundary.md) before enabling the CSV vertical slice.
The user selected trusted local CLI operator approval; equal-privilege agent
impersonation is outside that deployment boundary. This selects transport, not
approval of any dataset or completion of the safety amendment below.

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

### Refreshed client intake (2026-09-24)

Details, ordering and decisions: [feedback v2](feedback-2026-09-24-v2.md).
All items below remain unverified until reproduced against the current candidate.

- [ ] Inspect new/changed harnesses; record package/version/SHA or wheel hash,
  extras, probe hashes and safe isolated baseline/candidate execution plans.
- [ ] Reproduce/fix 22: allowed AND/OR/nested predicates on both SQL adapters;
  retain forbidden-function, authorization and budget negative controls.
- [ ] Reproduce/fix 25: all generation entrances honor documented explicit/omitted
  mode and ratio precedence; effective spec/manifest/report/exit reflect execution.
- [ ] Reproduce/fix 20: doctor retains failed checks, distinguishes missing extras
  from capability failures and gives safe recovery hints without backend text.
- [ ] Decide 21 auth methods/secret indirection, then implement shared Trino
  propagation, pre-connect requirements, TLS and redaction tests; no live access.
- [ ] Integrate 23 into exact-decimal contract and carry precision/scale through
  profile/spec/generation/formulas/exports without float intermediates.
- [ ] Reproduce/fix 24 with declared Parquet schemas and physical/readback checks;
  settle intentional-invalid mixed-type behavior with 25 before implementation.
- [ ] Reproduce/fix 26 unknown-versus-measured Parquet metadata and bounded
  sensitivity profiling; decide CLI exposure/export compatibility explicitly.
- [ ] Reconcile refreshed 1–19 evidence: missing date bounds, SQL diagnostics and
  scan costs, formula dependencies, publication/overwrite and utility boundaries.
- [ ] Extend candidate matrix to findings 1–26 and section E safeguards; record
  unavailable private/live cases honestly. Full scope and final RC gates unchanged.

### Existing transformation and release requirements

- [ ] Reconcile every client finding against [client acceptance](client-acceptance.md),
  with disposition and executable evidence; do not treat supplied fix prompts
  or monkeypatches as approved implementation instructions.
- [ ] Locally replay reviewed client scripts against isolated baseline and
  installed candidate-branch packages; record per-requirement before/after
  results, disclosed harness adaptations and genuinely unverified private cases.
- [ ] Support inline YAML and local CSV mappings with equivalent validation;
  keep external script/API execution an unapproved future TODO.

- [ ] Implement bounded local CSV transformation with explicit field actions.
- [ ] Make the first CSV replacement primitive unconditional exact-text
  file-wide and per-column lookup tables (`true -> false`, `001 -> 1`) with
  one-pass matching, duplicate-key rejection and no type inference. Resolve
  competing-scope precedence explicitly. Keep preservation/unknown-value gates.
  Add opt-in bounded local dry-run/trace with row, column, scope, rule ordinal and
  status, plus counts, but no literals or value hashes; test trace/execution
  consistency and value-free errors on fictional data.
- [ ] Implement review/validate/execute parity for supported agent interfaces
  with bounded structured responses and no source-row disclosure; only the
  interactive local CLI may mint preservation approval receipts.
- [ ] Add RC acceptance for skill-guided agents: discover both packaged
  `SKILL.md` files through a documented, runtime-neutral path; choose only
  capabilities present in the installed version; propose a safe workflow and
  use existing reviewed CLI/Python/MCP boundaries. Test fictional offline
  routes and unavailable-transformation rejection. Do not auto-register skills,
  add execution authority or mark this complete from packaging alone.
- [ ] Implement separately authorized read-only SQL-result access; preserve
  SQL allowlists and budgets without broadening default profiling/MCP.
- [ ] Implement consistent key mapping and declared derived-value computation.
- [ ] Implement scoped typed substitution dictionaries, unmapped-value policy,
  one-pass semantics, collision checks and restricted local mapping handling.
- [ ] Reject source-value retention disguised as substitution across inline,
  local CSV and shared-domain mappings before approval/execution; cover typed
  identity, null and composite entries with value-free failures.
- [ ] Expose substitution as a specification-level action separate from synthesis;
  test saved wizard-policy parity with noninteractive CLI and Python execution.
- [ ] Expose substitution, mapping references and unmatched-value handling in
  the versioned data behavior profile; test save/load and profile-to-spec
  round trips, conflict rejection and separation from observed evidence.
- [ ] Add a profile-review wizard that saves explicit field decisions; bulk
  acceptance must not bypass unresolved sensitivity conflicts or schema drift.
  - [x] Existing valid-policy sensitivity editor: per-column prompts with system
    comments, no default/bulk answer, unchanged actions/mappings, snapshot drift
    rejection and atomic in-place save; no approval or execution.
  - [x] Add explicit selection/configuration of existing field actions, including
    inline/CSV/domain mappings and unmatched behavior; revalidate new references.
  - [ ] Complete saved-policy parity with executable paths.
- [ ] Add a bounded, value-free system comment for each reviewed field: likely
  data meaning, sensitivity rationale and uncertainty from safe profile
  evidence. Display it with the suggestion and explicit operator decision in
  the wizard and local CLI; never turn default `sensitive=false` into automatic
  preservation. Save and bind the exact reviewed comment/evidence to approval;
  test unknown/conflicting cases, redaction, stale snapshots and save/load
  parity with the noninteractive policy.
- [ ] Validate every final row and declared cross-row relationship before
  atomic publication; reject conflicting policies.
- [ ] Implement the approved “Сохранено исходных значений: X%” transformation
  report indicator: actual unchanged values, explicit comparison scope and
  denominator, typed equality/null/drop/derive/empty-input tests, and safe
  aggregate disclosure. Unavailable is not zero; this is not uniqueness or
  permission to preserve source data.
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
