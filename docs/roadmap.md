# Roadmap

English · [Русский](ru/roadmap.md)

These are directions, not committed dates. The [1.7.1 corrective release](release-evidence-1.7.1.md)
shipped the CLI and MCP inference fixes. Stable [1.7.0](release-evidence-1.7.0.md)
is published and publicly verified. It includes capacity forecasts, bounded
generation for independent and eligible linked tables, CPython 3.15,
configurable inference with evidence, generator MCP Parquet profiling, and
stronger planning and recovery integrity. See the [release history](history.md).

## Now

- Follow up on the remaining external `1.6.0` evidence gaps through the
  [OpenSpec work plan](https://github.com/wa-pis/agent-paranoid-android/tree/main/openspec/changes/external-feedback-1-6):
  historical Trino application authentication settings and external profile
  provenance. The numeric profiling, relational planning/utility, bounded
  statistics and CLI fixes are in 1.7.0. The [RC1 evidence](feedback-acceptance-1.7.0rc1.md)
  records where they were first accepted; its finite installed
  checks do not reproduce missing private inputs or the historical 401.
- Keep transformation evidence scoped to the measured routes and artifact.
  The archived OpenSpec records 36 target-size format combinations, three
  refusal checks and the trust-boundary review; this grants no data permission.
- Improve onboarding from pilot feedback. Versioned guides and four downloadable
  formats are already published; see [documentation versions](versions.md).
- Run product-validation pilots on development and analytics workflows.
- Address confirmed client defects, migration feedback and dependency maintenance.
- Monitor source/output consistency, portable business rules and MCP permissions.

## Next

- Keep the configurable inference matrix green as sources, formats and interfaces
  evolve. OpenSpec `configurable-inference-heuristics` records coverage for equivalent
  safe profiles across Python, CLI and MCP.

- Keep GitHub Pages as the primary documentation host with native mike versions,
  bilingual navigation/search and four verified offline formats. The maintainer
  cancelled the Cloudflare migration on 2026-11-01: it served the same MkDocs site
  rather than adding managed documentation features. Cloudflare publication and
  preview workflows are disabled; successful experiment evidence remains in the
  [operator record](development/cloudflare-pages.md). RTD is superseded and its
  project-build retirement is owner-managed. The GitHub Pages return passed main
  Documentation 41336088977, including public verification and retained versions.
  Cancelled/superseded hosting proposals are archived without accepting their deltas.
- Evaluate support beyond the shipped acyclic linked-table engine. Cycles,
  shared PK/FK identities and global rules are outside its supported scope;
  any extension needs separate bounded planning and review.
- Simplify CSV and database workflows using pilot feedback.
- Publish runnable examples and short case studies using synthetic fixtures.
- Improve diagnostics where users repeatedly need help.

## Later

- Source-row EAV pivot/unpivot remains deferred. Conditional formulas and
  source-free EAV modeling shipped in 1.7.0 (first delivered in rc1); transforming existing
  EAV rows requires a separate proposal for row cardinality, duplicate/null
  semantics, typed values, provenance and explicitly authorized source I/O.
  Neither source-free generation nor one-to-one transformation authorizes it.
- Consider monthly-date category inference and a separately reviewed configurable
  local-category ceiling. Neither is implemented; source-preservation defaults
  remain 20 non-sensitive values of at most 64 characters, with content checks.
- Add integrations only after demonstrated demand.
- Consider reporting and validation adapters for concrete workflows.
- Evolve public contracts through the compatibility and deprecation policy.

The finite fictional transformation/session campaign for stable `1.6.0`
completed with [explicit coverage limits](release-evidence-1.6.0.md).
That grants no dataset permission. Changed public activation still requires
matching specifications, executable evidence and independent exact-source review.
