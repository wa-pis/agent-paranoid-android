# Design: agent-recovery

The agent state machine has three observable phases:

1. `awaiting_approval`
2. `recovery_required`
3. `completed`

Fresh generation writes `agent_completion.json` into the temporary generated
folder after generation, source-row checks, validation, and manifest creation.
The checkpoint is therefore published atomically with the bundle.

If root `agent_result.json` is absent after bundle publication, status reports
`recovery_required`. Recovery requires the same reviewed spec SHA-256 and then
rechecks:

- plan, profile, and effective-spec fingerprints;
- checkpoint identity and generation settings;
- generated profile and effective spec;
- generation manifest facts;
- bounded generated rows, schema/rule validation, and source-row non-reuse.

Only then are `approval_receipt.json` and `agent_result.json` written
atomically. Existing generated rows are never regenerated or silently
replaced.

When a completed result already exists, repeating approval with the same
reviewed hash returns that persisted result. A different hash fails.
