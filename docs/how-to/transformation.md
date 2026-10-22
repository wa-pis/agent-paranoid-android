# Transform Local Data

English · [Русский](../ru/how-to/transformation.md)

Use selective transformation when each output row must correspond to an input
row. Unlike synthetic generation, the result has mixed origin and may contain
explicitly replaced or approved preserved source values. Treat the destination
as potentially sensitive; validation is not an anonymity certificate.

## Choose An Action For Each Field

| Action | Effect |
| --- | --- |
| `drop` | Remove the field. |
| `synthesize` | Generate new values using the declared generation policy. |
| `substitute` | Apply an explicit typed mapping, optionally shared by a domain. |
| `replace_text` | Apply explicit exact-text mappings. Field mappings override file-wide mappings without cascading. |
| `preserve` | Retain an eligible non-sensitive field only after exact local approval. |

For an unmatched mapping, select rejection, synthesis or eligible preservation
explicitly. A preserve fallback has the same approval requirements as direct
preservation. Explicit mapped replacements may equal another source value,
including a sensitive permutation; this is not permission for implicit copying.
Mapping values never belong in logs, summaries, provider requests or MCP replies.

## Review Before Execution

1. Prepare a valid behavior policy, source and any local mapping files. Use a
   new destination distinct from every input.
2. Run `transform-review SOURCE POLICY.yaml`. Review the value-free field
   decisions and record the displayed `snapshot_sha256`.
3. To edit an already valid policy locally, use
   `transform-review SOURCE POLICY.yaml --decide --edit-actions`, then `SAVE`.
   Review the saved bytes again. Saving is not approval.
4. If any action preserves values, obtain the receipt in your own interactive
   local terminal with
   `transform-approve SOURCE POLICY.yaml RECEIPT --snapshot-sha256 SHA`.
5. Execute with
   `transform-execute SOURCE POLICY.yaml DESTINATION --snapshot-sha256 SHA`,
   adding `--receipt RECEIPT` when required. Inspect provenance and validation.

`SOURCE`, `POLICY.yaml`, `RECEIPT`, `DESTINATION` and `SHA` above are placeholders,
not a ready-to-run dataset approval. Use installed `COMMAND --help` for options.
Never supply real data to a provider while preparing the policy.

## Conditions For Preservation

Every preserved field needs an explicit non-sensitive decision, no positive or
conflicting sensitivity evidence, and a bounded operator comment. Sensitive,
unknown and disputed fields remain blocked. DECIMAL preservation is blocked by
default. Approval binds the exact source, classification, policy and referenced
mapping bytes. Any bound input change requires fresh review and approval.

Only the controlling local terminal can issue the receipt. Piped confirmation,
an agent flag and MCP approval cannot replace it. A matching receipt permits
only its reviewed plan; it does not authorize another dataset.

## Multiple Inputs And Databases

Use a [common saved profile](../reference/configuration.md#closed-common-transformation-profile)
with `transform-batch` for multiple inputs and final linked validation. Creation
saves configuration only. Validation and execution consume the exact reviewed
digest and any required local receipt.

Configured SQL sessions use administrator allowlists and read-only budgets to
capture once. Later steps reuse the same frozen snapshot without reconnecting.
Sessions enforce admission, expiry and cleanup. MCP consumers stay workspace
confined and return metadata, not rows.

See the [CLI contract](../reference/cli.md#implemented-rc-execution-candidate)
for formats and arguments, [MCP permissions](../reference/mcp-permissions.md)
for integration rights, and [Configuration](../reference/configuration.md)
for schemas and budgets. Historical RC anchors remain valid links.
