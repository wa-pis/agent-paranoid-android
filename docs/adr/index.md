# Architecture Decision Records

Recorded **2026-09-29**. This is a project-wide retrospective register, not a
proposal to rewrite the product and not a claim that 1.6.0rc1 is ready.

The inventory covers the current 16 baseline OpenSpec capabilities, the
cross-cutting architecture/operations contracts and the accepted selective
transformation decisions. It does not attempt to turn every implementation
choice, historical task or unapproved feature suggestion into an ADR.

## Status and authority

- **Accepted — retrospective baseline:** reconstructed from an existing
  documented project contract. No new owner approval or historical decision
  meeting is invented.
- **Accepted — owner decision/target:** explicit owner direction, with its
  recorded date where known. Implementation and public activation may still
  be incomplete or gated.
- **Proposed:** a future choice without sufficient acceptance evidence; not
  implementation authority. Unresolved choices are currently listed in the
  [open-question register](open-questions.md), not disguised as accepted ADRs.
- **Superseded / Rejected:** retain history and link the replacing decision or
  rejection evidence. The initial numbered records are current decisions;
  ADR-0025/0026 identify superseded *earlier prose*, not fictitious prior ADRs.

Each ADR separates context, decision, alternatives/consequences, evidence and
revisit conditions. Alternatives are reconstructed engineering contrasts unless
an authority source explicitly records their consideration; they are not minutes
of a historical vote. Original approval dates are unknown unless stated.

