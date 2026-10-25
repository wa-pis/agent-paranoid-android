# Claude Desktop Manual Acceptance

## Prepared Environment

User selected Claude Desktop on 2026-10-09. Installed app UI reports
1.46388.4 after its pending vendor update applied during restart.

Prospective source: `eafb3d771da16d354ad7f33d395feeebe2bfc84f`.
Local wheel installed in `/private/tmp/apa-rc2-claude-env` with MCP 2.2.0.
Installed-package mcp-profile checks passed. This is not the Ubuntu preflight
artifact or public package and must be rebound to the final candidate source.

Local server `apa-rc2-acceptance` is visibly Running in Developer settings.
Its sole workspace is `/private/tmp/apa-rc2-claude-workspace`, with a fictional
customers.csv. Existing Claude settings were retained. No database/provider
credentials were added. The generator remains workspace-bounded.

A prompt is prepared in a new Claude chat but has NOT been sent by the agent.
No external AI-provider call or human approval is claimed. If the user elects
to send the request, only file names, tool arguments and safe metadata are to
be sent; source cells and dataset rows must never be included in chat.

## Human Steps

1. Send the prepared plan+inspect prompt. It requests customers.csv,
   agent/claude-review, CSV format, four rows, seed 81 and customers table name.
2. Confirm no output was generated before approval. Open the spec path locally
   and review fields, privacy, count, seed and relationships.
3. Ask for inspection and record review.current_spec_sha256. Explicitly approve
   that exact specification; changes require renewed review.
4. Let the client invoke approve_dataset_plan using that reviewed fingerprint.
5. Inspect completion and confirm row_counts customers=4, validation_valid=true,
   synthetic=true, source_rows_copied=false and local artifact paths. Report
   summaries only. Check generated artifacts locally without attaching rows.

## Acceptance Record (Pending)

- Final candidate SHA and installed wheel SHA-256: pending.
- Actual client/version and date: pending completion confirmation.
- Human review and exact reviewed fingerprint: pending.
- Successful approval/completion and artifact verification: pending.
- Unexpected prompts/errors, if any: pending.

A Running server is connection evidence only. Prepared text, automated SDK
approval, or an agent reading the specification does not complete human
acceptance. Publication remains blocked until the actual outcome is recorded.

## Completed Human Acceptance: 2026-10-09

User confirmed completion with “готово” in this chat after executing the prepared
Claude workflow. Local inspection independently confirms completed/none state,
no remaining approval requirement and an actual sha256_confirmation receipt.

- Client: Claude Desktop 1.46388.4, MCP 2.2.0, installed package 1.6.0rc2.
- Installed local wheel SHA-256:
  a328c3033ef78b89c50c690f60dd44672e730bc99dca9f63855aec8193f21029.
- Built source eafb3d771da16d354ad7f33d395feeebe2bfc84f and final main
  21f4a04ed4acd7c33caac9fda8c6c03b7f0501d1 share exact tree
  0e5754d1ff5d955b4d2a8b0b9fdace39ed090071, independently verified by reviewer.
  Acceptance covers this identical candidate source, not Ubuntu artifact hashes.
- Reviewed specification fingerprint:
  bfca7ee8a871ef0baae16ccac9ae99ad77d7705f7d1333a5b6641eca12ec2985.
- Completion: customers=4, seed=81, CSV, validation_valid=true, synthetic=true,
  source_rows_copied=false. Spec fingerprint unchanged since planning.
- Manifest and validation report independently read only for safe metadata;
  CSV count and source-row disjointness verified locally without displaying rows.

The earlier pending sections above describe preparation history. Manual acceptance
is now completed by the user's confirmation plus actual receipt/artifact checks.
Exact-main CI, independent source clearance, Ubuntu preflight and signed release
manifest are still separately required; this record does not authorize stable.
