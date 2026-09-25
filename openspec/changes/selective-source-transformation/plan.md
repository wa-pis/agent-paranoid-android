# Proposed Implementation Milestones

Implementation and 1.6.0rc1 publication authorized by the user on 2026-09-24
(Europe/Samara). Use sequential signed PRs and green CI/CD. Independent AI
review applies to the final exact RC SHA and safety-policy changes, not every PR.
Stable publication is not authorized. No production source access is authorized.

The refreshed 2026-09-24 handover is planned in
[client feedback v2](feedback-2026-09-24-v2.md): findings 20–26, strengthened
acceptance for 1–19, dependencies and unresolved decisions. It extends this
change's client/financial/format acceptance work; it does not authorize embedded
repair instructions, live integrations or a weaker safety boundary.

1. **Contract and safety approval.** Separate source-free generation from
   one-to-one transformation; settle field actions, sensitivity review,
   preservation authority, dependencies and typed substitution dictionaries.
   The selected authority is the trusted local CLI operator: interactive
   confirmation of the exact plan and preserved columns, with a receipt bound
   to fixed input bytes. Equal-privilege local impersonation is outside this
   deployment claim. This choice does not activate preservation; the scoped
   safety amendment, executable checks and independent safety review still gate it.
2. **Confirmed client defects.** Reproduce and correct identifier collisions,
   repeated-key misclassification, generator/privacy disagreement and empty
   output directory publication. Report unknown date bounds and capped distinct
   statistics honestly. Do not import every suggested fix uncritically.
   Prioritize reproduction of permitted boolean SQL connectors (22) and
   mode/ratio parity (25); batch doctor diagnostics (20). Track Trino auth (21)
   behind an explicit configuration/secret-source decision.
3. **CSV vertical slice.** One-to-one rows, preserved reference combinations,
   replaced financial values, scoped substitutions, consistent keys and derived
   totals through a saved policy before adding interactive UI.
4. **Review wizard and agent parity.** Present per-field evidence and proposed actions; allow
   edits or bulk acceptance of reviewed decisions and save a replayable policy.
   High cardinality alone is not a semantic rejection reason: enforce resource
   budgets separately and disclose uncertainty rather than invent uniqueness.
   Expose review, policy validation and execution to noninteractive CLI/Python
   and explicitly scoped MCP operations; they may consume a matching local
   operator receipt but cannot create one. Return safe structured summaries,
   not source rows. Agents cannot self-declassify data.
   Before the RC, specify and verify skill-guided agent use: discover both
   packaged skills, distinguish capabilities of the installed version from
   proposed transformation steps, and route to existing reviewed interfaces.
   This is a pending agent-integration task, not permission to execute a skill
   or register it silently with every agent runtime.
5. **PostgreSQL and approved SQL inputs.** Reuse transformation semantics with
   bounded read-only access, fixed-input replay and cross-input mapping domains.
   Complex query support and additional adapters require scoped decisions.
6. **Documentation reconciliation.** Audit the complete documentation surface,
   update affected contracts/examples/help and remove contradictory current
   claims. Preserve historical release records. Document both modes, mapping
   security, residual risk and safe error recovery. Update docs alongside each
   milestone, then perform the full consistency pass here.
7. **Client acceptance and candidate readiness.** Verify a fictional finance
   scenario end-to-end; report safety, constraint conformance and utility
   separately. Complete independent review, executable documentation checks
   and release gates. Candidate publication is authorized only after these gates;
   verify public artifacts and disable the implementation automation on completion.

## Financial Type Follow-up

The user requested exact financial handling: add a reviewed decimal contract
with precision/scale, rounding and overflow rules across profiling, policy,
generation/derivation and export. Avoid float intermediates for exact amounts.
Retain approximate DOUBLE semantics explicitly; do not claim recovered precision.
CSV needs companion type/null/format metadata and round-trip tests for decimals,
large integers, leading-zero strings and timestamps. Review schema compatibility
before implementation. No new Hadoop connector is implicitly requested.
Findings 23/24/26 add precision/scale transport, declared Arrow output schemas,
honest Parquet profiling evidence and typed readback to this same milestone.
Decide invalid-mode heterogeneous Parquet behavior with finding 25 rather than
silently converting whole columns to strings.