Repository/code/spec links are pinned to baseline commit
[`6370659`](https://github.com/wa-pis/agent-paranoid-android/commit/637065966c12584e11c9b437c1e8b8f8d708c0df) (merged PR #594).
Relative links point to maintained documentation. The current worktree also has
uncommitted private SQL-limit work: its presence does not establish an accepted
implementation, new public interface or release. Test links identify coverage
anchors, **not tests run during ADR collection**.

## How to use this register

1. Before changing a boundary, find its ADR and read its cited contract.
2. If implementation differs from the accepted decision, record the discrepancy;
   do not silently reinterpret the ADR or treat code as permission.
3. If the decision must change, write a new record using the
   [template](template.md), explain the trigger and affected contracts, and obtain
   the existing product/security/release authority. Then mark the old record
   Superseded with reciprocal links.
4. Update executable OpenSpec/reference contracts and tests for behavior changes.
   Plans reference the decision; progress records results and acceptance evidence.
5. Editorial corrections or evidence additions may update the same ADR. Changes
   to meaning must not be hidden as editorial cleanup.

Explicit later owner decisions supersede earlier assistant planning where the
conflict is documented. Baseline safety restrictions remain in force until the
already-required amendment/review/activation gates are satisfied. An ADR is not
an access grant, dataset approval, receipt, GitHub approval or release tag.
For unresolved contradictions, use [the discrepancy register](open-questions.md)
rather than guessing a new product/security policy.

## Decision index

### Foundations and data

| Record | Decision |
| --- | --- |
| [ADR-0001](0001-decision-records.md) | Record decisions separately from specifications and progress |
| [ADR-0002](0002-source-free-generation.md) | Keep synthetic generation source-row-free |
| [ADR-0003](0003-layered-typed-core.md) | Enforce policy below CLI, MCP and provider adapters |
| [ADR-0004](0004-profile-spec-evidence.md) | Separate observations, hypotheses and executable DatasetSpec |
| [ADR-0005](0005-determinism-provenance.md) | Bind reproducibility to the full recorded environment |
| [ADR-0006](0006-bounded-profiling.md) | Profile bounded metadata and preserve uncertainty |
| [ADR-0007](0007-deterministic-rules.md) | Make relationships and business rules executable |
| [ADR-0008](0008-exact-decimal.md) | Keep exact financial types out of binary FLOAT |

### Access and application boundaries

| Record | Decision |
| --- | --- |
| [ADR-0009](0009-database-access.md) | Authorize database access before I/O |
| [ADR-0010](0010-sql-query-sources.md) | Treat approved SQL as a bounded virtual source |
| [ADR-0011](0011-review-first-agent.md) | Use a review-first, recoverable agent state machine |
| [ADR-0012](0012-provider-boundary.md) | Keep providers optional, untrusted and advisory |
| [ADR-0013](0013-interface-parity.md) | Share application policy across CLI, Python and MCP |
| [ADR-0014](0014-filesystem-publication.md) | Validate fixed inputs and publish completed artifacts safely |

### Operations and delivery

| Record | Decision |
| --- | --- |
| [ADR-0015](0015-resource-limits.md) | Make budgets explicit, separate and actionable |
| [ADR-0016](0016-compatibility-packaging.md) | Keep public contracts versioned and integrations optional |
| [ADR-0017](0017-audit.md) | Audit operations without recording their sensitive contents |
| [ADR-0018](0018-container-isolation.md) | Deploy separate least-privilege CLI and MCP images |
| [ADR-0019](0019-release-integrity.md) | Release immutable reviewed commits and verify public artifacts |

### Selective transformation

| Record | Decision |
| --- | --- |
| [ADR-0020](0020-selective-transformation.md) | Separate mixed-origin transformation from synthetic generation |
| [ADR-0021](0021-local-preservation-approval.md) | Require local human approval of exact preservation inputs |
| [ADR-0022](0022-behavior-policies-mappings.md) | Use one strict behavior policy and deterministic mapping semantics |
| [ADR-0023](0023-field-types-null-time.md) | Make matching, nulls and temporal conversion explicit per field |
| [ADR-0024](0024-format-adapters.md) | Use typed input/output adapters around one transformation core |
| [ADR-0025](0025-action-origin-reporting.md) | Report executed cell origins rather than value equality |
| [ADR-0026](0026-transformation-scope.md) | Keep internal formula recomputation out of the 1.6 RC scope |

### Acceptance and documentation

| Record | Decision |
| --- | --- |
| [ADR-0027](0027-acceptance-evidence.md) | Accept complete workflows using fictional, reproducible evidence |
| [ADR-0028](0028-executable-documentation.md) | Keep documentation and release claims tied to supported behavior |

## Coverage of baseline specifications

Coverage is a navigation map, not a declaration that every requirement has passed.

| OpenSpec capability | Governing records |
| --- | --- |
| [synthetic-generation](https://github.com/wa-pis/agent-paranoid-android/blob/637065966c12584e11c9b437c1e8b8f8d708c0df/openspec/specs/synthetic-generation/spec.md) | [ADR-0002](0002-source-free-generation.md), [ADR-0004](0004-profile-spec-evidence.md), [ADR-0005](0005-determinism-provenance.md), [ADR-0007](0007-deterministic-rules.md), [ADR-0008](0008-exact-decimal.md), [ADR-0014](0014-filesystem-publication.md), [ADR-0016](0016-compatibility-packaging.md) |
| [safe-csv-profiling](https://github.com/wa-pis/agent-paranoid-android/blob/637065966c12584e11c9b437c1e8b8f8d708c0df/openspec/specs/safe-csv-profiling/spec.md) | [ADR-0006](0006-bounded-profiling.md), [ADR-0014](0014-filesystem-publication.md), [ADR-0015](0015-resource-limits.md) |
| [dataset-validation](https://github.com/wa-pis/agent-paranoid-android/blob/637065966c12584e11c9b437c1e8b8f8d708c0df/openspec/specs/dataset-validation/spec.md) | [ADR-0002](0002-source-free-generation.md), [ADR-0007](0007-deterministic-rules.md), [ADR-0008](0008-exact-decimal.md), [ADR-0027](0027-acceptance-evidence.md) |
| [agent-orchestration](https://github.com/wa-pis/agent-paranoid-android/blob/637065966c12584e11c9b437c1e8b8f8d708c0df/openspec/specs/agent-orchestration/spec.md) | [ADR-0003](0003-layered-typed-core.md), [ADR-0011](0011-review-first-agent.md), [ADR-0012](0012-provider-boundary.md), [ADR-0013](0013-interface-parity.md) |
| [safe-mcp-workflow](https://github.com/wa-pis/agent-paranoid-android/blob/637065966c12584e11c9b437c1e8b8f8d708c0df/openspec/specs/safe-mcp-workflow/spec.md) | [ADR-0002](0002-source-free-generation.md), [ADR-0009](0009-database-access.md), [ADR-0011](0011-review-first-agent.md), [ADR-0013](0013-interface-parity.md), [ADR-0015](0015-resource-limits.md), [ADR-0017](0017-audit.md) |
| [mcp-interface](https://github.com/wa-pis/agent-paranoid-android/blob/637065966c12584e11c9b437c1e8b8f8d708c0df/openspec/specs/mcp-interface/spec.md) | [ADR-0013](0013-interface-parity.md), [ADR-0016](0016-compatibility-packaging.md) |
| [public-python-api](https://github.com/wa-pis/agent-paranoid-android/blob/637065966c12584e11c9b437c1e8b8f8d708c0df/openspec/specs/public-python-api/spec.md) | [ADR-0003](0003-layered-typed-core.md), [ADR-0016](0016-compatibility-packaging.md) |
| [public-contracts](https://github.com/wa-pis/agent-paranoid-android/blob/637065966c12584e11c9b437c1e8b8f8d708c0df/openspec/specs/public-contracts/spec.md) | [ADR-0004](0004-profile-spec-evidence.md), [ADR-0013](0013-interface-parity.md), [ADR-0016](0016-compatibility-packaging.md) |
| [artifact-contract](https://github.com/wa-pis/agent-paranoid-android/blob/637065966c12584e11c9b437c1e8b8f8d708c0df/openspec/specs/artifact-contract/spec.md) | [ADR-0005](0005-determinism-provenance.md), [ADR-0011](0011-review-first-agent.md), [ADR-0014](0014-filesystem-publication.md), [ADR-0016](0016-compatibility-packaging.md) |
| [database-source-configuration](https://github.com/wa-pis/agent-paranoid-android/blob/637065966c12584e11c9b437c1e8b8f8d708c0df/openspec/specs/database-source-configuration/spec.md) | [ADR-0009](0009-database-access.md), [ADR-0015](0015-resource-limits.md) |
| [database-source-allowlists](https://github.com/wa-pis/agent-paranoid-android/blob/637065966c12584e11c9b437c1e8b8f8d708c0df/openspec/specs/database-source-allowlists/spec.md) | [ADR-0006](0006-bounded-profiling.md), [ADR-0009](0009-database-access.md), [ADR-0010](0010-sql-query-sources.md) |
| [sql-query-source-profiling](https://github.com/wa-pis/agent-paranoid-android/blob/637065966c12584e11c9b437c1e8b8f8d708c0df/openspec/specs/sql-query-source-profiling/spec.md) | [ADR-0009](0009-database-access.md), [ADR-0010](0010-sql-query-sources.md), [ADR-0026](0026-transformation-scope.md) |
| [operational-readiness](https://github.com/wa-pis/agent-paranoid-android/blob/637065966c12584e11c9b437c1e8b8f8d708c0df/openspec/specs/operational-readiness/spec.md) | [ADR-0014](0014-filesystem-publication.md), [ADR-0015](0015-resource-limits.md), [ADR-0016](0016-compatibility-packaging.md), [ADR-0018](0018-container-isolation.md), [ADR-0027](0027-acceptance-evidence.md) |
| [container-deployment](https://github.com/wa-pis/agent-paranoid-android/blob/637065966c12584e11c9b437c1e8b8f8d708c0df/openspec/specs/container-deployment/spec.md) | [ADR-0018](0018-container-isolation.md), [ADR-0019](0019-release-integrity.md) |
| [release-supply-chain](https://github.com/wa-pis/agent-paranoid-android/blob/637065966c12584e11c9b437c1e8b8f8d708c0df/openspec/specs/release-supply-chain/spec.md) | [ADR-0016](0016-compatibility-packaging.md), [ADR-0019](0019-release-integrity.md), [ADR-0027](0027-acceptance-evidence.md) |
| [public-documentation](https://github.com/wa-pis/agent-paranoid-android/blob/637065966c12584e11c9b437c1e8b8f8d708c0df/openspec/specs/public-documentation/spec.md) | [ADR-0001](0001-decision-records.md), [ADR-0028](0028-executable-documentation.md) |

The active [selective-source-transformation change](https://github.com/wa-pis/agent-paranoid-android/blob/637065966c12584e11c9b437c1e8b8f8d708c0df/openspec/changes/selective-source-transformation/plan.md)
is covered by ADR-0008, ADR-0010, ADR-0015 and ADR-0020–0027; its SQL delta also
maps to ADR-0010/0026. Module extraction maps to ADR-0003 and the
[application-boundary inventory](../reference/application-boundaries.md).
Provider integrations map to ADR-0012/0016, not to a new source-data permission.

## Implementation and acceptance snapshot

Owner successor [ADR-0029: unified replacement contract](0029-unified-replacement-contract.md)
permits explicit mapped source-membership/permutations for every field, with
value-free sensitivity notes. Direct preservation and source-free rules remain
unchanged; activation requires new executable evidence and independent review.

- Existing generation/profiling/agent contracts remain separate from transformation.
- PR #594 merged private installed-wheel CSV replacement acceptance at
  **300,000 × 50**. See [immutable evidence](https://github.com/wa-pis/agent-paranoid-android/blob/637065966c12584e11c9b437c1e8b8f8d708c0df/openspec/changes/selective-source-transformation/csv-scale-acceptance.md).
- **1,000,000 × 100**, SQL-result scale, complete twelve-route coverage, public
  transformation execution and final RC acceptance are not proved by that run.
- The provenance decision replaces the earlier user-facing equality report;
  safety comparisons remain. Internal formula recomputation is not required
  for the RC. Do not recreate those old blockers.
- Development automation was paused at the owner's request. Creating these ADRs
  does not resume it or authorize publication. Resume work only on explicit
  direction, using the current progress and diff.

See [open questions and discrepancies](open-questions.md) for the unresolved
choices, superseded prose and implementation gaps. See
[ADR-0001](0001-decision-records.md) for document responsibilities.
