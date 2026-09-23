# Proposed Implementation Milestones

Implementation and 1.6.0rc1 publication authorized by the user on 2026-09-24
(Europe/Samara). Use sequential signed PRs, green CI/CD and independent review.
Stable publication is not authorized. No production source access is authorized.

1. **Contract and safety approval.** Separate source-free generation from
   one-to-one transformation; settle field actions, sensitivity review,
   preservation authority, dependencies and typed substitution dictionaries.
2. **Confirmed client defects.** Reproduce and correct identifier collisions,
   repeated-key misclassification, generator/privacy disagreement and empty
   output directory publication. Report unknown date bounds and capped distinct
   statistics honestly. Do not import every suggested fix uncritically.
3. **CSV vertical slice.** One-to-one rows, preserved reference combinations,
   replaced financial values, scoped substitutions, consistent keys and derived
   totals through a saved policy before adding interactive UI.
4. **Review wizard and agent parity.** Present per-field evidence and proposed actions; allow
   edits or bulk acceptance of reviewed decisions and save a replayable policy.
   High cardinality alone is not a semantic rejection reason: enforce resource
   budgets separately and disclose uncertainty rather than invent uniqueness.
   Expose the same review, policy validation, approval and execution flow to
   noninteractive CLI/Python and explicitly scoped MCP operations; return safe
   structured summaries, not source rows. Agents cannot self-declassify data.
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
