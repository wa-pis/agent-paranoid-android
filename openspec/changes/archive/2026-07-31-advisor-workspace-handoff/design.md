# Design: advisor-workspace-handoff

`advise_agent_workspace` first verifies that the workspace is awaiting
approval and reloads its bounded profile and current effective `DatasetSpec`.
It builds the same fingerprint-bound `AdvisorRequest` used by the direct API
and validates provider output before writing anything.

The operation publishes two atomic checkpoints in order:

1. `advisor_review.json`, containing the safe request, validated proposal, and
   proposed-spec fingerprint;
2. the proposed `dataset_spec.yaml`.

If interruption occurs between checkpoints, the next call validates and reuses
the persisted exchange instead of contacting the provider. If the current spec
matches neither the proposal baseline nor proposed fingerprint, the operation
fails rather than overwriting a human edit.

Pending status rebuilds its metadata-only summary from the current effective
spec. The existing reviewed-spec fingerprint remains the only authorization
accepted by `agent-approve`.
