# Proposed Implementation Milestones

## Owner scope correction — 2026-09-28

The owner clarified that aggregates belong to allowlisted, bounded SQL queries
executed by the database. Transformation consumes their result tables; aggregate
columns are ordinary input fields. An internal formula engine, SQL-to-formula
translation, recomputation of financial totals/balances and nullable-formula
semantics are NOT required for 1.6.0rc1. Earlier text implying that requirement
was an assistant scope expansion and is superseded by this correction, not a
record of owner authorization. Existing private derive code/tests are historical
implementation evidence, not release gates or authorization for public activation;
existing source-free generation remains unchanged. Key mapping, one-to-one rows,
exact numeric types, sensitivity controls and SQL budgets remain in scope.

Implementation and 1.6.0rc1 publication authorized by the user on 2026-09-24
(Europe/Samara). Use sequential signed PRs and green CI/CD. Independent AI
review applies to the final exact RC SHA and safety-policy changes, not every PR.
Stable publication is not authorized. No production source access is authorized.

## Format-independent scope clarification — 2026-09-27

The owner clarified the original RC scope: CSV and Parquet files, and bounded
read-only query results from Trino or PostgreSQL, are independent input choices.
Each can target CSV, Parquet or an SQL script file. SQL output is never executed
against a database; SQL-file import is not included. This is not live-access
authorization. Preserve SQL allowlists, budgets and explicit source authority.

Use input adapters -> shared typed transformation/validation -> output adapters.
Field rules and logical null/decimal/date semantics belong to the common core;
CSV dialect/null markers, Parquet physical types and SQL literal/identifier
encoding belong to adapters. Bind source snapshot, policy, mappings and selected
output settings to review/approval. Do not place CSV parsing in the common core.
Reuse the working CSV slice as the first route and regression baseline, then
extract only shared behavior needed by the next adapter. No per-format engines.
Completion requires all 4 input kinds x 3 output kinds, not CSV-only acceptance.
For query results, preserve the captured snapshot order; do not promise stable
database order across executions without an explicit ordering contract.

Private captured-result increment (2026-09-28): `postgres_query` and
`trino_query` drafts consume a versioned in-memory envelope containing adapter,
query SHA-256 and typed Parquet bytes. Parquet is an internal encoding only;
the selected source remains a query result. The full envelope (including schema,
row order and nulls) participates in the existing exact-byte snapshot binding.
This is fictional closed-executor development, not a database row-fetch adapter,
query authorization proof, aggregate recomputation or public activation. The
capture helper accepts already captured bytes and opens no database. Before
activation, separately implement and verify authorized bounded capture and
bind its authorization context; a caller-supplied query hash grants no access.

Concrete next adapter increment: CSV -> SQL-script using existing PostgreSQL
identifier/literal encoding. First separate the validated logical result from
CSV rendering, retaining null provenance and exact values. Do not parse output
CSV back into rows or infer final types from source-only metadata: unconditional
replace_text may change a numeric input to arbitrary text. Bind explicit output
schema/dialect/selection in policy snapshots and validate before publication.
The existing synthetic SQL renderer keeps its source-free guards unchanged;
reuse scalar encoding, not bypasses. Reuse typed_parquet_table for the following
Parquet output increment. These are planned implementation steps, not completed
routes or permission to publish to durable user destinations.

The refreshed 2026-09-24 handover is planned in
[client feedback v2](feedback-2026-09-24-v2.md): findings 20–26, strengthened
acceptance for 1–19, dependencies and unresolved decisions. It extends this
change's client/financial/format acceptance work; it does not authorize embedded
repair instructions, live integrations or a weaker safety boundary.

1. **Contract and safety approval.** Separate source-free generation from
   one-to-one transformation; settle field actions, sensitivity review,
   preservation authority, dependencies and typed substitution dictionaries.
   The review profile gives each field a bounded system comment explaining
   its inferred meaning, sensitivity suggestion and uncertainty before the
   operator decides; an unreviewed `sensitive=false` is not preserve consent.
   The selected authority is the trusted local CLI operator: interactive
   confirmation of the exact plan and preserved columns, with a receipt bound
   to fixed input bytes. Equal-privilege local impersonation is outside this
   deployment claim. This choice does not activate preservation; the scoped
   safety amendment, executable checks and independent safety review still gate it.
   These are activation gates: closed implementation and isolated fictional-data
   tests come first, followed by end-to-end evidence and independent review of
   the exact implementation SHA. No public execution or user-data access is
   enabled merely by developing that code; see the safety boundary.
2. **Confirmed client defects.** Reproduce and correct identifier collisions,
   repeated-key misclassification, generator/privacy disagreement and empty
   output directory publication. Report unknown date bounds and capped distinct
   statistics honestly. Do not import every suggested fix uncritically.
   Prioritize reproduction of permitted boolean SQL connectors (22) and
   mode/ratio parity (25); batch doctor diagnostics (20). Track Trino auth (21)
   behind an explicit configuration/secret-source decision.
3. **CSV vertical slice.** One-to-one rows, preserved reference combinations,
   replaced financial values, scoped substitutions and consistent keys through
   a saved policy before adding interactive UI. SQL aggregates are computed by
   the authorized query, not an internal formula engine. The first
   executable replacement primitive is a table of unconditional exact-text
   pairs (`true` -> `false`, `001` -> `1`): no inferred source/target type or
   numeric conversion. Support file-wide and per-column tables together in
   one file, not as mutually exclusive modes; apply each match once, never
   cascade. A matching per-column key overrides the same file-wide key;
   otherwise use the file-wide match, then the declared unmatched policy.
   Reject duplicate keys within each table. Keep reviewed
   field-action and preservation gates around this primitive. Add bounded
   local value-free trace/dry-run output for row/column/rule matches and
   unmatched cells.
4. **Review wizard and agent parity.** Present per-field evidence and proposed actions; allow
   edits or bulk acceptance of reviewed decisions and save a replayable policy.
   Show the system comment next to each explicit sensitivity decision; a bulk
   action cannot silently resolve unknown or conflicting classifications.
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
The 1.6.0rc1 declared exact DECIMAL precision cap is 38 digits, with scale
0..precision. This covers DECIMAL(20,2) and DECIMAL(38,16) using Arrow
decimal128 in Parquet. The cap is an interoperability boundary, not a claim
that higher-precision input is safe to approximate: higher precision fails
closed, without FLOAT conversion, implicit rounding or decimal256 fallback.
Decimal256/76-digit support is deferred until an end-to-end need and contract
are established; it is not a release blocker for the requested examples.
The dependent source-free slice adds DatasetSpec 1.1 `decimal_range` with exact
seeded generation and CSV/JSON/SQL/Parquet export. Existing 1.0 readers retain
their meaning; missing-version files remain 1.0. This is not completion of
exact profiling, financial formulas, transformation, or final RC acceptance.
Declared Parquet/SQL precision and scale are profile metadata only; reviewed
generation bounds must still be supplied. Unbounded SQL `numeric` keeps the
pre-existing approximate FLOAT path and cannot satisfy exact financial review.
For finding 25, reject the entire mixed/negative Parquet export when an
intentionally invalid value is incompatible with its declared physical type;
never stringify a whole column or publish a partial artifact.
