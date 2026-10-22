# Roadmap

This roadmap describes intended product direction, not committed dates. Work is
prioritized from observed user needs and confirmed defects.

## Now

- Process external stable `1.6.0` feedback through the
  [OpenSpec work plan](https://github.com/wa-pis/agent-paranoid-android/tree/main/openspec/changes/external-feedback-1-6):
  reviewed numeric CSV profiling, authenticated Trino access, relational planning
  and utility evidence, bounded statistics and actionable CLI diagnostics.
  Preserve conservative privacy defaults and read-only database budgets. Start
  with reproduced failures; do not reopen corrected historical harness findings.

- Enforce the complete [source/output matrix](reference/source-output-matrix.md):
  one reviewed DatasetSpec, all field types/options and business rules across
  sources and formats. Track implementation and evidence in OpenSpec
  `source-output-contract-parity`.

- Prepare the owner-authorized stable `1.6.0` promotion of the accepted
  `1.6.0rc5` runtime, including the accepted changes since `1.5.0`. Complete fresh
  exact-source release gates and public verification before recommending stable
  `1.6.0`; see [stable status](1.6.0-release-status.md).

- Monitor `1.6.0rc5` feedback for the shared source/output contract, portable
  business rules and MCP permissions. The frozen runtime passed exact-main
  automated gates and actual Codex full-current-specification human acceptance;
  publication workflows and public verification passed.
  See [RC5 status](rc5-release-status.md).

- Monitor migration feedback for stable `1.5.0`; do not assume future integration
  feedback or claim unavailable private-data acceptance.
- Continue the separately gated transformation/session acceptance campaign:
  saved behavior profiles, bounded one-to-one mappings, local approval boundaries
  and fictional acceptance. Published RC evidence remains historical; the RC5
  synthetic-client check does not close this campaign or issue preservation
  authority. Changed activation needs its own safety clearance and release gates.
  Stable authorization does not close this campaign or expand preservation rights.
- Run product-validation pilots against real development and analytics tasks.
- Fix onboarding friction reported by external users.
- Address confirmed client defects and routine dependency maintenance.

## Next

- Plan batch-based dataset validation so CSV, JSON and Parquet rows do not all
  remain in memory. Design bounded cross-table key and uniqueness checks,
  preserve deterministic results and existing validation contracts, and measure
  peak memory on synthetic scale fixtures. Create a separate OpenSpec change
  before implementation. This future feature does not replace current resource
  limits or expand the `1.6.0rc1` scope; confirmed safety defects still block RC.

- Simplify CSV and database workflows using pilot feedback.
- Publish runnable real-world examples and short case studies built from
  synthetic fixtures.
- Improve diagnostics and documentation where users repeatedly need help.

## Later

- Add integrations only after demonstrated demand.
- Consider optional reporting and validation adapters when concrete workflows
  justify them.
- Evolve public contracts through the documented compatibility and deprecation
  policy.

Completed implementation history belongs in the
[changelog](https://github.com/wa-pis/agent-paranoid-android/blob/main/CHANGELOG.md),
[release evidence](release-evidence.md), and the
[OpenSpec archive](openspec-archive.md).
