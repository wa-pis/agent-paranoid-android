# Roadmap

This roadmap describes intended product direction, not committed dates. Work is
prioritized from observed user needs and confirmed defects.

## Now

- Monitor migration feedback for stable `1.5.0`; do not assume future integration
  feedback or claim unavailable private-data acceptance.
- Prepare the isolated `1.6.0rc1` selective-transformation candidate: saved
  behavior profiles, bounded one-to-one mappings, local approval boundaries and
  fictional acceptance. Public activation and publication require independent
  safety clearance and release gates; stable `1.6.0` is not authorized.
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
