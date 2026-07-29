# Design: agent-review-report

`review_agent_workspace` first uses the existing workspace inspector. It
accepts only an awaiting-approval workspace with fingerprint-bound review
state. The function then reloads the bounded current spec and compares its
fingerprint to the inspected state, failing if a concurrent edit occurred.

The typed report includes only metadata needed for review:

1. plan, profile, planned-spec, and current-spec identities;
2. entity row counts, primary keys, and field flags;
3. semantic type and distribution kind, but no distribution values;
4. relationships, constraints, privacy defaults, assumptions, and warnings.

Human rendering limits detailed fields per entity and points to the complete
`dataset_spec.yaml`. JSON retains all metadata for automation. Both forms are
read-only and row-free.
