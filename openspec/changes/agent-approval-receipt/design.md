# Design: agent-approval-receipt

`agent-plan` creates a random non-secret `plan_id` and canonical SHA-256
fingerprints for the safe profile and planned `DatasetSpec`. The persisted plan
contains an `AgentReviewState` with those values.

`agent-status` reloads and validates the current spec, reports its canonical
fingerprint, and indicates whether it differs from the initially inferred
spec. This supports intentional reviewer edits without silently approving
later changes.

`agent-approve` requires the reported current fingerprint. It reloads the
workspace, verifies the stored profile fingerprint, validates immutable
generation settings, computes the effective spec fingerprint, and compares it
to the supplied value immediately before generation.

Successful generation writes `approval_receipt.json`. The typed receipt binds
the plan identifier, profile fingerprint, and reviewed spec fingerprint. A
workspace without the new review state must be replanned before approval.
